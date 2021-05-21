"""This module provides functionality to communicate with the server."""


from typing import List

from sweetpea.blocks import Block
from sweetpea.core import CNF, combine_cnf_with_requests, cnf_is_satisfiable
from sweetpea.logic import And, cnf_to_json


def build_cnf(block: Block) -> CNF:
    """Converts a Block into a CNF represented as a Unigen-compatible string.
    """
    backend_request = block.build_backend_request()
    cnf = CNF(backend_request.get_cnfs_as_json())
    combined_cnf = combine_cnf_with_requests(
        cnf,
        backend_request.fresh - 1,
        block.variables_per_sample(),
        backend_request.get_requests_as_generation_requests())
    return combined_cnf


def is_cnf_still_sat(block: Block, additional_clauses: List[And]) -> bool:
    backend_request = block.build_backend_request()
    cnf = CNF(backend_request.get_cnfs_as_json()) + CNF(cnf_to_json(additional_clauses))
    combined_cnf = combine_cnf_with_requests(
        cnf,
        backend_request.fresh - 1,
        block.variables_per_sample(),
        backend_request.get_requests_as_generation_requests())
    return cnf_is_satisfiable(combined_cnf)
