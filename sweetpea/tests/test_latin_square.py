import operator as op
import pytest

from sweetpea import *

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_latin_square_two_by_two(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    outer = CrossBlock([A, B], [A, B], [LatinSquare([A, B]), MinimumTrials(8)])
    exps = synthesize_trials(outer, 10, sampling_strategy=strategy)
    assert len(exps) == 10

    for e in exps:
        for j in range(0, 6, 2):
            assert { e["A"][i] for i in range(j, j+2) } == { "a1", "a2" }
            assert { e["B"][i] for i in range(j, j+2) } == { "b1", "b2" }

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_latin_square_two_by_two_uncrossed(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    outer = CrossBlock([A, B], [], [LatinSquare([A, B]), MinimumTrials(8)])
    exps = synthesize_trials(outer, 5, sampling_strategy=strategy)
    assert len(exps) == 5

    for e in exps:
        for j in range(0, 6, 2):
            assert { e["A"][i] for i in range(j, j+2) } == { "a1", "a2" }
            assert { e["B"][i] for i in range(j, j+2) } == { "b1", "b2" }

def test_latin_square_three_by_three():
    A = Factor("A", ["a1", "a2", "a3"])
    B = Factor("B", ["b1", "b2", "b3"])
    C = Factor("C", ["c1", "c2"])
    outer = CrossBlock([A, B, C], [A, C], [LatinSquare([A, B])])
    exps = synthesize_trials(outer, 1000, sampling_strategy=IterateGen)
    assert len(exps) == 288

def test_latin_rectangle1():
    A = Factor("A", ["a1", "a2", "a3", "a4"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2", "c3"])

    inner = CrossBlock([A, B, C], [A], [LatinSquare([A, B])])

    session = Factor("session", ["s1", "s2"])
    outer = CrossBlock([session], [session], [MinimumTrials(4)])

    nb = Nest(outer, inner, [])
    
    exps = synthesize_trials(nb, 10, sampling_strategy=IterateSATGen)
    assert len(exps) == 10

    for e in exps:
        assert { e["A"][i] for i in range(0, 4) } == { "a1", "a2", "a3", "a4" }
        assert { e["B"][i] for i in range(0, 2) } == { "b1", "b2" }
        assert { e["B"][i] for i in range(2, 4) } == { "b1", "b2" }

def test_latin_rectangle2():
    A = Factor("A", ["a1", "a2", "a3", "a4"])
    B = Factor("B", ["b1", "b2", "b3"])
    C = Factor("C", ["c1", "c2", "c3"])

    inner = CrossBlock([A, B, C], [A], [LatinSquare([A, B])])

    session = Factor("session", ["s1", "s2"])
    outer = CrossBlock([session], [session], [MinimumTrials(6)])

    nb = Nest(outer, inner, [])
    
    exps = synthesize_trials(nb, 10, sampling_strategy=IterateSATGen)
    assert len(exps) == 10

    for e in exps:
        assert { e["A"][i] for i in range(0, 4) } == { "a1", "a2", "a3", "a4" }
        assert { e["B"][i] for i in range(0, 4) } == { "b1", "b2", "b3" }
