import operator as op
import pytest

from itertools import permutations

from sweetpea import fully_cross_block, synthesize_trials_non_uniform
from sweetpea.constraints import at_most_k_in_a_row, Reify
from sweetpea.primitives import Factor, DerivedLevel, ElseLevel, WithinTrial, Transition
from sweetpea.server import build_cnf
from acceptance import path_to_cnf_files, reset_expected_solutions


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
    ElseLevel("ntr-ntr")
])

@pytest.mark.parametrize('design', permutations([congruency, congruency_transition]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [congruency]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 6


def test_correct_solution_count_with_congruence_factor_but_unconstrained_cnf(design=[congruency, congruency_transition]):
    crossing = [congruency]
    constraints = list(map(Reify, design))

    block  = fully_cross_block(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_but_unconstrained.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_but_unconstrained.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()
