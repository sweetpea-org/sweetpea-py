from sweetpea import  *

def test_simple_sequential():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2", "c3"])

    outer = CrossBlock([A, B, C], [A, B], [Sequential(C), MinimumTrials(16)])
    
    exps = synthesize_trials(outer, 32, sampling_strategy=IterateGen)
    assert len(exps) == 32
    for e in exps:
        for i in range(0, len(e["C"])):
            assert e["C"][i] == ["c1", "c2", "c3"][i % 3]
