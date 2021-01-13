"""The behind-the-scenes stuff that powers SweetPea."""

from enum import Enum, auto
from typing import List, NamedTuple

from .simple_types import Clause, Count, CNF, Var


# NOTE: As of Python 3.9, typing.NamedTuple (and typing.TypedDict) are now
#       functions instead of classes. This causes Pylint to raise a few errors.
#       The following three lines disable checking for these specific errors
#       within this file. This behavior is documented in the following issues:
#           https://bugs.python.org/issue41973
#           https://github.com/PyCQA/pylint/issues/3876
# TODO: Once Pylint is updated to accommodate this change, remove the lines
#       disabling the checks.
# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods
# pylint: disable=inherit-non-class


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
