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
from sweetpea.docker import update_docker_image, start_docker_container, stop_docker_container, check_server_health
from sweetpea.backend import BackendRequest
from sweetpea.primitives import *
from sweetpea.constraints import *

# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def __count_solutions(block: Block) -> int:
    fc_size = block.trials_per_sample()
    return math.factorial(fc_size)


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


def __generate_json_data(block: Block, sequence_count: int) -> dict:
    backend_request = block.build_backend_request()
    support = block.variables_per_sample()
    solution_count = __count_solutions(block)
    return backend_request.to_request_data(support, sequence_count, solution_count)


def __generate_json_request(block: Block, sequence_count: int) -> dict:
    print("Generating design formula... ", end='', flush=True)
    t_start = datetime.now()
    json_data = __generate_json_data(block, sequence_count)
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
    return json_data


def save_cnf(block: Block, filename: str) -> None:
    cnf_str = __generate_cnf(block)
    with open(filename, 'w') as f:
        f.write(cnf_str)


def save_json_request(block: Block, sequence_count: int, filename: str) -> None:
    json_request = json.dumps(__generate_json_request(block, sequence_count))
    with open(filename, 'w') as f:
        f.write(json_request)


"""
Invokes the backend to build the final CNF formula in DIMACS format, returning it as a string.
"""
def __generate_cnf(block: Block) -> str:
    json_data = __generate_json_request(block, 0)
    json_data['action'] = {
        'actionType': 'BuildCNF',
        'parameters': {}
    }

    update_docker_image("sweetpea/server")
    container = start_docker_container("sweetpea/server", 8080)

    cnf_job = None
    try:
        check_server_health()

        cnf_job_response = requests.post('http://localhost:8080/experiments/jobs', data = json.dumps(json_data))
        if cnf_job_response.status_code != 200:
            raise RuntimeError("Received non-200 response from CNF job submission! response=" + str(cnf_job_response.status_code) + " body=" + cnf_job_response.text)
        else:
            cnf_job = cnf_job_response.json()

        print("Waiting for CNF generation", end='', flush=True)
        t_start = datetime.now()

        delay = 0.2
        while cnf_job['status'] == 'InProgress':
            print('.', end='', flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 30)
            url = 'http://localhost:8080/experiments/jobs/' + cnf_job['id']
            cnf_job_response = requests.get(url)
            if cnf_job_response.status_code != 200:
                raise RuntimeError("Received non-200 response from CNF job status query! url=" + url + " response=" + str(cnf_job_response.status_code) + " body=" + cnf_job_response.text)
            else:
                cnf_job = cnf_job_response.json()

        t_end = datetime.now()
        print("\nCNF generation complete. " + str((t_end - t_start).seconds) + "s")

    finally:
        stop_docker_container(container)

    return cnf_job['result']


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
                      require_complete_crossing=True,
                      cnf_fn=to_cnf_tseitin) -> Block:
    all_constraints = cast(List[Constraint], [FullyCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints)
    block = FullyCrossBlock(design, crossing, all_constraints, require_complete_crossing, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    return block


def __desugar_constraints(constraints: List[Constraint]) -> List[Constraint]:
    desugared_constraints = []
    for c in constraints:
        desugared_constraints.extend(c.desugar())
    return desugared_constraints


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
def synthesize_trials_non_uniform(block: Block, sequence_count: int) -> List[dict]:
    json_data = __generate_json_request(block, sequence_count)
    json_data['action'] = {
        'actionType': 'SampleNonUniform',
        'parameters': {
            'count': str(sequence_count)
        }
    }

    solutions = cast(List[dict], [])

    # Make sure the local image is up-to-date.
    update_docker_image("sweetpea/server")

    # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
    container = start_docker_container("sweetpea/server", 8080)

    print("Sending formula to backend... ", end='', flush=True)
    t_start = datetime.now()

    job = None
    try:
        check_server_health()

        url = 'http://localhost:8080/experiments/jobs'
        job_response = requests.post(url, data = json.dumps(json_data))
        if job_response.status_code != 200:
            tmp_filename = ""
            with tempfile.NamedTemporaryFile(delete=False) as f:
                json.dump(json.dumps(json_data), f)
                tmp_filename = f.name

            raise RuntimeError("Received non-200 response from non-uniform experiment generation job submission! Request body saved to temp file '" +
                tmp_filename + "' status_code=" + str(job_response.status_code) + " response_body=" + str(job_response.text))

        job = job_response.json()
        delay = 0.2
        while job['status'] == 'InProgress':
            print('.', end='', flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 30)
            url = 'http://localhost:8080/experiments/jobs/' + job['id']
            job_response = requests.get(url)
            if job_response.status_code != 200:
                raise RuntimeError("Received non-200 response from non-uniform job status query! url=" + url + " response=" + str(job_response.status_code) + " body=" + job_response.text)
            else:
                job = job_response.json()

        solutions = json.loads(job['result'])['solutions']
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")

    # 3. Stop and then remove the docker container.
    finally:
        stop_docker_container(container)

    # 4. Decode the results
    result = list(map(lambda s: __decode(block, s['assignment']), solutions))

    return result


"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results
in some direct cnfs being produced and some requests to the backend being produced). Then
calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable
& (2) psyNeuLink readable.
"""
def synthesize_trials(block: Block, sequence_count: int=10) -> List[dict]:
    return __synthesize_trials_unigen(block, sequence_count)


def __synthesize_trials_unigen(block: Block, sequence_count: int) -> List[dict]:
    # TODO: Do this in separate thread, and output some kind of progress indicator.
    json_data = __generate_json_request(block, sequence_count)

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
        check_server_health()

        experiments_request = requests.post('http://localhost:8080/experiments/generate', data = json_data)
        if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
            tmp_filename = ""
            with tempfile.NamedTemporaryFile(delete=False) as f:
                json.dump(json_data, f)
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


def __synthesize_trials_guided(block: Block, sequence_count: int) -> List[dict]:
    # TODO - implement new idea
    return []
