import operator as op
import pytest

from sweetpea import Factor, DerivedLevel, WithinTrial, NoMoreThanKInARow, Transition
from sweetpea import fully_cross_block, synthesize_trials_non_uniform


# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent factor
con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

# Repeated color factor
repeated_color_factor = Factor("repeated color?", [
  DerivedLevel("repeated", Transition(op.eq, [color, color])),
  DerivedLevel("not repeated", Transition(op.ne, [color, color]))
])


def test_correct_solution_count():
    design = [color, text]
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


def test_correct_solution_count_with_congruence_factor_but_unconstrained():
    design = [color, text, con_factor]
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


def test_correct_solution_count_with_congruence_factor_and_constrained():
    design = [color, text, con_factor]
    crossing = [color, text]
    constraints = [NoMoreThanKInARow(1, ("congruent?", "con"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 12


def test_correct_solution_count_with_repeated_color_factor_but_unconstrained():
    design = [color, text, repeated_color_factor]
    crossing = [color, text]
    constraints = []

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 24


def test_correct_solution_count_with_repeated_color_factor_and_constrained():
    design = [color, text, repeated_color_factor]
    crossing = [color, text]
    constraints = [NoMoreThanKInARow(1, ("repeated color?", "repeated"))]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)
    
    # With only two colors, there can never be two color repetitons anyways,
    # so the total should still be the same.
    assert len(experiments) == 24
