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
    # this is to prevent testing when sklearn is not installed:
    try:
        from sklearn.neural_network import MLPClassifier
    except ImportError as e:
        assert True
        return
    res = auto_correlation_scores_samples_between(samples)
    assert 'color' in res.keys() and 'word' in res.keys() and 'congruency' in res.keys()


def test_score_auto_correlation():
    # this is to prevent testing when sklearn is not installed:
    try:
        from sklearn.neural_network import MLPClassifier
    except ImportError as e:
        assert True
        return
    res = auto_correlation_scores_samples_between(samples, ['color'])
    assert 'color' in res.keys() and 'word' not in res.keys() and 'congruency' not in res.keys()


