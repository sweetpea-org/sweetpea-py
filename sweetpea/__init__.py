import docker
import json
import os
import requests
import shutil
import subprocess
import tempfile
import time
import math

from ascii_graph import Pyasciigraph
from functools import reduce, partial
from datetime import datetime
from itertools import product
from typing import Any, List, Union, Tuple, cast

from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.internal import chunk, get_level_name, get_all_level_names
from sweetpea.logic import to_cnf_tseitin
from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.docker import update_docker_image, start_docker_container, stop_docker_container
from sweetpea.backend import BackendRequest
from sweetpea.primitives import *
from sweetpea.constraints import *

# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def __count_solutions(block: Block) -> int:
    fc_size = block.trials_per_sample()
    return math.factorial(fc_size)


def __desugar(block: Block) -> BackendRequest:
    fresh = 1 + block.variables_per_sample()
    backend_request = BackendRequest(fresh)

    for c in block.constraints:
        c.apply(block, backend_request)

    return backend_request


"""
Decodes a single solution into a dict of this form:
{
  '<factor name>': ['<trial 1 label>', '<trial 2 label>, ...]
  ...
}
"""
def __decode(block: Block, solution: List[int]) -> dict:
    num_encoding_vars = block.variables_per_sample()
    vars_per_trial = block.variables_per_trial()

    # Looks like [[2, 4, 6], [8, 10, 12], [14, 16, 18], [20, 22, 23]]
    trial_assignments = list(map(lambda l: list(filter(lambda n: n > 0, l)),
                                 list(chunk(solution[:num_encoding_vars], vars_per_trial))))

    transposed = cast(List[List[int]], list(map(list, zip(*trial_assignments))))
    assignment_indices = [list(map(lambda n: (n - 1) % vars_per_trial, s)) for s in transposed]

    factor_names = list(map(lambda f: f.name, block.design))
    factors = list(zip(factor_names, assignment_indices))

    level_names = list(map(lambda tup: tup[1], get_all_level_names(block.design)))

    experiment = {c: list(map(lambda idx: level_names[idx], v)) for (c,v) in factors}

    return experiment


def __generate_json_data(block: Block) -> str:
    backend_request = __desugar(block)
    support = block.variables_per_sample()
    solution_count = __count_solutions(block)
    return backend_request.to_json(support, solution_count)


def __generate_json_request(block: Block) -> str:
    print("Generating design formula... ", end='', flush=True)
    t_start = datetime.now()
    json_data = __generate_json_data(block)
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
    return json_data


def __check_server_health():
    health_check = requests.get('http://localhost:8080/')
    if health_check.status_code != 200:
        raise RuntimeError("SweetPea server healthcheck returned non-200 reponse! " + str(health_check.status_code))


"""
Invokes the backend to build the final CNF formula in DIMACS format, returning it as a string.
"""
def __generate_cnf(block: Block) -> str:
    json_data = __generate_json_request(block)

    update_docker_image("sweetpea/server")
    container = start_docker_container("sweetpea/server", 8080)

    cnf_str = ""
    try:
        __check_server_health()

        cnf_request = requests.post('http://localhost:8080/experiments/build-cnf', data = json_data)
        if cnf_request.status_code != 200:
            raise RuntimeError("Received non-200 response from CNF generation! response=" + str(cnf_request.status_code) + " body=" + cnf_request.text)
        else:
            cnf_str = cnf_request.text

    finally:
        stop_docker_container(container)

    return cnf_str


