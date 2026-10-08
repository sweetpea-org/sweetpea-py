import operator as op
import pytest

from sweetpea import *

color = Factor("color",  ["red", "blue"])
size = Factor("size",  ["big", "small"])
direction = Factor("direction",  ["up", "down", "left", "right"])

red = color.get_level('red')
blue = color.get_level('blue')
up = direction.get_level('up')
down = direction.get_level('down')
right = direction.get_level('right')
left = direction.get_level('left')

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_base_constraints_on_design_factor(strategy):
    block = CrossBlock([color], [color], [MinimumTrials(4), AtMostKInARow(1, color)])
    repet = Repeat(block, [MinimumTrials(8)])
    trials = synthesize_trials(repet, 100, strategy)
    assert len(trials) == 4

    repet = Repeat(block, [MinimumTrials(8), AtMostKInARow(1, color)])
    trials = synthesize_trials(repet, 100, strategy)
    assert len(trials) == 2

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('constraints_and_solutions',
                         # only way this works is red, blue, blue, red; solutions: 4
                         [[[AtMostKInARow(1, (color, red)), AtLeastKInARow(2, (color, blue))], 4],
                          [[AtMostKInARow(1, (color, red))], 12],
                          [[AtLeastKInARow(2, (color, red))], 12],
                          [[ExactlyKInARow(2, (color, red))], 12],
                          [[ExactlyK(2, (color, red))], 24]])
def test_check_constraints_on_crossing_factor(strategy, constraints_and_solutions):
    constraints = constraints_and_solutions[0]
    solutions = constraints_and_solutions[1]

    design       = [color, size]
    crossing     = [color, size]
    block        = CrossBlock(design, crossing, constraints)

    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == solutions

    # Two instances of the block should be independent
    experiments  = synthesize_trials(Repeat(block, [MinimumTrials(2*len(experiments[0]['color']))]),
                                     1000, sampling_strategy=strategy)
    assert len(experiments) == solutions * solutions
    

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
@pytest.mark.parametrize('constraints_and_solutions',
                         [[[ExactlyK(3, up), ExactlyK(1, right)], 96],
                          [[ExactlyK(4, up)], 24],
                          [[ExactlyKInARow(4, up), ExactlyK(4, up)], 24],
                          [[ExactlyKInARow(3, up), ExactlyK(3, up)], 144],
                          [[ExactlyKInARow(1, up),
                            ExactlyK(2,(direction, up)),
                            Exclude(left),
                            ExactlyKInARow(1, down),
                            ExactlyKInARow(1, right)],
                           240]])
def test_check_constraints_on_design_factor(strategy, constraints_and_solutions):
    constraints = constraints_and_solutions[0]
    solutions = constraints_and_solutions[1]

    design       = [color, size, direction]
    crossing     = [color, size]
    block        = CrossBlock(design, crossing, constraints)

    experiments  = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert len(experiments) == solutions


# ~~~~~~~~~~~~ AtLeastKInARow where no run boundary fits ~~~~~~~~~~~~

def _free_color(constraints):
    """`color` is uncrossed, so nothing forces how often a level appears."""
    color = Factor('color', ['red', 'green', 'blue'])
    return color, CrossBlock([color], [], constraints(color) + [MinimumTrials(6)])


def test_at_least_k_filling_the_block_is_all_or_nothing():
    # k equals the trial count, so a run of k is the whole block: red fills it
    # or stays away. Pinning one trial leaves only the filled option.
    color, block = _free_color(lambda c: [AtLeastKInARow(6, (c, 'red')),
                                          Pin(0, (c, 'red'))])
    experiments = synthesize_trials(block, 5, sampling_strategy=IterateGen)
    assert experiments
    for e in experiments:
        assert e['color'] == ['red'] * 6


def test_at_least_k_longer_than_the_block_excludes_the_level():
    # A run of 9 cannot fit in 6 trials, so red cannot appear at all.
    color, block = _free_color(lambda c: [AtLeastKInARow(9, (c, 'red'))])
    experiments = synthesize_trials(block, 5, sampling_strategy=IterateGen)
    assert experiments
    for e in experiments:
        assert 'red' not in e['color']


def test_at_least_k_longer_than_the_block_conflicts_with_a_pin():
    color, block = _free_color(lambda c: [AtLeastKInARow(9, (c, 'red')),
                                          Pin(0, (c, 'red'))])
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen) == []
