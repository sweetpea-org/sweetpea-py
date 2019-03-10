import operator as op

from functools import reduce
from math import factorial
from typing import Dict

from sweetpea.blocks import Block
from sweetpea.constraints import ExactlyKInARow, AtMostKInARow
from sweetpea import __generate_cnf


"""
Given a block, this function will collect various metrics pertaining to the block
and return them in a dictionary.
"""
def collect_design_metrics(block: Block) -> Dict:
    backend_request = block.build_backend_request()
    dimacs_header = __generate_cnf(block).split('\n')[0].split(' ')

    return {
        'full_factor_count': len(block.design),
        'crossing_factor_count': len(block.crossing),
        'constraint_count': len(block.constraints),

        'block_length': block.trials_per_sample(),
        'block_length_factorial': factorial(block.trials_per_sample()),

        'low_level_request_count': len(backend_request.ll_requests),
        'cnf_total_variables': int(dimacs_header[2]),
        'cnf_total_clauses': int(dimacs_header[3])
    }
