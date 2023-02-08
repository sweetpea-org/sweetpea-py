import pytest

from sweetpea import (
    Factor, Level, DerivedLevel, ElseLevel,
    MinimumTrials, WithinTrial, Transition,
    CrossBlock, Repeat,
    synthesize_trials, print_experiments,
    CMSGen, IterateSATGen, RandomGen
)

def check_consistent_solutions(block, expect):
    r_experiments  = synthesize_trials(block, 1000, RandomGen)
    i_experiments  = synthesize_trials(block, 1000, IterateSATGen)

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

def test_correct_solutions_with_plain_level_weight_and_min_trials():
    color = Factor("color",  [Level("red", 1), "blue"])
    size = Factor("size",  ["big", Level("small", 2)])    

    constraints = [MinimumTrials(7)]

    design       = [color, size]
    crossing     = [color, size]
    block        = Repeat(CrossBlock(design, crossing, []),
                          constraints)

    check_consistent_solutions(block, 720)

@pytest.mark.slow
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
    check_consistent_solutions(Repeat(CrossBlock(design, crossing, [], constraints)), 36)

def test_correct_solutions_with_transition_level_weight():
    color = Factor("color",  ["red", "blue"])
    size = Factor("size",  ["big", "small"])

    look = Factor("look",
                  [DerivedLevel("bolden",
                                Transition(lambda c, s: c[0] == "red" and s[0] == "big",
                                           [color, size]),
                                2),
                   ElseLevel("weaken", 1)])

    constraints = [MinimumTrials(7)]
    
    design       = [color, size, look]
    crossing     = [look]
    
    check_consistent_solutions(CrossBlock(design, crossing, []), 36)
    check_consistent_solutions(Repeat(CrossBlock(design, crossing, []), constraints), 324)

def test_uncrossed_level_weight():
    color = Factor("color",  ["red", "blue"])
    size = Factor("size",  ["big", Level("small", 2)])

    design       = [color, size]
    crossing     = [color]
    block        = CrossBlock(design, crossing, [])

    check_consistent_solutions(CrossBlock(design, crossing, []), 18)
    check_consistent_solutions(Repeat(CrossBlock(design, crossing, []), [MinimumTrials(3)]), 108)
    
    experiments  = synthesize_trials(CrossBlock(design, crossing, []), 1000, RandomGen)
    totals = {}
    totals['big'] = 0
    totals['small'] = 0
    for e in experiments:
        for l in e['size']:
            totals[l] += 1

    assert totals['small'] == totals['big'] * 2
    assert set(experiments[0].keys()) == set(['color', 'size'])

def test_two_uncrossed_level_weight():
    same = Factor("same", "one")
    color = Factor("color",  ["red", Level("blue", 4)])
    size = Factor("size",  ["big", Level("medium", 2), Level("small", 3)])

    design       = [same, color, size]
    crossing     = [same]
    block        = CrossBlock(design, crossing, [])

    experiments  = synthesize_trials(CrossBlock(design, crossing, []), 1000, RandomGen)
    assert len(experiments) == 1000

    assert set(experiments[0].keys()) == set(['color', 'size', 'same'])

    totals = {}
    totals['red'] = 0
    totals['blue'] = 0
    totals['big'] = 0
    totals['medium'] = 0
    totals['small'] = 0
    for e in experiments:
        for l in e['size']:
            totals[l] += 1
        for l in e['color']:
            totals[l] += 1

    # These counts can fail, but with very low probability

    assert totals['small'] < totals['big'] * 4
    assert totals['small'] > totals['big'] * 2
    
    assert totals['medium'] < totals['big'] * 3
    assert totals['medium'] > totals['big'] * 1
    
    assert totals['blue'] < totals['red'] * 5
    assert totals['blue'] > totals['red'] * 3
