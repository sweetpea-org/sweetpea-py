import pytest
import operator as op

from itertools import permutations

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
from sweetpea.tests.test_utils import get_level_from_name


direction = factor("direction", ["up", "down"])

color_list = ["red", "blue"]
color = factor("color", color_list)
text  = factor("text",  color_list)

congruent_factor = factor("congruent?", [
    derived_level("con", within_trial(op.eq, [color, text])),
    derived_level("inc", within_trial(op.ne, [color, text]))
])

repeated_color_factor = factor("repeated color?", [
    derived_level("yes", transition(lambda colors: colors[0] == colors[1], [color])),
    derived_level("no",  transition(lambda colors: colors[0] != colors[1], [color]))
])


@pytest.mark.parametrize('design', [[direction, color, text, congruent_factor],
                                    [congruent_factor, direction, color, text],
                                    [direction, congruent_factor, color, text]])
def test_correct_solution_count_when_unconstrained(design):
    crossing = [direction, congruent_factor]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 500)

    assert len(experiments) == 384


@pytest.mark.parametrize('design', permutations([direction, color, text, congruent_factor]))
def test_correct_solution_count_when_constrained(design):
    crossing = [direction, congruent_factor]
    constraints = [at_most_k_in_a_row(1, congruent_factor)]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 500)

    assert len(experiments) == 128


@pytest.mark.parametrize('design', permutations([direction, color, repeated_color_factor]))
def test_correct_solution_count_when_transition_in_crossing_and_unconstrained(design):
    crossing = [direction, repeated_color_factor]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([direction, color, repeated_color_factor]))
def test_correct_solution_count_when_transition_in_crossing_and_constrained(design):
    crossing = [direction, repeated_color_factor]
    constraints = [at_most_k_in_a_row(1, (color, get_level_from_name(color, "red")))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 32


@pytest.mark.parametrize('design', permutations([color, repeated_color_factor]))
def test_correct_solution_count_when_crossing_with_derived_transition(design):
    crossing = [color, repeated_color_factor]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 4
