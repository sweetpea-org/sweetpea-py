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
from sweetpea.internal import chunk, get_all_level_names, intersperse
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

For factors that don't have a value for a given level, such as Transitions,
the label will be ''.
"""
def __decode(block: Block, solution: List[int]) -> dict:
    gt0 = lambda n: n > 0
    simple_variables = list(filter(gt0, solution[:block.grid_variables()]))
    complex_variables = list(filter(gt0, solution[block.grid_variables():block.variables_per_sample()]))

    experiment = cast(dict, {})

    # Simple factors
    tuples = list(map(lambda v: block.decode_variable(v), simple_variables))
    for (factor_name, level_name) in tuples:
        if factor_name not in experiment:
            experiment[factor_name] = []
        experiment[factor_name].append(level_name)

    # Complex factors - The challenge here is knowing when to insert '', rather than using the variables.
    # Start after 'width' trials, and shift 'stride' trials for each variable.
    complex_factors = list(filter(lambda f: f.has_complex_window(), block.design))
    for f in complex_factors:
        # Get variables for this factor
        start = block.first_variable_for_level(f.name, f.levels[0].name) + 1
        end = start + block.variables_for_factor(f)
        variables = list(filter(lambda n: n in range(start, end), complex_variables))

        # Get the level names for the variables in the solution.
        level_names = list(map(lambda v: block.decode_variable(v)[1], variables))

        # Intersperse empty strings for the trials to which this factor does not apply.
        level_names = list(intersperse('', level_names, f.levels[0].window.stride - 1))
        level_names = list(repeat('', f.levels[0].window.width - 1)) + level_names

        experiment[f.name] = level_names

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
