import operator as op
import pytest

from sweetpea import *

@pytest.mark.slow
@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_nest_block_correct_solution_count(strategy):
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    inner = CrossBlock([A, B], [A, B], [])

    session = Factor("session", ["s1", "s2"])
    outer = CrossBlock([session], [session], [])

    nb = Nest(outer, inner, [])

    exps = synthesize_trials(nb, 2000, sampling_strategy=strategy)
    assert len(exps) == 24 * 24 *2

def test_nest_block_dependent_correct_solution_count():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])

    def consi(a, b):
        return (a == "a1" and b == "b1") or (a == "a2" and b == "b2") 

    E = Factor("E", [DerivedLevel("consi", WithinTrial(consi, [A, B])),
                     ElseLevel("incons")])

    outer = CrossBlock([A, B, E], [A, E], [])

    session = Factor("session", ["s1", "s2"])
    inner = CrossBlock([session], [session], [])
    
    nb = Nest(outer, inner, [], alignment=AlignmentMode.POST_PREAMBLE)

    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateSATGen)
    assert len(exps) == 384
