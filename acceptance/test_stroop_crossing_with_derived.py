import pytest
import operator as op

from itertools import permutations

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea._internal.constraint import AtMostKInARow
from sweetpea._internal.encoding_diagram import print_encoding_diagram
from sweetpea import CrossBlock, synthesize_trials, print_experiments, IterateGen
from sweetpea._internal.server import build_cnf
from acceptance import path_to_cnf_files, reset_expected_solutions


direction = Factor("direction", ["up", "down"])

color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

congruent_factor = Factor("congruent?", [
    DerivedLevel("con", WithinTrial(op.eq, [color, text])),
    DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
])

repeated_color_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])


@pytest.mark.parametrize('design', [[direction, color, text, congruent_factor],
                                    [congruent_factor, direction, color, text],
                                    [direction, congruent_factor, color, text]])
def test_correct_solution_count_when_unconstrained(design):
    crossing = [direction, congruent_factor]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 500, IterateGen)

    assert len(experiments) == 384


@pytest.mark.parametrize('design', permutations([direction, color, text, congruent_factor]))
def test_correct_solution_count_when_constrained(design):
    crossing = [direction, congruent_factor]
    constraints = [AtMostKInARow(1, congruent_factor)]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 500, IterateGen)

    assert len(experiments) == 128


@pytest.mark.parametrize('design', permutations([direction, color, repeated_color_factor]))
def test_correct_solution_count_when_transition_in_crossing_and_unconstrained(design):
    crossing = [direction, repeated_color_factor]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', permutations([direction, color, repeated_color_factor]))
def test_correct_solution_count_when_transition_in_crossing_and_constrained(design):
    crossing = [direction, repeated_color_factor]
    constraints = [AtMostKInARow(1, (color, "red"))]

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 32


def test_correct_solution_count_when_transition_in_crossing_and_constrained_cnf(design=[direction, color, repeated_color_factor]):
    crossing = [direction, repeated_color_factor]
    constraints = [AtMostKInARow(1, (color, "red"))]

    block  = CrossBlock(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_when_transition_in_crossing_and_constrained.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_when_transition_in_crossing_and_constrained.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()


@pytest.mark.parametrize('design', permutations([color, repeated_color_factor]))
def test_correct_solution_count_when_crossing_with_derived_transition(design):
    crossing = [color, repeated_color_factor]
    constraints = []

    block  = CrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, IterateGen)

    assert len(experiments) == 4
