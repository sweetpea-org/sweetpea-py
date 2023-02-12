from sweetpea import *

samples = [
    {
        'color': ['red', 'green', 'red', 'green', 'red', 'green'],
        'word': ['red', 'green', 'red', 'green', 'red', 'red'],
        'congruency': ['con', 'con', 'inc', 'con', 'inc', 'con']
    },
    {
        'color': ['red', 'green', 'red', 'green', 'red', 'green'],
        'word': ['red', 'red', 'green', 'red', 'red', 'green'],
        'congruency': ['con', 'con', 'con', 'inc', 'con', 'con']
    },
    {
        'color': ['green', 'red', 'green', 'red', 'green', 'red'],
        'word': ['green', 'red', 'red', 'red', 'green', 'red'],
        'congruency': ['con', 'inc', 'con', 'con', 'con', 'inc']
    }]


def test_score_auto_correlation_all():
    res = auto_correlation_scores_samples(samples)
    assert 'color' in res.keys() and 'word' in res.keys() and 'congruency' in res.keys()


def test_score_auto_correlation():
    res = auto_correlation_scores_samples(samples, ['color'])
    assert 'color' in res.keys() and 'word' not in res.keys() and 'congruency' not in res.keys()


