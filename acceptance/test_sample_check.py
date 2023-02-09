import pytest

from sweetpea import *

number = Factor("number", [1.0, 2.0, 3.0])
number2 = Factor("number", [Level(1.0, weight=2), 2.0, 3.0])
color = Factor("color", ["red", "green", "blue"])

def check_mutually_exclusive(ex1, ex2, strategy):
    trials1 = synthesize_trials(ex1, 10, strategy)
    trials2 = synthesize_trials(ex2, 10, strategy)

    assert len(trials1) > 0
    assert len(trials2) > 0

    for trials in trials1:
        assert sample_mismatch_experiment(ex2, trials)
    for trials in trials2:
        assert sample_mismatch_experiment(ex1, trials)

@pytest.mark.parametrize('strategy', [IterateSATGen, RandomGen])
def test_mutually_exclusive_experiments(strategy):
    # Try pairs of experiments where a solution to one is
    # never a solution to the other

    check_mutually_exclusive(CrossBlock([number], [number], []),
                             CrossBlock([number2], [number2], []),
                             strategy)

    check_mutually_exclusive(CrossBlock([number], [number], [Pin(1, number[1.0])]),
                             CrossBlock([number], [number], [Pin(1, number[2.0])]),
                             strategy)

    check_mutually_exclusive(CrossBlock([number], [number], [Pin(1, number[1.0])]),
                             CrossBlock([number], [number], [Pin(-1, number[1.0])]),
                             strategy)

    check_mutually_exclusive(CrossBlock([number], [number], [Exclude(number[2.0])], False),
                             CrossBlock([number], [number], []),
                             strategy)

    check_mutually_exclusive(CrossBlock([number2], [number2], [AtMostKInARow(1, number2[1.0])]),
                             CrossBlock([number2], [number2], [AtLeastKInARow(2, number2[1.0])]),
                             strategy)

    check_mutually_exclusive(CrossBlock([number, color], [number, color], [AtMostKInARow(1, number[1.0])]),
                             CrossBlock([number, color], [number, color], [AtLeastKInARow(2, number[1.0])]),
                             strategy)

    check_mutually_exclusive(CrossBlock([number, color], [number, color], [MinimumTrials(18)]),
                             CrossBlock([number, color], [number, color], []),
                             strategy)

def test_mutually_exclusive_experiments_SAT():
    check_mutually_exclusive(CrossBlock([number, color], [number, color], [MinimumTrials(18),
                                                                           # implies that all "red"s are together,
                                                                           # would have to be in the middle to
                                                                           # satisfy repeat construction
                                                                           AtLeastKInARow(4, color["red"]),
                                                                           # ditto (so can't both happen)
                                                                           AtLeastKInARow(4, number[2.0])]),
                             Repeat(CrossBlock([number, color], [number, color], []),
                                    [MinimumTrials(18)]),
                             IterateSATGen)
