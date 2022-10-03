import operator as op
import pytest

from itertools import permutations

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row, exclude
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, synthesize_trials

# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent Factor
con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

# Repeated color Factor
repeated_color_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

# Repeated text Factor
repeated_text_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[1], [text]))
])


@pytest.mark.parametrize('design', permutations([color, text]))
def test_correct_solution_count(design):
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained(design):
    crossing = [color, text]
    constraints = [at_most_k_in_a_row(1, (con_factor, "con"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 12


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained_exactly(design):
    crossing = [color, text]
    constraints = [exactly_k_in_a_row(2, con_factor)]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 8


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_constrained(design):
    crossing = [color, text]
    constraints = [at_most_k_in_a_row(1, (repeated_color_factor, "yes"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    # With only two colors, there can never be two color repetitions anyways,
    # so the total should still be the same.
    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_and_constrained(design):
    crossing = [color, text]
    constraints = [
        at_most_k_in_a_row(1, (repeated_color_factor, "yes")),
        at_most_k_in_a_row(1, (repeated_text_factor, "yes"))
    ]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed(design):
    crossing = [color, text]
    constraints = [exclude(repeated_color_factor, "yes")]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 8
