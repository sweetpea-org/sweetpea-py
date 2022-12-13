"""This module provides the types and common functions that are used across the
various submodules of :mod:`sweetpea.core.generate`.
"""


from __future__ import annotations

from contextlib import contextmanager
from enum import Enum, auto
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Iterator, List, NamedTuple, Optional
from uuid import uuid4 as generate_uuid

from ..cnf import CNF, Var


__all__ = [
    'AssertionType', 'GenerationRequest', 'SampleType', 'ProblemSpecification', 'Solution',
    'combine_and_save_cnf', 'combine_cnf_with_requests', 'save_cnf', 'temporary_cnf_file'
]


JSONDict = Dict[str, Any]


@contextmanager
def temporary_cnf_file(base_path: Path = Path('.'), suffix: str = ".cnf") -> Iterator[Path]:
    """Returns a :class:`pathlib.Path` to a new, local file in the directory of
    the given path with a ``.cnf`` suffix. When used as a context manager
    (recommended), the file will be deleted when it leaves the context scope.
    """
    cnf_file = base_path / Path(str(generate_uuid())).with_suffix(suffix)
    try:
        yield cnf_file
    finally:
        if cnf_file.exists():
            cnf_file.unlink()


class AssertionType(Enum):
    """The three supported variants of CNF assertion."""
    #: Assert k == n.
    EQ = auto()
    #: Assert k < n.
    LT = auto()
    #: Assert k > n.
    GT = auto()

    @staticmethod
    def from_json(s: str) -> AssertionType:
        """Converts a JSON string to an :class:`AssertionType`."""
        return AssertionType[s]


class GenerationRequest(NamedTuple):
    """A request to generate a CNF."""
    #: The variant of assertion to make.
    assertion_type: AssertionType
    #: The ``k`` value.
    k: int
    #: A list of variables to use in generation.
    boolean_values: List[Var]

    @staticmethod
    def from_json(data: JSONDict) -> GenerationRequest:
        """Converts a JSON object to a :class:`GenerationRequest`."""
        return GenerationRequest(
            assertion_type=AssertionType.from_json(data['equalityType']),
            k=data['k'],
            boolean_values=[Var(v) for v in data['booleanValues']])


class SampleType(Enum):
    """The supported methods of interacting with SweetPea core."""
    #: Uniform sampling of a CNF formula.
    Uniform       = auto()
    #: Non-uniform sampling of a CNF formula.
    NonUniform    = auto()
    #: Test whether a CNF formula is satisfiable.
    IsSatisfiable = auto()

    @staticmethod
    def from_json(s: str) -> SampleType:
        """Converts a JSON string to a :class:`SampleType`."""
        if s in ('BuildCNF', 'SampleUniform', 'Uniform'):
            return SampleType.Uniform
        elif s in ('SampleNonUniform', 'NonUniform'):
            return SampleType.NonUniform
        elif s in ('IsSAT', 'IsSatisfiable'):
            return SampleType.IsSatisfiable
        else:
            raise ValueError(f"Invalid value for SampleType: {s}")


class ProblemSpecification(NamedTuple):
    """A specification of a complete SweetPea problem to be solved."""
    #: The type of sample to produce.
    sample_type: SampleType
    #: The number of samples to take.
    sample_count: int
    #: The number of fresh variables in the input.
    # TODO: This should be removed eventually.
    fresh: int
    #: The length of the support set.
    support: int
    #: The CNF formula to sample.
    cnf: CNF
    #: A list of requests to make with regard to the CNF formula.
    requests: List[GenerationRequest]

    @staticmethod
    def from_json(data: JSONDict) -> ProblemSpecification:
        """Converts a JSON object to a :class:`ProblemSpecification`."""
        return ProblemSpecification(
            sample_type=SampleType.from_json(data['action']),
            sample_count=data['sampleCount'],
            fresh=data['fresh'],
            support=data['support'],
            cnf=CNF(data['cnfs']),
            requests=[GenerationRequest.from_json(gr) for gr in data['requests']])


class Solution(NamedTuple):
    """The result of a generation."""
    # TODO DOC
    assignment: List[int]
    # TODO DOC
    frequency: int


def combine_cnf_with_requests(initial_cnf: CNF,
                              fresh: int,
                              support: int,  # FIXME: Remove.
                              generation_requests: List[GenerationRequest]) -> CNF:
    """Combines a base :class:`CNF` with a new :class:`CNF` formed from the
    given :class:`GenerationRequests <.GenerationRequest>`.
    """
    fresh_cnf = CNF.from_fresh(fresh)
    for request in generation_requests:
        if request.assertion_type is AssertionType.EQ:
            fresh_cnf.assert_k_of_n(request.k, request.boolean_values)
        elif request.assertion_type is AssertionType.LT:
            fresh_cnf.assert_k_less_than_n(request.k, request.boolean_values)
        elif request.assertion_type is AssertionType.GT:
            fresh_cnf.assert_k_greater_than_n(request.k, request.boolean_values)
        else:
            raise ValueError(f"invalid assertion type: {request.assertion_type}")
    final_cnf = fresh_cnf + initial_cnf
    return final_cnf  # TODO: Does this still work right?


def save_cnf(filename: Path,
             cnf: CNF,
             fresh: Optional[int] = None,
             support: Optional[int] = None):
    """Writes a CNF formula to a file at the given path."""
    filename.write_text(cnf.as_unigen_string(support_set_length=support))


def combine_and_save_cnf(filename: Path,
                         initial_cnf: CNF,
                         fresh: int,
                         support: int,
                         generation_requests: List[GenerationRequest]):
    """Combines a base CNF formula with the augmentations specified by the
    :class:`list` of :class:`GenerationRequests <.GenerationRequest>`, merges
    those formulas, then saves the result to a file at the given path.
    """
    print("Encoding experiment constraints...")
    combined_cnf = combine_cnf_with_requests(initial_cnf, fresh, support, generation_requests)
    save_cnf(filename, combined_cnf, fresh, support)

def combine_and_save_opb(filename: Path,
                         cnf: CNF,
                         support: int,
                         generation_requests: List[GenerationRequest]):
    print("Encoding experiment constraints...")

    with open(filename, 'a') as opb_file:
        opb_file.write(cnf.as_opb_string())

        for request in generation_requests:
            if request.assertion_type is AssertionType.EQ:
                comparison = ' = ' + str(request.k)
            elif request.assertion_type is AssertionType.LT:
                comparison = ' <= ' + str(request.k - 1)
            elif request.assertion_type is AssertionType.GT:
                comparison = ' >= ' + str(request.k - 1)
            else:
                raise ValueError(f"invalid assertion type: {request.assertion_type}")
            opb_file.write('\n' + ' '.join(map(lambda x :  '+1 v' + str(x), request.boolean_values)) \
                                    + comparison + ' ; ')
