import pytest

from sweetpea.logic import And
from sweetpea.sampling_strategies.guided import GuidedSamplingStrategy


def test_committed_to_solution():
    assert GuidedSamplingStrategy._GuidedSamplingStrategy__committed_to_solution([
        And([1, 3, 5]),
        And([2, 4, 6])
    ]) == [1, 3, 5, 2, 4, 6]
