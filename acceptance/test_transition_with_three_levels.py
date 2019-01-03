import operator as op
import pytest

from itertools import permutations

from sweetpea import Factor, DerivedLevel, WithinTrial, NoMoreThanKInARow, Transition
from sweetpea import fully_cross_block, synthesize_trials_non_uniform


congruency            = Factor("congruency", ["congruent", "incongruent", "neutral"])
congruency_transition = Factor("congruency_transition", [
    DerivedLevel("con-con", Transition(lambda c: c[0] == "congruent"   and c[1] == "congruent",   [congruency])),
    DerivedLevel("con-inc", Transition(lambda c: c[0] == "congruent"   and c[1] == "incongruent", [congruency])),
    DerivedLevel("con-ntr", Transition(lambda c: c[0] == "congruent"   and c[1] == "neutral",     [congruency])),
    DerivedLevel("inc-con", Transition(lambda c: c[0] == "incongruent" and c[1] == "congruent",   [congruency])),
    DerivedLevel("inc-inc", Transition(lambda c: c[0] == "incongruent" and c[1] == "incongruent", [congruency])),
    DerivedLevel("inc-ntr", Transition(lambda c: c[0] == "incongruent" and c[1] == "neutral",     [congruency])),
    DerivedLevel("ntr-con", Transition(lambda c: c[0] == "neutral"     and c[1] == "congruent",   [congruency])),
    DerivedLevel("ntr-inc", Transition(lambda c: c[0] == "neutral"     and c[1] == "incongruent", [congruency])),
    DerivedLevel("ntr-ntr", Transition(lambda c: c[0] == "neutral"     and c[1] == "neutral",     [congruency])),
])

@pytest.mark.parametrize('design', permutations([congruency, congruency_transition]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [congruency]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 6
