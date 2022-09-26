import pytest

from sweetpea.primitives import factor, derived_level, within_trial, DerivedLevel, DerivedFactor
from sweetpea.constraints import minimum_trials, exclude
from sweetpea import fully_cross_block, synthesize_trials, \
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
    experiments  = synthesize_trials(block, 1, sampling_strategy=UniformCombinatoricSamplingStrategy)

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_check_max_solutions(strategy):
    color      = factor("color",  ["red", "green", "blue"])
    design       = [color]
    crossing     = [color]

    block        = fully_cross_block(design, crossing, [minimum_trials(3)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 6

    block        = fully_cross_block(design, crossing, [minimum_trials(4)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 18

    block        = fully_cross_block(design, crossing, [minimum_trials(5)],
                                     require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 36

@pytest.mark.parametrize('strategy', [UniformCombinatoricSamplingStrategy, NonUniformSamplingStrategy])
def test_check_max_solutions_derived_factor(strategy):
    color = factor("color", ['red', 'green'])
    size = factor("size", ['small', 'med', 'large'])

    match = DerivedFactor(name="match", initial_levels=[
        DerivedLevel(name="high", window=within_trial(lambda a, b: b != 'large', [color, size])),
        DerivedLevel(name="low", window=within_trial(lambda a, b: b == 'large', [color, size]))
    ])

    block      = fully_cross_block(design=[color, size, match], crossing=[color, match], constraints=[])
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 96
