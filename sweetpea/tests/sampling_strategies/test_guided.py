import pytest

from sweetpea.logic import And
from sweetpea.sampling_strategies.guided import Guided


def test_committed_to_solution():
    assert Guided._Guided__committed_to_solution([
        And([1, 3, 5]),
        And([2, 4, 6])
    ]) == [1, 3, 5, 2, 4, 6]
