"""This module provides functionality for collecting metrics about a specific
block in an experimental design.

STATUS: dead code, retained but unreferenced.

Nothing in the library, the tests, or the example programs imports this module,
and it was not importable at all between December 2022 and September 2026: it
referenced `sweetpea._internal.blocks`, which has never existed under that name
(the module is `sweetpea._internal.block`). That import has been corrected here,
along with a dependency on a `main.__generate_cnf` helper that was removed in
September 2026, so that the module at least type-checks -- but it remains
untested and uncalled.
"""


from math import factorial
from typing import Dict

from sweetpea._internal.block import Block
from sweetpea._internal.server import build_cnf
from sweetpea._internal.core.cnf import Var


def collect_design_metrics(block: Block) -> Dict:
    """Given a block, this function will collect various metrics pertaining to
    the block and return them in a dictionary.
    """
    backend_request = block.build_backend_request()
    cnf = build_cnf(block)
    cnf_str = cnf.as_unigen_string(
        sampled_variables=[Var(n) for n in block.support_variables()])
    dimacs_header = cnf_str.split('\n')[0].split(' ')

    return {
        'full_factor_count': len(block.design),
        'non_implied_factor_count': len(block.act_design),
        'crossing_factor_count': len(block.crossings),
        'constraint_count': len(block.constraints),

        'block_length': block._trials_per_sample(),
        'block_length_factorial': factorial(block._trials_per_sample()),

        'low_level_request_count': len(backend_request.ll_requests),
        'cnf_total_variables': int(dimacs_header[2]),
        'cnf_total_clauses': int(dimacs_header[3])
    }
