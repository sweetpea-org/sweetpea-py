import operator as op
import pytest

from itertools import permutations

from sweetpea import factor, derived_level, else_level, within_trial, at_most_k_in_a_row, transition
from sweetpea import fully_cross_block, synthesize_trials_non_uniform


congruency            = factor("congruency", ["congruent", "incongruent", "neutral"])
congruency_transition = factor("congruency_transition", [
    derived_level("con-con", transition(lambda c: c[0] == "congruent"   and c[1] == "congruent",   [congruency])),
    derived_level("con-inc", transition(lambda c: c[0] == "congruent"   and c[1] == "incongruent", [congruency])),
    derived_level("con-ntr", transition(lambda c: c[0] == "congruent"   and c[1] == "neutral",     [congruency])),
    derived_level("inc-con", transition(lambda c: c[0] == "incongruent" and c[1] == "congruent",   [congruency])),
    derived_level("inc-inc", transition(lambda c: c[0] == "incongruent" and c[1] == "incongruent", [congruency])),
    derived_level("inc-ntr", transition(lambda c: c[0] == "incongruent" and c[1] == "neutral",     [congruency])),
    derived_level("ntr-con", transition(lambda c: c[0] == "neutral"     and c[1] == "congruent",   [congruency])),
    derived_level("ntr-inc", transition(lambda c: c[0] == "neutral"     and c[1] == "incongruent", [congruency])),
    else_level("ntr-ntr")
])

@pytest.mark.parametrize('design', permutations([congruency, congruency_transition]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [congruency]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 6
