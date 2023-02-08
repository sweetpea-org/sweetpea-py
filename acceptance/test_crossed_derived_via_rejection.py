import operator as op
import pytest

from sweetpea import *

color = Factor("color", ['red', 'green'])
size = Factor("size", ['small', 'med', 'large'])

red = color.get_level('red')
med = size.get_level('med')

match2 = Factor(name="match2", initial_levels=[
    DerivedLevel("up2", Window(lambda a: a[-2] == 'red', [color], 3, 1)),
    DerivedLevel("down2", Window(lambda a: a[-2] != 'red', [color], 3, 1))
])

match1 = Factor(name="match1", initial_levels=[
    DerivedLevel("up2", Window(lambda a: a[-1] == 'red', [color], 2, 1)),
    DerivedLevel("down2", Window(lambda a: a[-1] != 'red', [color], 2, 1))
])

def check_crossed_derived_factor(strategy, design, solutions, constraints=[], repeat_constraints=[]):
    block = CrossBlock(design=design,
                       crossing=design,
                       constraints=constraints)
    repeat = Repeat(block, repeat_constraints)

    experiments = synthesize_trials(block=repeat, samples=1000, sampling_strategy=strategy)
    
    assert len(experiments) == solutions

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_small_crossed_derived_factor(strategy):
    check_crossed_derived_factor(strategy, [color, match2], 4)

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_big_crossed_derived_factor(strategy):
    check_crossed_derived_factor(strategy, [color, match2, match1], 16)

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_crossed_derived_factor_with_minimum_trials(strategy):
    check_crossed_derived_factor(strategy, [color, match2], 108, [MinimumTrials(8)])
    check_crossed_derived_factor(strategy, [color, match2], 16, [], [MinimumTrials(8)])
