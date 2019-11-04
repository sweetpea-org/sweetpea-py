from acceptance import assert_no_repetition
from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import exclude
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
from sweetpea.tests.test_utils import get_level_from_name

color      = factor("color",  ["red", "blue", "green"])
word       = factor("motion", ["red", "blue"])

def illegal_stimulus(color, word):
    return color == "green" and word == "blue"

def legal_stimulus(color, word):
    return not illegal_stimulus(color, word)

stimulus_configuration = factor("stimulus configuration", [
    derived_level("legal",   within_trial(legal_stimulus, [color, word])),
    derived_level("illegal", within_trial(illegal_stimulus, [color, word]))
])

constraints = [exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "illegal"))]

design       = [color, word, stimulus_configuration]
crossing     = [color, word]


def test_no_solutions_without_override_flag():
    block       = fully_cross_block(design, crossing, constraints)
    experiments = synthesize_trials_non_uniform(block, 500)

    assert block.crossing_size() == 6
    assert len(experiments) == 0
    assert_no_repetition(experiments)


def test_correct_solution_count_with_override_flag():
    block       = fully_cross_block(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials_non_uniform(block, 500)

    assert block.crossing_size() == 5
    assert len(experiments) == 120
    assert_no_repetition(experiments)


def test_correct_solution_count_with_override_flag_and_multiple_trials_excluded():
    # With this constraint, there should only be ONE allowed crossing, and therefore one solution.
    constraints = [exclude(stimulus_configuration, get_level_from_name(stimulus_configuration, "legal"))]
    block       = fully_cross_block(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials_non_uniform(block, 500)

    assert block.crossing_size() == 1
    assert len(experiments) == 1
    assert_no_repetition(experiments)
