from sweetpea import *
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, window

color = Factor("color", ['red', 'green'])
size = Factor("size", ['real small', 'great big'])

def test_implied_within_trial():
    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="same", window=WithinTrial(predicate=lambda a, b: a[0] == b[0], factors=[color, size])),
        DerivedLevel(name="diff", window=WithinTrial(predicate=lambda a, b: a[0] != b[0], factors=[color, size]))
    ])

    block      = fully_cross_block([color, size, match], crossing=[color, size], constraints=[])
    experiments = synthesize_trials_non_uniform(block=block, samples=4)

    assert len(experiments) == 4
    assert len(experiments[0]["color"]) == 4

    for e in experiments:
        for i in range(0, len(e["color"])):
            if (e["color"][i][0] == e["size"][i][0]):
                assert e["match"][i] == "same"
            else:
                assert e["match"][i] == "diff"

def test_implied_window():
    match = Factor(name="match", initial_levels=[
        DerivedLevel(name="same", window=window(lambda a: a[0] == a[1], [color], 2, 1)),
        DerivedLevel(name="diff", window=window(lambda a: a[0] != a[1], [color], 2, 1))
    ])

    block      = fully_cross_block([color, size, match], crossing=[color, size], constraints=[])
    experiments = synthesize_trials_non_uniform(block=block, samples=4)

    assert len(experiments) == 4
    assert len(experiments[0]["color"]) == 4

    for e in experiments:
        assert e["match"][0] == ""
        for i in range(1, len(e["color"])):
            if (e["color"][i] == e["color"][i-1]):
                assert e["match"][i] == "same"
            else:
                assert e["match"][i] == "diff"
