import operator as op
import pytest

from itertools import permutations

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row, exclude
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy
from sweetpea import multiple_cross_block, synthesize_trials_non_uniform, synthesize_trials
from sweetpea.tests.test_utils import get_level_from_name

# Basic setup
color_list = ["red", "blue"]
color = factor("color", color_list)
text  = factor("text",  color_list)
mix   = factor("text",  color_list)

# Congruent factor
con_level  = derived_level("con", within_trial(op.eq, [color, text]))
inc_level  = derived_level("inc", within_trial(op.ne, [color, text]))
con_factor = factor("congruent?", [con_level, inc_level])

# Repeated color factor
repeated_color_factor = factor("repeated color?", [
    derived_level("yes", transition(lambda colors: colors[0] == colors[1], [color])),
    derived_level("no",  transition(lambda colors: colors[0] != colors[1], [color]))
])

# Repeated text factor
repeated_text_factor = factor("repeated text?", [
    derived_level("yes", transition(lambda texts: texts[0] == texts[1], [text])),
    derived_level("no",  transition(lambda texts: texts[0] != texts[1], [text]))
])


@pytest.mark.parametrize('design', permutations([color, text, mix]))
def test_correct_solution_count(design):
    crossing = [[color, mix], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, con_factor]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = [at_most_k_in_a_row(1, (con_factor, get_level_from_name(con_factor, "con")))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 48


@pytest.mark.parametrize('design', permutations([color, text, mix, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained_exactly(design):
    crossing = [[color, text], [text, mix]]
    constraints = [exactly_k_in_a_row(2, con_factor)]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 32


@pytest.mark.parametrize('design', permutations([color, text, mix, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_but_unconstrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_constrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = [at_most_k_in_a_row(1, (repeated_color_factor, get_level_from_name(repeated_color_factor, "yes")))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    # With only two colors, there can never be two color repetitons anyways,
    # so the total should still be the same.
    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_but_unconstrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_and_constrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = [
        at_most_k_in_a_row(1, (repeated_color_factor, get_level_from_name(repeated_color_factor, "yes"))),
        at_most_k_in_a_row(1, (repeated_text_factor, get_level_from_name(repeated_text_factor, "yes")))
    ]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([color, text, mix, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed(design):
    crossing = [[color, text], [mix, text]]
    constraints = [exclude(repeated_color_factor, get_level_from_name(repeated_color_factor, "yes"))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 32
