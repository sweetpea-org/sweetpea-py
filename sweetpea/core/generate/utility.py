"""This module provides the types and common functions that are used across the
various generation functionalities.
"""


from contextlib import contextmanager
from enum import Enum, auto
from pathlib import Path
from typing import Iterator, List, NamedTuple
from uuid import uuid4 as generate_uuid

from ..cnf import CNF, Var


__all__ = ['AssertionType', 'GenerationRequest', 'Solution', 'combine_and_save_cnf', 'save_cnf', 'temporary_cnf_file']


@contextmanager
def temporary_cnf_file(base_path: Path = Path('.')) -> Iterator[Path]:
    """Returns a `Path` to a new, local file in the directory of the given path
    with a .cnf suffix. When used as a context manager (recommended), the file
    will be deleted when it leaves the context scope.
    """
    cnf_file = base_path / Path(str(generate_uuid())).with_suffix('.cnf')
    try:
        yield cnf_file
    finally:
        if cnf_file.exists():
            cnf_file.unlink()


class AssertionType(Enum):
    """The three supported variants of CNF assertion:

        EQ :: assert k == n
        LT :: assert k < n
        GT :: assert k > n
    """
    EQ = auto()
    LT = auto()
    GT = auto()


class GenerationRequest(NamedTuple):
    """A request to generate a CNF."""
    assertion_type: AssertionType
    k: int
    boolean_values: List[Var]


class Solution(NamedTuple):
    """The result of a generation."""
    assignment: List[int]
    frequency: int


def combine_cnf_with_requests(initial_cnf: CNF,
                              fresh: int,
                              support: int,
                              generation_requests: List[GenerationRequest]) -> CNF:
    """Combines a base CNF formula with a new CNF formula formed from the given
    GenerationRequests.
    """
    for request in generation_requests:
        if request.assertion_type is AssertionType.EQ:
            initial_cnf.assert_k_of_n(request.k, request.boolean_values)
        elif request.assertion_type is AssertionType.LT:
            initial_cnf.assert_k_less_than_n(request.k, request.boolean_values)
        elif request.assertion_type is AssertionType.GT:
            initial_cnf.assert_k_greater_than_n(request.k, request.boolean_values)
        else:
            raise ValueError(f"invalid assertion type: {request.assertion_type}")
    return initial_cnf  # TODO: Does this still work right?


def save_cnf(filename: Path, cnf: CNF):
    """Writes a CNF formula to a file at the given path."""
    filename.write_text(cnf.as_dimacs_string())


def combine_and_save_cnf(filename: Path,
                         initial_cnf: CNF,
                         fresh: int,
                         support: int,
                         generation_requests: List[GenerationRequest]):
    """Combines a base CNF formula with the augmentations specified by the
    list of GenerationRequests, merges those formulas, then saves the result to
    a file at the given path.
    """
    combined_cnf = combine_cnf_with_requests(initial_cnf, fresh, support, generation_requests)
    save_cnf(filename, combined_cnf)
