from sweetpea import *

def test_window_with_early_start():
    color = Factor("color", ["red", "green", "blue"])
    flavor = Factor("flavor", ["mild", "spicy"])
    redness = Factor("redness",
                     [DerivedLevel("ruddy", Window(lambda c: (c[-1] != "red" and c[0] == "red"), [color], 2, 1, 0)),
                      ElseLevel("plain")])

    block = CrossBlock([color, flavor, redness], [flavor, redness], [])

    i_experiments = synthesize_trials(block, 100, IterateSATGen)
    r_experiments = synthesize_trials(block, 100, RandomGen)

    assert len(i_experiments) == 64
    assert len(r_experiments) == 64

    distinct = set()
    for i in i_experiments:
        distinct.add(tuple([(k, tuple(i[k])) for k in ["color", "flavor", "redness"]]))
    for i in r_experiments:
        assert tuple([(k, tuple(i[k])) for k in ["color", "flavor", "redness"]]) in distinct
    assert len(distinct) == 64

    color = Factor("color", ["red"])

def test_window_with_late_start():
    color = Factor("color", ["red"])
    redness = Factor("redness",
                     [DerivedLevel("ruddy", Window(lambda c: c == "red", [color], 1, 1, 10))])

    block = CrossBlock([color, redness], [color, redness], [])

    i_experiments = synthesize_trials(block, 20, IterateSATGen)
    r_experiments = synthesize_trials(block, 20, RandomGen)
    assert len(i_experiments) == 1
    assert len(r_experiments) == 1

def test_window_early_start_regression():
    letter = Factor('letter', ['b', 'f', 'm', 'q', 'k', 'x', 'r', 'h'])

    def is_target(letters):
        return letters[-1] == letters[0]

    def is_not_target(letters):
        return not is_target(letters)

    one_t = DerivedLevel(1, Window(is_target, [letter], width=2, stride=1, start=0), 1)
    two_t = DerivedLevel(2, Window(is_not_target, [letter], width=2, stride=1, start=0), 1)

    target = Factor('target', [one_t, two_t])

    block = Repeat(CrossBlock(design=[letter, target],
                              constraints=[],
                              crossing=[letter, target]),
                   constraints=[MinimumTrials(48)])

    experiments = synthesize_trials(block, 1)

    # Only possibile solutions alternate bewteen 1 and 2
    for i, v in enumerate(experiments[0]['target']):
        assert v == ((i+1) % 2) + 1

def test_window_early_start_regression2():
    letter = Factor('letter', ['b', 'f'])

    def is_target(letters):
        return letters[-2] == letters[0]

    def is_not_target(letters):
        return not is_target(letters)

    one_t = DerivedLevel('1', Window(is_target, [letter], width=3, stride=1, start=0), 1)
    two_t = DerivedLevel('2', Window(is_not_target, [letter], width=3, stride=1, start=0), 2)

    target = Factor('target', [one_t, two_t])
    
    block = CrossBlock(design=[letter, target],
                       constraints=[],
                       crossing=[letter, target])

    i_experiments = synthesize_trials(block, 10, IterateSATGen)
    r_experiments = synthesize_trials(block, 10, RandomGen)
    assert len(i_experiments) == 8
    assert len(r_experiments) == 8
