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
from sweetpea.sampling_strategies.base_strategy import BaseStrategy
from sweetpea.sampling_strategies.non_uniform import NonUniform

# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def save_cnf(block: Block, filename: str) -> None:
    cnf_str = __generate_cnf(block)
    with open(filename, 'w') as f:
        f.write(cnf_str)

"""
Invokes the backend to build the final CNF formula in DIMACS format, returning it as a string.
"""
def __generate_cnf(block: Block) -> str:
    backend_request = block.build_backend_request()
    json_data = {
        'action': 'BuildCNF',
        'cnfs': backend_request.get_cnfs_as_json(),
        'requests': backend_request.get_requests_as_json(),
        'support': block.variables_per_sample(),
        'fresh': backend_request.fresh,
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
    return synthesize_trials(block, sequence_count, sampling_strategy=NonUniform)


"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results
in some direct cnfs being produced and some requests to the backend being produced). Then
calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable
& (2) psyNeuLink readable.
"""
def synthesize_trials(block: Block, sequence_count: int=10, sampling_strategy=NonUniform) -> List[dict]:
    return sampling_strategy.sample(block, sequence_count)
