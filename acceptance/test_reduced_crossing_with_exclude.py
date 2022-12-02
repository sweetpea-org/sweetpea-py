import pytest

from acceptance import assert_no_repetition, path_to_cnf_files, reset_expected_solutions
from sweetpea import *
from sweetpea._internal.encoding_diagram import print_encoding_diagram
from sweetpea._internal.server import build_cnf

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

constraints = [Exclude(stimulus_configuration["illegal"])]

design       = [color, word, stimulus_configuration]
crossing     = [color, word]


@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_no_solutions_without_override_flag(strategy):
    block       = CrossBlock(design, crossing, constraints)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 5
    assert len(experiments) == 0
    assert_no_repetition(experiments)

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count_with_override_flag(strategy):
    block       = CrossBlock(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 5
    assert len(experiments) == 120
    assert_no_repetition(experiments)  # FIXME

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count_with_exclusion_via_complex_factor(strategy):
    def illegal_stimulus(color, word):
        return color[0] == "green" and word[0] == "blue"
    def legal_stimulus(color, word):
        return not illegal_stimulus(color, word)

    stimulus_configuration = Factor("stimulus configuration", [
        DerivedLevel("legal",   Transition(legal_stimulus, [color, word])),
        DerivedLevel("illegal", Transition(illegal_stimulus, [color, word]))
    ])

    constraints = [Exclude(stimulus_configuration["illegal"])]

    design       = [color, word, stimulus_configuration]
    crossing     = [color, word]

    block      = CrossBlock(design, crossing, constraints,
                            require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=150, sampling_strategy=strategy)

    assert len(experiments) == 120

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count_with_exclusion_via_nested_complex_factor(strategy):
    def unhappy_stimulus(color, word):
        return color[0] == "green" and word[0] == "blue"
    def happy_stimulus(color, word):
        return not unhappy_stimulus(color, word)
    smiley = Factor("smiley", [
        DerivedLevel("happy",   Transition(happy_stimulus, [color, word])),
        DerivedLevel("unhappy", Transition(unhappy_stimulus, [color, word]))
    ])

    def illegal_stimulus(smiley):
        return smiley == "unhappy"
    def legal_stimulus(smiley):
        return smiley == "happy"
    stimulus_configuration = Factor("stimulus configuration", [
        DerivedLevel("legal",   WithinTrial(legal_stimulus, [smiley])),
        DerivedLevel("illegal", WithinTrial(illegal_stimulus, [smiley]))
    ])

    constraints = [Exclude(stimulus_configuration["illegal"])]

    design       = [color, word, smiley, stimulus_configuration]
    crossing     = [color, word]

    block      = CrossBlock(design, crossing, constraints,
                            require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=150, sampling_strategy=strategy)

    assert len(experiments) == 120

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count_with_override_flag_and_multiple_trials_excluded(strategy):
    # With this constraint, there should only be ONE allowed crossing, and therefore one solution.
    constraints = [Exclude(stimulus_configuration["legal"])]
    block       = CrossBlock(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert block.crossing_size() == 1
    assert len(experiments) == 1
    assert_no_repetition(experiments)

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_count_with_crossing_levels_excluded(strategy):
    color = Factor("color", ['red', 'green'])
    size = Factor("size", ['small', 'med', 'large'])

    red = color.get_level('red')
    med = size.get_level('med')

    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="up", window=WithinTrial(predicate=lambda a, b: b != 'large', factors=[color, size])),
        DerivedLevel(name="down", window=WithinTrial(predicate=lambda a, b: b == 'large', factors=[color, size]))
    ])

    block      = CrossBlock(design=[color, size, match],
                            crossing=[color, match],
                            constraints=[Exclude(red)],
                            require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 4
    assert len(experiments[0][list(experiments[0].keys())[0]]) == 2

    for e in experiments:
        for l in e['color']:
            assert l != 'red'

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
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

    block      = CrossBlock(design=[color, size, match], crossing=[color, size],
                            constraints=[Exclude(down)],
                            require_complete_crossing=False)
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 24
    assert len(experiments[0][list(experiments[0].keys())[0]]) == 4
    
    for e in experiments:
        for l in e['size']:
            assert l != 'large'

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_with_extra_crossing_factor(strategy):
    color      = Factor("color",  ["red", "green", "blue", "brown"])
    word       = Factor("word", ["Red", "Green", "Blue", "Brown"])
    location       = Factor("location", ["up", "down", "left", "right"])

    def is_response_left(color):
        return color == "red"
    def is_response_right(color):
        return color == "green"
    def is_response_up(color):
        return color == "blue"
    def is_response_down(color):
        return color == "brown"

    response = Factor("response", [
        DerivedLevel("left", WithinTrial(is_response_left, [color])),
        DerivedLevel("right", WithinTrial(is_response_right, [color])),
        DerivedLevel("up", WithinTrial(is_response_up, [color])),
        DerivedLevel("down", WithinTrial(is_response_down, [color]))
    ])

    def is_congruent(color, word):
        return color[1:] == word[1:]

    def is_incongruent(color, word):
        return not is_congruent(color, word)

    congruent = DerivedLevel("congruent", WithinTrial(is_congruent, [color, word]))
    incongruent = DerivedLevel("incongruent", WithinTrial(is_incongruent, [color, word]))

    congruency = Factor("congruency", [
        congruent,
        incongruent
    ])


    constraints = [Exclude(congruent)]

    design       = [color, word, response, congruency, location]
    crossing     = [color, word, location]
    block        = CrossBlock(design, crossing, constraints,
                              require_complete_crossing=False)

    experiments  = synthesize_trials(block, 1, sampling_strategy=strategy)

    assert len(experiments[0]['color']) == 48 # would be 64 without exclude

    found = {}
    for i in range(len(experiments[0]['color'])):
        key = (experiments[0]['color'][i], experiments[0]['word'][i], experiments[0]['location'][i])
        assert not key in found
        found[key] = True

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solution_with_just_one_factor(strategy):
    color = Factor("color", ['red', 'green'])
    red = color.get_level('red')

    block      = CrossBlock(design=[color], crossing=[color],
                            require_complete_crossing=False,
                            constraints=[Exclude(red)])
    experiments = synthesize_trials(block=block, samples=1, sampling_strategy=strategy)

    assert len(experiments[0]['color']) == 1
    assert experiments[0]['color'][0] == 'green'

def test_correct_solution_count_with_override_flag_and_multiple_trials_excluded_cnf():
    # With this constraint, there should only be ONE allowed crossing, and therefore one solution.
    constraints = [Exclude(stimulus_configuration["legal"])]
    block       = CrossBlock(design, crossing, constraints, require_complete_crossing=False)
    cnf = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_correct_solution_count_with_override_flag_and_multiple_trials_excluded.cnf', 'w') as f:
            f.write(cnf.as_unigen_string())
    with open(path_to_cnf_files+'/test_correct_solution_count_with_override_flag_and_multiple_trials_excluded.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf.as_unigen_string()  # FIXME

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_correct_solutions_with_implicitly_excluded_crossing_due_to_derived_definition(strategy):
    def ugly_stimulus(color, word):
        return color == "green" and word == "red"
    def pretty_stimulus(color, word):
        return not ugly_stimulus(color, word)
    aesthetic = Factor("aesthetic", [
        DerivedLevel("ugly",   WithinTrial(ugly_stimulus, [color, word])),
        DerivedLevel("pretty", WithinTrial(pretty_stimulus, [color, word]))
    ])


    def unhappy_stimulus(color, word):
        return color[0] == "green" and word[0] == "blue"
    def happy_stimulus(color, word):
        return not unhappy_stimulus(color, word)
    smiley = Factor("smiley", [
        DerivedLevel("happy",   Transition(happy_stimulus, [color, word])),
        DerivedLevel("unhappy", Transition(unhappy_stimulus, [color, word]))
    ])

    constraints = [Exclude(aesthetic["ugly"])]

    design       = [color, word, smiley, aesthetic]
    crossing     = [color, word, aesthetic]


    block       = CrossBlock(design, crossing, constraints, require_complete_crossing=False)
    experiments = synthesize_trials(block, 4, sampling_strategy=RandomGen)

    assert block.crossing_size() == 5
    assert len(experiments) == 4
    for e in experiments:
        assert len(e['color']) == 5
        seen = set()
        for i in range(5):
            key = (e['color'][i], e['motion'][i])
            assert not key in seen
            seen.add(key)
