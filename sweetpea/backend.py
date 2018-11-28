import json
import math

from typing import List
from sweetpea.logic import And, cnf_to_json


"""
Represents an individual low-level request to the backend.
"""
class LowLevelRequest:
    comparisons = ['EQ', 'LT', 'GT']

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

    """
    Converts this request to a dict suitable for conversion to json and then the backend.
    """
    def to_dict(self):
        return {
            'equalityType': self.comparison,
            'k': self.k,
            'booleanValues': self.variables
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


"""
Represents a full request to the backend, including CNFs, LowLevelRequests, and
unigen arguments.
"""
class BackendRequest:
    def __init__(self, fresh: int, cnfs: List[And] = [], ll_requests: List[LowLevelRequest] = []) -> None:
        self.cnfs = list(cnfs)
        self.ll_requests = list(ll_requests)
        self.fresh = fresh
        self.support = -1
        self.solution_count = -1

    def to_json(self, support: int, solution_count: int):

        # Taken from the unigen2.py script: https://bitbucket.org/kuldeepmeel/unigen/src/4677b2ec4553b2a44a31910db0037820abdc1394/UniGen2.py?at=master&fileviewer=file-view-default
        kappa = 0.638
        pivot_unigen = math.ceil(4.03 * (1 + 1 / kappa) * (1 + 1 / kappa))
        log_count = math.log(solution_count, 2)
        start_iteration = int(round(log_count + math.log(1.8, 2) - math.log(pivot_unigen, 2))) - 2

        return json.dumps({ "fresh" : self.fresh,
                            "cnfs" : cnf_to_json(self.cnfs),
                            "requests" : list(map(lambda r: r.to_dict(), self.ll_requests)),
                            "unigen" : {
                                "support" : support,
                                "arguments" : [
                                    "--verbosity=0",
                                    "--samples=100",
                                    "--kappa=" + str(kappa),
                                    "--pivotUniGen=" + str(pivot_unigen),
                                    "--startIteration=" + str(start_iteration),
                                    "--maxLoopTime=3000",
                                    "--maxTotalTime=72000",
                                    "--tApproxMC=1",
                                    "--pivotAC=60",
                                    "--gaussuntil=400"
                                ]
                            }})

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)