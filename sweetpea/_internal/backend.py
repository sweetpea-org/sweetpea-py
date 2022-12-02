"""This module provides functionality for making requests to the backend."""


from typing import List

from sweetpea._internal.logic import And, cnf_to_json
from sweetpea._internal.core import Var
from sweetpea._internal.core.generate.utility import GenerationRequest, AssertionType


class LowLevelRequest:
    """Represents an individual low-level request to the backend."""

    comparisons = ['EQ', 'LT', 'GT']  # will we want more comparisons in the future?

    def __init__(self, comparison: str, k: int, variables: List[int]) -> None:
        self.comparison = comparison
        self.k = k
        self.variables = variables
        self.__validate()

    def __validate(self):
        if self.comparison not in self.comparisons:
            raise ValueError('LowLevelRequest.comparison must be one of ' + str(self.comparisons))

        if not isinstance(self.k, int):
            raise ValueError('LowLevelRequest.k must be an integer')
        # TODO - Non-empty list, list containing non-integers

    def to_dict(self):
        """Converts this request to a dict suitable for conversion to json and
        then the backend.
        """

        return {
            'equalityType': self.comparison,
            'k': self.k,
            'booleanValues': self.variables
        }

    def to_generation_request(self):
        return GenerationRequest(AssertionType[self.comparison], self.k, [Var(v) for v in self.variables])

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class BackendRequest:
    """Represents a full request to the backend, including CNFs,
    LowLevelRequests, and unigen arguments.
    """

    def __init__(self, fresh: int, cnfs: List[And] = [], ll_requests: List[LowLevelRequest] = []) -> None:
        self.cnfs = list(cnfs)
        self.ll_requests = list(ll_requests)
        self.fresh = fresh
        self.support = -1
        self.solution_count = -1

    def get_cnfs_as_json(self):
        return cnf_to_json(self.cnfs)

    def get_requests_as_json(self):
        return list(map(lambda r: r.to_dict(), self.ll_requests))

    def get_requests_as_generation_requests(self):
        return list(map(lambda r: r.to_generation_request(), self.ll_requests))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
