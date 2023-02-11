from sweetpea import *

color = Factor('color', ['red', 'green'])
word = Factor('word', ['red', 'green'])

congruency = Factor('congruency', [
    DerivedLevel('congruent', WithinTrial(lambda c, w: c == w, [color, word])),
    DerivedLevel('incongruent', WithinTrial(lambda c, w: c != w, [color, word]))
])

color_transition = Factor('color_transition', [
    DerivedLevel('repeat', Transition(lambda c: c[-1] == c[0], [color])),
    DerivedLevel('switch', Transition(lambda c: c[-1] != c[0], [color]))
])

color_window = Factor('color_window', [
    DerivedLevel('2-back', Window(lambda c: c[-2] == c[0], [color], 3)),
    DerivedLevel('not-2-back', Window(lambda c: c[-2] != c[0], [color], 3, 1))
])


def test_mismatch_derived_factor_within():
    design = [color, word, congruency]
    crossing = [congruency]
    constraints = []
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green'],
                       'word': ['green', 'green'],
                       'congruency': ['congruent', 'incongruent']}

    sample_no_mismatch = {'color': ['red', 'green'],
                          'word': ['green', 'green'],
                          'congruency': ['incongruent', 'congruent']}

    assert sample_mismatch_experiment(block, sample_mismatch)['factors'] == ['congruency'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_derived_factor_transition():
    design = [color, color_transition]
    crossing = [color_transition]
    constraints = []
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'green'],
                       'color_transition': ['', 'repeat', 'switch']}

    sample_no_mismatch = {'color': ['red', 'green', 'green'],
                          'color_transition': ['', 'switch', 'repeat']}

    assert sample_mismatch_experiment(block, sample_mismatch)['factors'] == ['color_transition'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_derived_factor_window():
    design = [color, color_window]
    crossing = [color_window]
    constraints = []
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'green', 'green'],
                       'color_window': ['', '', '2-back', 'not-2-back']}

    sample_no_mismatch = {'color': ['red', 'green', 'green', 'green'],
                          'color_window': ['', '', 'not-2-back', '2-back']}

    assert sample_mismatch_experiment(block, sample_mismatch)['factors'] == ['color_window'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_constraint_at_most_k_in_a_row():
    design = [color]
    crossing = [color]
    constraints = [AtMostKInARow(1, color), MinimumTrials(4)]
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'red', 'green', 'green']}
    sample_no_mismatch = {'color': ['red', 'green', 'red', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['constraints'] == ['AtMostKInARow, 1, Level<red>',
                                                                                 'AtMostKInARow, 1, Level<green>'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_constraint_at_least_k_in_a_row():
    design = [color]
    crossing = [color]
    constraints = [AtLeastKInARow(2, color), MinimumTrials(4)]
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'red', 'green']}
    sample_no_mismatch = {'color': ['red', 'red', 'green', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['constraints'] == ['AtLeastKInARow, 2, Level<red>',
                                                                                 'AtLeastKInARow, 2, Level<green>'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_constraint_exactly_k():
    design = [color, word]
    crossing = [color]
    constraints = [ExactlyK(2, word), MinimumTrials(4)]
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'red', 'red', 'green']}
    sample_no_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'green', 'red', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['constraints'] == ['ExactlyK, 2, Level<red>',
                                                                                 'ExactlyK, 2, Level<green>'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_constraint_exactly_k_in_a_row():
    design = [color, word]
    crossing = [color]
    constraints = [ExactlyKInARow(2, word), MinimumTrials(4)]
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'green', 'red', 'green']}
    sample_no_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'red', 'green', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['constraints'] == ['ExactlyKInARow, 2, Level<red>',
                                                                                 'ExactlyKInARow, 2, Level<green>'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}


def test_mismatch_constraint_exclude():
    design = [color, word]
    crossing = [color]
    constraints = [Exclude((word, 'red')), MinimumTrials(4)]
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'green', 'red', 'green']}
    sample_no_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['green', 'green', 'green', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['constraints'] == ['Exclude, Level<red>'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}

def test_mismatch_crossing():
    design = [color, word]
    crossing = [color, word]
    constraints = []
    block = CrossBlock(design, crossing, constraints)

    sample_mismatch = {'color': ['red', 'green', 'red', 'green'], 'word': ['red', 'green', 'red', 'green']}
    sample_no_mismatch = {'color': ['red', 'red', 'green', 'green'], 'word': ['red', 'green', 'red', 'green']}

    assert sample_mismatch_experiment(block, sample_mismatch)['crossings'] == ['[Factor<color>, Factor<word>]'] and \
           sample_mismatch_experiment(block, sample_no_mismatch) == {}
