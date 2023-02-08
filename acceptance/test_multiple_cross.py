import operator as op
import pytest

from sweetpea import *
from sweetpea._internal.server import build_cnf
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)
mix   = Factor("mix",  color_list)

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

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('add_transition', [False, True])
def test_correct_solutions_with_different_crossing_sizes(strategy, add_transition):
    mix   = Factor("mix",  ["cake", "concrete", "tape"])
    design = [color, mix, text] + ([repeated_color_factor] if add_transition else [])
    crossing = [[color, text] + ([repeated_color_factor] if add_transition else []), [text, mix]]
    constraints = []

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 10, RandomGen)

    start = 1 if add_transition else 0

    assert len(experiments[0]['color']) == (9 if add_transition else 6)

    for e in experiments:
        seen = {}
        if add_transition:
            for i in range(1, 9):
                key = (e['color'][i], e['text'][i], e['repeated color?'][i])
                assert key not in seen
                seen[key] = True
            for i in range(1, 9):
                key = (e['text'][i], e['mix'][i])
                if key in seen:
                    assert seen[key] == 1
                    seen[key] = 2
                else:
                    seen[key] = 1
        else:
            for i in range(6):
                key = (e['text'][i], e['mix'][i])
                assert key not in seen
                seen[key] = True
            for i in range(6):
                key = ('one', e['color'][i], e['text'][i])
                if key in seen:
                    assert seen[key] == 1
                    seen[key] = 2
                else:
                    seen[key] = 1

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix], 6))
def test_correct_solution_count(strategy, design):
    crossing = [[color, mix], [text, mix]]
    constraints = []

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 96


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_but_unconstrained(strategy, design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 96


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_and_constrained(strategy, design):
    crossing = [[color, text], [text, mix]]
    constraints = [AtMostKInARow(1, (con_factor, "con"))]

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 48


def test_correct_solution_count_with_congruence_factor_and_constrained_cnf(design=[color, text, mix, con_factor]):
    crossing = [[color, text], [text, mix]]
    constraints = [AtMostKInARow(1, (con_factor, "con"))]

    block  = MultiCrossBlock(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, con_factor], 6))
def test_correct_solution_count_with_congruence_factor_and_constrained_exactly(strategy, design):
    crossing = [[color, text], [text, mix]]
    constraints = [ExactlyKInARow(2, con_factor)]

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 32


def test_correct_solution_count_with_congruence_factor_and_constrained_exactly_cnf(design=[color, text, mix, con_factor]):
    crossing = [[color, text], [text, mix]]
    constraints = [ExactlyKInARow(2, con_factor)]

    block  = MultiCrossBlock(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained_exactly.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_congruence_factor_and_constrained_exactly.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_but_unconstrained(strategy, design):
    crossing = [[color, text], [text, mix]]
    constraints = []

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 96

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_and_constrained(strategy, design):
    crossing = [[color, text], [mix, text]]
    constraints = [AtMostKInARow(1, (repeated_color_factor, "yes"))]

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    # With only two colors, there can never be two color repetitions anyways,
    # so the total should still be the same.
    assert len(experiments) == 96

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor, repeated_text_factor], 6))
def test_correct_solution_count_with_repeated_color_and_text_factors_but_unconstrained(strategy, design):
    crossing = [[color, text], [mix, text]]
    constraints = []

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 96


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor, repeated_text_factor], 6))
def test_correct_solution_count_with_repeated_color_and_text_factors_and_constrained(strategy, design):
    crossing = [[color, text], [mix, text]]
    constraints = [
        AtMostKInARow(1, (repeated_color_factor, "yes")),
        AtMostKInARow(1, (repeated_text_factor, "yes"))
    ]

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 96


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('design', shuffled_design_sample([color, text, mix, repeated_color_factor], 6))
def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed(strategy, design):
    crossing = [[color, text], [mix, text]]
    constraints = [Exclude(repeated_color_factor["yes"])]

    block  = MultiCrossBlock(design, crossing, constraints)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == 32


def test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed_cnf(design=[color, text, mix, repeated_color_factor]):
    crossing = [[color, text], [mix, text]]
    constraints = [Exclude(repeated_color_factor["yes"])]

    block  = MultiCrossBlock(design, crossing, constraints)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_repeated_color_factor_and_no_repetition_allowed.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_works_with_much_smaller_first_crossing(strategy, design=[color, text, mix, repeated_color_factor]):
    a = Factor("a", ["a1", "a2"])
    b = Factor("b", ["b1", "b2"])
    c = Factor("c", ["c1", "c2"])
    design = [a, b, c]
    crossing = [[c], [a,b]]
    block=MultiCrossBlock(design,crossing,[])
    
    experiments = synthesize_trials(block, 1, strategy)
    assert len(experiments[0]["a"]) == 4
    
    for e in experiments:
        seen = {}
        for i in range(0, 4):
            key = e['c'][i]
            if key in seen:
                assert seen[key] == 1
                seen[key] = 2
            else:
                seen[key] = 1
        seen = {}
        for i in range(0, 4):
            key = (e['a'][i], e['b'][i])
            assert key not in seen
            seen[key] = True
