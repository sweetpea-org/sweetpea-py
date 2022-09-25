import pytest

from sweetpea.primitives import factor, derived_level, within_trial
from sweetpea.constraints import minimum_trials, exclude
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, \
    print_experiments, tabulate_experiments, experiment_to_csv, \
    UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy

@pytest.mark.parametrize('num_trials', [1, 2, 3, 4, 5, 6, 7, 8, 100, 1000])
def test_ok_to_ask_for_more_trials_than_solutions(num_trials):
    color      = factor("color",  ["red", "green"])
    design       = [color]
    crossing     = [color]
    trial_constraint = minimum_trials(num_trials)
    constraints = [trial_constraint]
    block        = fully_cross_block(design, crossing, constraints,
                                     require_complete_crossing=False)
    experiments  = synthesize_trials_non_uniform(block, 1)

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_ok_to_ask_for_more_trials_than_solutions(strategy):
    color      = factor("color",  ["red", "green", "blue"])
    design       = [color]
    crossing     = [color]

    block        = fully_cross_block(design, crossing, [minimum_trials(3)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials_non_uniform(block, 100)
    assert len(experiments) == 6

    block        = fully_cross_block(design, crossing, [minimum_trials(4)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials_non_uniform(block, 100)
    assert len(experiments) == 18

    block        = fully_cross_block(design, crossing, [minimum_trials(5)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials_non_uniform(block, 100)
    assert len(experiments) == 36
