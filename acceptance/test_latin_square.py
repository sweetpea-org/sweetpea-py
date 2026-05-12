
import operator as op
import pytest

from sweetpea import *

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('config', [(1, 16),
                                    (8, 576),
                                    (5, 192)])
def test_latin_square_uncrossed(strategy, config):
    (min_trials, expected_count) = config
    
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2"])
    
    outer = CrossBlock([A, B, C], [A, C], [LatinSquare([A, B]), MinimumTrials(min_trials)])
    
    exps = synthesize_trials(outer, 1000, sampling_strategy=IterateGen)
    assert len(exps) == expected_count

def test_latin_square_merge():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2"])

    orig = CrossBlock([A, C], [A, C], [])
    more = MultiCrossBlock([B], [], [])

    outer = Merge([orig, more], [LatinSquare([A, B]), MinimumTrials(8)],
                  mode = RepeatMode.WEIGHT)

    exps = synthesize_trials(outer, 1000, sampling_strategy=IterateGen)
    assert len(exps) == 576
