import pytest

from itertools import permutations

from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
from sweetpea.constraints import at_most_k_in_a_row, exclude
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea.primitives import factor, derived_level, window
from sweetpea.tests.test_utils import get_level_from_name

# Basic setup
color_list = ["red", "blue"]
color = factor("color", color_list)
text  = factor("text",  color_list)

# congruent 'bookend' factor. (color and text in first and last trial are congruent)
congruent_bookend = factor("congruent bookend?", [
    derived_level("yes", window(lambda color, text: color == text, [color, text], 1, 3)),
    derived_level("no",  window(lambda color, text: color != text, [color, text], 1, 3))
])


@pytest.mark.parametrize('design', permutations([color, text, congruent_bookend]))
def test_correct_solution_count_when_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, congruent_bookend]))
def test_correct_solution_count_when_bookends_must_be_congruent(design):
    crossing = [color, text]

    # Require both bookends to be congruent.
    constraints = [exclude(congruent_bookend, get_level_from_name(congruent_bookend, "no"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 4


@pytest.mark.parametrize('design', permutations([color, text, congruent_bookend]))
def test_correct_solution_count_when_bookends_must_not_be_congruent(design):
    crossing = [color, text]

    # Require both bookends to not be congruent.
    constraints = [exclude(congruent_bookend, get_level_from_name(congruent_bookend, "yes"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 4


@pytest.mark.parametrize('design', permutations([color, text, congruent_bookend]))
def test_correct_solution_count_when_bookends_must_not_match_each_other(design):
    crossing = [color, text]

    # Require both bookends to be incongruent with each other.
    constraints = [at_most_k_in_a_row(1, congruent_bookend)]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 16
