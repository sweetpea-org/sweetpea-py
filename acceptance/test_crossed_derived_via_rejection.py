import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, DerivationWindow
from sweetpea.constraints import AtMostKInARow, AtLeastKInARow, ExactlyKInARow, ExactlyK, Exclude
from sweetpea import fully_cross_block, synthesize_trials, UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy

color = Factor("color", ['red', 'green'])
size = Factor("size", ['small', 'med', 'large'])

red = color.get_level('red')
med = size.get_level('med')

match2 = Factor(name="match2", initial_levels=[
    DerivedLevel("up2", DerivationWindow(lambda a: a[0] == 'red', [color], 3, 1)),
    DerivedLevel("down2", DerivationWindow(lambda a: a[0] != 'red', [color], 3, 1))
])

match1 = Factor(name="match1", initial_levels=[
    DerivedLevel("up2", DerivationWindow(lambda a: a[0] == 'red', [color], 2, 1)),
    DerivedLevel("down2", DerivationWindow(lambda a: a[0] != 'red', [color], 2, 1))
])

def check_crossed_derived_factor(strategy, design, solutions):
    block = fully_cross_block(design=design,
                              crossing=design,
                              constraints=[])

    experiments = synthesize_trials(block=block, samples=100, sampling_strategy=strategy)
    
    assert len(experiments) == solutions

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_check_small_crossed_derived_factor(strategy):
    check_crossed_derived_factor(strategy, [color, match2], 4)

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
@pytest.mark.slow
def test_check_big_crossed_derived_factor(strategy):
    check_crossed_derived_factor(strategy, [color, match2, match1], 16)
