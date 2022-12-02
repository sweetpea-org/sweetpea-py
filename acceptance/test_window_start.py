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
