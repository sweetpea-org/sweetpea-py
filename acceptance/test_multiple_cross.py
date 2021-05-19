import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row, exclude
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy
from sweetpea import multiple_cross_block, synthesize_trials_non_uniform, synthesize_trials
from sweetpea.tests.test_utils import get_level_from_name
from sweetpea.server import build_cnf
from acceptance import shuffled_design_sample, path_to_cnf_files

# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)
mix   = Factor("text",  color_list)

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


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix], 6))
def test_correct_solution_count(design):
    crossing = [[color, mix], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_and_constrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = [at_most_k_in_a_row(1, (con_factor, get_level_from_name(con_factor, "con")))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 48


def test_correct_solution_count_with_congruence_factor_and_constrained_cnf(design=[color, text, mix, con_factor]):
    crossing = [[color, text], [text, mix]]
    constraints = [at_most_k_in_a_row(1, (con_factor, get_level_from_name(con_factor, "con")))]

    block  = multiple_cross_block(design, crossing, constraints)
    cnf = build_cnf(block)

    # with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained.cnf', 'w') as f:
    #     f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_and_constrained_exactly(design):
    crossing = [[color, text], [text, mix]]
    constraints = [exactly_k_in_a_row(2, con_factor)]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 32


def test_correct_solution_count_with_congruence_factor_and_constrained_exactly_cnf(design=[color, text, mix, con_factor]):
    crossing = [[color, text], [text, mix]]
    constraints = [exactly_k_in_a_row(2, con_factor)]

    block  = multiple_cross_block(design, crossing, constraints)
    cnf = build_cnf(block)

    # with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained_exactly.cnf', 'w') as f:
    #     f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained_exactly.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_but_unconstrained(design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_and_constrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = [at_most_k_in_a_row(1, (repeated_color_factor, get_level_from_name(repeated_color_factor, "yes")))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    # With only two colors, there can never be two color repetitions anyways,
    # so the total should still be the same.
    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor, repeated_text_factor], 6))
def test_correct_solution_count_with_repeated_color_and_text_factors_but_unconstrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = []

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor, repeated_text_factor], 6))
def test_correct_solution_count_with_repeated_color_and_text_factors_and_constrained(design):
    crossing = [[color, text], [mix, text]]
    constraints = [
        at_most_k_in_a_row(1, (repeated_color_factor, get_level_from_name(repeated_color_factor, "yes"))),
        at_most_k_in_a_row(1, (repeated_text_factor, get_level_from_name(repeated_text_factor, "yes")))
    ]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 96


@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed(design):
    crossing = [[color, text], [mix, text]]
    constraints = [exclude(repeated_color_factor, get_level_from_name(repeated_color_factor, "yes"))]

    block  = multiple_cross_block(design, crossing, constraints)
    experiments  = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 32


def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed_cnf(design=[color, text, mix, repeated_color_factor]):
    crossing = [[color, text], [mix, text]]
    constraints = [exclude(repeated_color_factor, get_level_from_name(repeated_color_factor, "yes"))]

    block  = multiple_cross_block(design, crossing, constraints)
    cnf = build_cnf(block)

    # with open(path_to_cnf_files+'/test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed.cnf', 'w') as f:
    #     f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()
