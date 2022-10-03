import pytest

from itertools import permutations

from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
from sweetpea.constraints import at_most_k_in_a_row, exclude
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea.primitives import Factor, DerivedLevel, Window
from sweetpea.server import build_cnf
from acceptance import path_to_cnf_files, reset_expected_solutions

# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# congruent 'bookend' Factor. (color and text in first and last trial are congruent)
congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", Window(lambda color, text: color == text, [color, text], 1, 3)),
    DerivedLevel("no",  Window(lambda color, text: color != text, [color, text], 1, 3))
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
    constraints = [exclude(congruent_bookend, "no")]

    block  = fully_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 4


@pytest.mark.parametrize('design', permutations([color, text, congruent_bookend]))
def test_correct_solution_count_when_bookends_must_not_be_congruent(design):
    crossing = [color, text]

    # Require both bookends to not be congruent.
    constraints = [exclude(congruent_bookend, "yes")]

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

def test_correct_solution_count_when_bookends_must_not_match_each_other_cnf(design=[color, text, congruent_bookend]):
    crossing = [color, text]

    # Require both bookends to be incongruent with each other.
    constraints = [at_most_k_in_a_row(1, congruent_bookend)]

    block  = fully_cross_block(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_when_bookends_must_not_match_each_other.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_when_bookends_must_not_match_each_other.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()
