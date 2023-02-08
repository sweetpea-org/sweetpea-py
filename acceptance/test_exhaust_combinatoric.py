import pytest

from sweetpea import *

@pytest.mark.parametrize('num_trials', [1, 2, 3, 4, 5, 6, 7, 8, 100, 1000])
def test_ok_to_ask_for_more_trials_than_solutions(num_trials):
    color      = Factor("color",  ["red", "green"])
    design       = [color]
    crossing     = [color]
    trial_constraint = MinimumTrials(num_trials)
    constraints = [trial_constraint]
    block        = Repeat(CrossBlock(design, crossing, [],
                                     require_complete_crossing=False),
                          constraints)
    experiments  = synthesize_trials(block, 1, sampling_strategy=RandomGen)

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_max_solutions(strategy):
    color      = Factor("color",  ["red", "green", "blue"])
    design       = [color]
    crossing     = [color]

    block        = CrossBlock(design, crossing, [MinimumTrials(3)],
                              require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 6

    block        = Repeat(CrossBlock(design, crossing, [],
                                     require_complete_crossing=False),
                          [MinimumTrials(3)])
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 6

    block        = CrossBlock(design, crossing, [MinimumTrials(4)],
                              require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 54

    block        = Repeat(CrossBlock(design, crossing, [],
                                     require_complete_crossing=False),
                          [MinimumTrials(4)])
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 18

    block        = CrossBlock(design, crossing, [MinimumTrials(5)],
                              require_complete_crossing=False)
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 90

    block        = Repeat(CrossBlock(design, crossing, [],
                                     require_complete_crossing=False),
                          [MinimumTrials(5)])
    experiments  = synthesize_trials(block, 100, sampling_strategy=strategy)
    assert len(experiments) == 36

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
def test_check_max_solutions_derived_factor(strategy):
    color = Factor("color", ['red', 'green'])
    size = Factor("size", ['small', 'med', 'large'])

    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="high", window=WithinTrial(lambda a, b: b != 'large', [color, size])),
        DerivedLevel(name="low", window=WithinTrial(lambda a, b: b == 'large', [color, size]))
    ])

    block      = CrossBlock(design=[color, size, match], crossing=[color, match], constraints=[])
    experiments = synthesize_trials(block=block, samples=200, sampling_strategy=strategy)

    assert len(experiments) == 96
