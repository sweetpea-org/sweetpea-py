"""The behind-the-scenes stuff that powers SweetPea."""

from enum import Enum, auto
from typing import List, NamedTuple

from .cnf import CNF, Var


class SolutionSpec(NamedTuple):
    assignment: List[int]
    frequency: int


class GenerationType(Enum):
    """An enum that provides access to the three methods of CNF generation:

        1. Assert k == n.
        2. Assert k < n.
        3. Assert k > n.

    Instances of this enum also have the `.function` property, which allows
    calling the associated function.
    """
    EQ = auto()
    LT = auto()
    GT = auto()

    # NOTE: There is a more complete definition of this enum coming, but its
    #       useful public interface will not change.


class GenerationRequest(NamedTuple):
    generationType: GenerationType
    k: int
    boolean_values: List[Var]


def generate_CNF(
        initial_CNF: CNF,
        fresh: int,
        support: int,
        generation_requests: List[GenerationRequest],
        use_docker: bool = True
) -> List[SolutionSpec]:
    raise NotImplementedError()


def generate_non_uniform_CNF(
        count: int,
        initial_CNF: CNF,
        fresh: int,
        support: int,
        generation_requests: List[GenerationRequest]
) -> List[SolutionSpec]:
    raise NotImplementedError()


def build_CNF(
        initial_CNF: CNF,
        fresh: int,
        support: int,
        generation_requests: List[GenerationRequest]
) -> str:
    raise NotImplementedError()
