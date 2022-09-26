import pytest

from acceptance import assert_no_repetition, path_to_cnf_files, reset_expected_solutions
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import exclude
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea import UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy
from sweetpea import fully_cross_block, synthesize_trials, print_experiments
from sweetpea.tests.test_utils import get_level_from_name
from sweetpea.server import build_cnf
from sweetpea.server import build_cnf

color      = Factor("color",  ["red", "blue", "green"])
word       = Factor("motion", ["red", "blue"])

def illegal_stimulus(color, word):
    return color == "green" and word == "blue"

def legal_stimulus(color, word):
    return not illegal_stimulus(color, word)

stimulus_configuration = Factor("stimulus configuration", [
    DerivedLevel("legal",   WithinTrial(legal_stimulus, [color, word])),
    DerivedLevel("illegal", WithinTrial(illegal_stimulus, [color, word]))
])

constraints = [exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "illegal"))]

design       = [color, word, stimulus_configuration]
crossing     = [color, word]


@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_no_solutions_without_override_flag(strategy):
    block       = fully_cross_block(design, crossing, constraints)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 6
    assert len(experiments) == 0
    assert_no_repetition(experiments)

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_correct_solution_count_with_override_flag(strategy):
    block       = fully_cross_block(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 5
    assert len(experiments) == 120
    assert_no_repetition(experiments)  # FIXME

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_correct_solution_count_with_override_flag_and_multiple_trials_excluded(strategy):
    # With this constraint, there should only be ONE allowed crossing, and therefore one solution.
    constraints = [exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "legal"))]
    block       = fully_cross_block(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 1
    assert len(experiments) == 1
    assert_no_repetition(experiments)

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_correct_solution_count_with_crossing_levels_excluded(strategy):
    color = Factor("color", ['red', 'green'])
    size = Factor("size", ['small', 'med', 'large'])

    red = color.get_level('red')
    med = size.get_level('med')

    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="up", window=WithinTrial(predicate=lambda a, b: b != 'large', factors=[color, size])),
        DerivedLevel(name="down", window=WithinTrial(predicate=lambda a, b: b == 'large', factors=[color, size]))
    ])

    block      = fully_cross_block(design=[color, size, match],
                                   crossing=[color, match],
                                   constraints=[exclude(color, red)],
                                   require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 4
    assert len(experiments[0][list(experiments[0].keys())[0]]) == 2

    for e in experiments:
        for l in e['color']:
            assert l != 'red'

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_correct_solution_count_with_design_levels_excluded(strategy):
    color = Factor("color", ['red', 'green'])
    size = Factor("size", ['small', 'med', 'large'])
    
    red = color.get_level('red')
    med = size.get_level('med')
    
    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="up", window=WithinTrial(predicate=lambda a, b: b != 'large', factors=[color, size])),
        DerivedLevel(name="down", window=WithinTrial(predicate=lambda a, b: b == 'large', factors=[color, size]))
    ])
    down = match.get_level('down')

    block      = fully_cross_block(design=[color, size, match], crossing=[color, size],
                                   constraints=[exclude(match, down)],
                                   require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 24
    assert len(experiments[0][list(experiments[0].keys())[0]]) == 4
    
    for e in experiments:
        for l in e['size']:
            assert l != 'large'

def test_correct_solution_count_with_override_flag_and_multiple_trials_excluded_cnf():
    # With this constraint, there should only be ONE allowed crossing, and therefore one solution.
    constraints = [exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "legal"))]
    block       = fully_cross_block(design, crossing, constraints, require_complete_crossing=False)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_override_flag_and_multiple_trials_excluded.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_override_flag_and_multiple_trials_excluded.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()  # FIXME