"""
Approximates the number of solutions to the CNF formula generated for this experiment.
Expects the sharpSAT binary to be present on the PATH
"""
def __approximate_solution_count(block: Block, timeout_in_seconds: int = 60, cache_size_mb: int = 4096) -> int:
    approx_sol_cnt = -1

    cnf_str = __generate_cnf(block)

    # Write the CNF to a tmp file
    tmp_filename = ""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(str.encode(cnf_str))
        tmp_filename = f.name

    print("Approximating solution count with sharpSAT...", end='', flush=True)
    t_start = datetime.now()
    output = subprocess.check_output(["sharpSAT", "-q", "-t", str(timeout_in_seconds), "-cs", str(cache_size_mb), tmp_filename])
    approx_sol_cnt = int(output.decode().split('\n')[0])
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")

    return approx_sol_cnt


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Returns a fully crossed block that we'll process with synthesize! Carries with it the function that
should be used for all CNF conversions.
"""
def fully_cross_block(design: List[Factor],
                      crossing: List[Factor],
                      constraints: List[Constraint],
                      cnf_fn=to_cnf_tseitin) -> Block:
    all_constraints = cast(List[Constraint], [FullyCross, Consistency]) + constraints
    block = FullyCrossBlock(design, crossing, all_constraints, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    return block


"""
Helper method to print a chart outlining the variable mappings, helpful for visualizing
the formula space. For example, for the simple stroop test:
----------------------------------------------
|   Trial |  color   |   text   | congruent? |
|       # | red blue | red blue |  con  inc  |
----------------------------------------------
|       1 |  1   2   |  3   4   |   5    6   |
|       2 |  7   8   |  9   10  |  11    12  |
|       3 | 13   14  | 15   16  |  17    18  |
|       4 | 19   20  | 21   22  |  23    24  |
----------------------------------------------
"""
def print_variable_grid(blk: Block):
    design_size = blk.variables_per_trial()
    num_trials = blk.trials_per_sample()
    num_vars = blk.variables_per_sample()

    largest_number_len = len(str(num_vars))

    header_widths = []
    row_format_str = '| {:>7} |'
    for f in blk.design:
        # length of all levels concatenated for this factor
        level_names = list(map(get_level_name, f.levels))
        level_name_widths = [max(largest_number_len, l) for l in list(map(len, level_names))]

        level_names_width = sum(level_name_widths) + len(level_names) - 1 # Extra length for spaces in between names.
        factor_header_width = max(len(f.name), level_names_width)
        header_widths.append(factor_header_width)

        # If the header is longer than the level widths combined, then they need to be lengthened.
        diff = factor_header_width - level_names_width
        if diff > 0:
            idx = 0
            while diff > 0:
                level_name_widths[idx] += 1
                idx += 1
                diff -= 1
                if idx >= len(level_name_widths):
                    idx = 0

        # While we're here, build up the row format str.
        row_format_str = reduce(lambda a, b: a + ' {{:^{}}}'.format(b), level_name_widths, row_format_str)
        row_format_str += ' |'

    header_format_str = reduce(lambda a, b: a + ' {{:^{}}} |'.format(b), header_widths, '| {:>7} |')
    factor_names = list(map(lambda f: f.name, blk.design))
    header_str = header_format_str.format(*["Trial"] + factor_names)
    row_width = len(header_str)
    print('-' * row_width)
    print(header_str)

    all_level_names = [ln for (fn, ln) in get_all_level_names(blk.design)]
    print(row_format_str.format(*['#'] + all_level_names))
    print('-' * row_width)

    for t in range(num_trials):
        args = [str(t + 1)] + list(map(str, range(t * design_size + 1, t * design_size + design_size + 2)))
        print(row_format_str.format(*args))

    print('-' * row_width)


"""
Display the generated experiments in human-friendly form.
"""
def print_experiments(block: Block, experiments: List[dict]):
    nested_assignment_strs = [list(map(lambda l: f.name + " " + get_level_name(l), f.levels)) for f in block.design]
    column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

    for e in experiments:
        strs = [list(map(lambda v: name + " " + v, values)) for (name,values) in e.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


"""
This is a helper function for getting some number of unique non-uniform solutions. It invokes a separate
endpoint on the server that repeatedly computes individual solutions while updating the formula to exclude
each solution once it has been found. It's intended to give users something somewhat useful, while
we work through issues with unigen.
"""
def synthesize_trials_non_uniform(block: Block, trial_count: int) -> List[dict]:
    json_data = __generate_json_request(block)

    solutions = cast(List[dict], [])

    # Make sure the local image is up-to-date.
    update_docker_image("sweetpea/server")

    # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
    container = start_docker_container("sweetpea/server", 8080)

    print("Sending formula to backend... ", end='', flush=True)
    t_start = datetime.now()
    try:
        __check_server_health()

        url = 'http://localhost:8080/experiments/generate/non-uniform/' + str(trial_count)
        experiments_request = requests.post(url, data = json_data)
        if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
            tmp_filename = ""
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(str.encode(json_data))
                tmp_filename = f.name

            raise RuntimeError("Received non-200 response from non-uniform experiment generation! Request body saved to temp file '" +
                tmp_filename + "' status_code=" + str(experiments_request.status_code) + " response_body=" + str(experiments_request.text))

        solutions = experiments_request.json()['solutions']
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")

    # 3. Stop and then remove the docker container.
    finally:
        stop_docker_container(container)

    # 4. Decode the results
    result = list(map(lambda s: __decode(block, s['assignment']), solutions))

    return result


"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results in some direct cnfs being produced and some requests to the backend being produced). Then calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable & (2) psyNeuLink readable.
"""
def synthesize_trials(block: Block) -> List[dict]:
    # TODO: Do this in separate thread, and output some kind of progress indicator.
    json_data = __generate_json_request(block)

    solutions = cast(List[dict], [])

    # Make sure the local image is up-to-date.
    update_docker_image("sweetpea/server")

    # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
    container = start_docker_container("sweetpea/server", 8080)

    # 2. POST to /experiments/generate using the backend request json as the body.
    # TOOD: Do this in separate thread, and output some kind of progress indicator.
    print("Sending formula to backend... ", end='', flush=True)
    t_start = datetime.now()
    try:
        __check_server_health()

        experiments_request = requests.post('http://localhost:8080/experiments/generate', data = json_data)
        if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
            tmp_filename = ""
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(str.encode(json_data))
                tmp_filename = f.name

            raise RuntimeError("Received non-200 response from experiment generation! LowLevelRequest body saved to temp file '" +
                tmp_filename + "' status_code=" + str(experiments_request.status_code) + " response_body=" + str(experiments_request.text))

        solutions = experiments_request.json()['solutions']
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")

    # 3. Stop and then remove the docker container.
    finally:
        stop_docker_container(container)

    # 4. Decode the results
    result = list(map(lambda s: __decode(block, s['assignment']), solutions))

    # Dump histogram of frequency distribution, just to make sure it's somewhat even.
    print()
    print("Found " + str(len(solutions)) + " distinct solutions.")
    print()
    hist_data = [("Solution #" + str(idx + 1), sol['frequency']) for idx, sol in enumerate(solutions)]
    hist_data.sort(key=lambda tup: tup[1], reverse=True)

    graph = Pyasciigraph()
    for line in  graph.graph('Most Frequently Sampled Solutions', hist_data[:15]):
        print(line)

    return result
