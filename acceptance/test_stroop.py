import operator as op
import pytest

from itertools import permutations

from sweetpea import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea import AtMostKInARow, ExactlyKInARow, Exclude
from sweetpea import IterateGen
from sweetpea import CrossBlock, synthesize_trials, synthesize_trials

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
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])

# Repeated text Factor
repeated_text_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[-1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[-1], [text]))
])


@pytest.mark.parametrize('design', permutations([color, text]))
def test_correct_solution_count(design):
    crossing = [color, text]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained(design):
    crossing = [color, text]
    constraints = [AtMostKInARow(1, (con_factor, "con"))]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 12


@pytest.mark.parametrize('design', permutations([color, text, con_factor]))
def test_correct_solution_count_with_congruence_factor_and_constrained_exactly(design):
    crossing = [color, text]
    constraints = [ExactlyKInARow(2, con_factor)]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 8


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_constrained(design):
    crossing = [color, text]
    constraints = [AtMostKInARow(1, (repeated_color_factor, "yes"))]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    # With only two colors, there can never be two color repetitions anyways,
    # so the total should still be the same.
    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_but_unconstrained(design):
    crossing = [color, text]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor, repeated_text_factor]))
def test_correct_solution_count_with_repeated_color_and_text_factors_and_constrained(design):
    crossing = [color, text]
    constraints = [
        AtMostKInARow(1, (repeated_color_factor, "yes")),
        AtMostKInARow(1, (repeated_text_factor, "yes"))
    ]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 24


@pytest.mark.parametrize('design', permutations([color, text, repeated_color_factor]))
def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed(design):
    crossing = [color, text]
    constraints = [Exclude(repeated_color_factor["yes"])]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 8
