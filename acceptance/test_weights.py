import pytest

from sweetpea import (
    Factor, Level, DerivedLevel, ElseLevel,
    MinimumTrials, WithinTrial, Transition,
    CrossBlock,
    synthesize_trials, print_experiments,
    CMSGen, IterateGen, RandomGen
)

def check_consistent_solutions(block, expect):
    r_experiments  = synthesize_trials(block, 1000, RandomGen)
    i_experiments  = synthesize_trials(block, 1000, IterateGen)

    assert len(r_experiments) == expect
    assert len(i_experiments) == expect

    for e in r_experiments:
        assert e in i_experiments
    for e in i_experiments:
        assert e in r_experiments

def test_correct_solutions_with_plain_level_weight():
    color = Factor("color",  [Level("red", 1), "blue"])
    size = Factor("size",  ["big", Level("small", 2)])    

    constraints = []

    design       = [color, size]
    crossing     = [color, size]
    block        = CrossBlock(design, crossing, constraints)

    check_consistent_solutions(block, 180)
    
@pytest.mark.slow
def test_correct_solutions_with_plain_level_weight_and_min_trials():
    color = Factor("color",  [Level("red", 1), "blue"])
    size = Factor("size",  ["big", Level("small", 2)])    

    constraints = [MinimumTrials(7)]

    design       = [color, size]
    crossing     = [color, size]
    block        = CrossBlock(design, crossing, constraints)

    check_consistent_solutions(block, 720)

def test_correct_solutions_with_derived_level_weight():
    color = Factor("color",  ["red", "blue"])
    size = Factor("size",  ["big", "small"])

    look = Factor("look",
                  [DerivedLevel("bold",
                                WithinTrial(lambda c, s: c == "red" and s == "big",
                                            [color, size]),
                                2),
                   ElseLevel("plain")])

    constraints = [MinimumTrials(4)]
    
    design       = [color, size, look]
    crossing     = [look]

    check_consistent_solutions(CrossBlock(design, crossing, []), 9)
    check_consistent_solutions(CrossBlock(design, crossing, constraints), 36)

def test_correct_solutions_with_transition_level_weight():
    color = Factor("color",  ["red", "blue"])
    size = Factor("size",  ["big", "small"])

    look = Factor("look",
                  [DerivedLevel("bolden",
                                Transition(lambda c, s: c[1] == "red" and s[1] == "big",
                                           [color, size]),
                                2),
                   ElseLevel("weaken", 1)])

    constraints = [MinimumTrials(7)]
    
    design       = [color, size, look]
    crossing     = [look]
    
    check_consistent_solutions(CrossBlock(design, crossing, []), 36)
    check_consistent_solutions(CrossBlock(design, crossing, constraints), 324)
