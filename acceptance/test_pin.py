import pytest

from sweetpea import *

number = Factor("number", [1.0, 2.0, 3.0])
letter = Factor("letter", ["a", "b", "c"])

@pytest.mark.parametrize('index_and_solutions',
                         [[0, 2],
                          [-1, 2],
                          [-2, 2],
                          [100, 0],
                          [-100, 0]])
@pytest.mark.parametrize('strategy', [IterateSATGen, RandomGen])
def test_pin(index_and_solutions, strategy):
    index = index_and_solutions[0]
    solutions = index_and_solutions[1]
    block = CrossBlock([number], [number], [Pin(index, number[1.0])])
    experiments = synthesize_trials(block, 10, strategy)
    assert len(experiments) == solutions
    for e in experiments:
        trial_no = index if index >= 0 else len(e['number']) + index
        assert e['number'][trial_no] == 1.0

    block = CrossBlock([letter], [letter], [Pin(index, letter["b"])])
    experiments = synthesize_trials(block, 10, strategy)
    assert len(experiments) == solutions
    for e in experiments:
        trial_no = index if index >= 0 else len(e['letter']) + index
        assert e['letter'][trial_no] == "b"

    side = Factor("side", ["left", "right"])
    second_index = index + 3 if index > 0 else index - 3
    block = CrossBlock([letter, side], [letter, side], [Pin(index, (letter, "b")),
                                                        Pin(second_index, (letter, "b"))])
    experiments = synthesize_trials(block, 100, strategy)
    assert len(experiments) == solutions * 24
    for e in experiments:
        trial_no = index if index >= 0 else len(e['letter']) + index
        assert e['letter'][trial_no] == "b"
    
    unity = Factor("unity", [DerivedLevel("one", WithinTrial(lambda n: n == 1.0, [number])),
                             ElseLevel("many")])
    block = CrossBlock([number, unity], [number], [Pin(index, unity["many"])])
    experiments = synthesize_trials(block, 100, strategy)
    assert len(experiments) == solutions * 2
    for e in experiments:
        trial_no = index if index >= 0 else len(e['number']) + index
        assert e['number'][trial_no] != 1.0

    mood = Factor("mood", [DerivedLevel("up", Transition(lambda ns: ns[0] > ns[-1], [number])),
                           DerivedLevel("down", Transition(lambda ns: ns[0] < ns[-1], [number]))])
    t_index = index if index < 0 else index+1
    block = CrossBlock([number, mood], [number], [Pin(t_index, mood["up"])])
    experiments = synthesize_trials(block, 10, strategy)
    for e in experiments:
        trial_no = index if index >= 0 else len(e['number']) + index - 1
        e['number'][trial_no+1] > e['number'][trial_no]

@pytest.mark.parametrize('index_and_solutions',
                         [[0, 4, 12],
                          [-1, 4, 12],
                          [-2, 4, 12],
                          [100, 0, 0],
                          [-100, 0, 0]])
@pytest.mark.parametrize('strategy', [IterateSATGen, RandomGen])
def test_pin_repeats(index_and_solutions, strategy):
    index = index_and_solutions[0]
    solutions = index_and_solutions[1]
    repet_solutions = index_and_solutions[2]
 
    block = CrossBlock([number], [number], [Pin(index, number[1.0])])
    repet = Repeat(block, [MinimumTrials(6)])
    experiments = synthesize_trials(repet, 20, strategy)
    assert len(experiments) == solutions
    for e in experiments:
        trial_no = index if index >= 0 else len(e['number']) + index
        assert e['number'][trial_no] == 1.0
        trial_no = index + 3 if index >= 0 else len(e['number']) - 3 + index
        assert e['number'][trial_no] == 1.0

    block = CrossBlock([number], [number], [])
    repet = Repeat(block, [MinimumTrials(6), Pin(index, number[1.0])])
    experiments = synthesize_trials(repet, 20, strategy)
    assert len(experiments) == repet_solutions
    for e in experiments:
        trial_no = index if index >= 0 else len(e['number']) + index
        assert e['number'][trial_no] == 1.0

        
