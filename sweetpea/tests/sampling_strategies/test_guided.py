import pytest

from sweetpea._internal.logic import And
from sweetpea._internal.sampling_strategy.guided import GuidedGen


def test_committed_to_solution():
    assert GuidedGen._GuidedGen__committed_to_solution([
        And([1, 3, 5]),
        And([2, 4, 6])
    ]) == [1, 3, 5, 2, 4, 6]
