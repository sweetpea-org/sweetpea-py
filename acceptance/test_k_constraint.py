import operator as op
import pytest

from sweetpea.primitives import factor, derived_level, within_trial
from sweetpea.constraints import minimum_trials, exclude, AtMostKInARow, AtLeastKInARow, ExactlyKInARow, ExactlyK, Exclude
from sweetpea import fully_cross_block, synthesize_trials, UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy

color = factor("color",  ["red", "blue"])
size = factor("size",  ["big", "small"])
direction = factor("direction",  ["up", "down", "left", "right"])

red = color.get_level('red')
blue = color.get_level('blue')
up = direction.get_level('up')
down = direction.get_level('down')
right = direction.get_level('right')
left = direction.get_level('left')

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
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
    block        = fully_cross_block(design, crossing, constraints)

    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)

    assert len(experiments) == solutions

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
@pytest.mark.parametrize('constraints_and_solutions',
                         [[[ExactlyK(3, (direction, up)), ExactlyK(1, (direction, right))], 96],
                          [[ExactlyK(4, (direction, up))], 24],
                          [[ExactlyKInARow(4, (direction, up)), ExactlyK(4, (direction, up))], 24],
                          [[ExactlyKInARow(3, (direction, up)), ExactlyK(3, (direction, up))], 144],
                          [[ExactlyKInARow(1, (direction, up)),
                            ExactlyK(2,(direction, up)),
                            Exclude(direction, left),
                            ExactlyKInARow(1, (direction, down)),
                            ExactlyKInARow(1, (direction, right))],
                           240]])
def test_check_constraints_on_design_factor(strategy, constraints_and_solutions):
    constraints = constraints_and_solutions[0]
    solutions = constraints_and_solutions[1]

    design       = [color, size, direction]
    crossing     = [color, size]
    block        = fully_cross_block(design, crossing, constraints)

    experiments  = synthesize_trials(block, 500, sampling_strategy=strategy)

    assert len(experiments) == solutions
