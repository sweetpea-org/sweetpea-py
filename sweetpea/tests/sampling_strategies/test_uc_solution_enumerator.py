import operator as op
import pytest

from sweetpea import CrossBlock
from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial
from sweetpea._internal.constraint import Reify
from sweetpea._internal.sampling_strategy.random import UCSolutionEnumerator

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

crossing = [color, text]
design = [color, text]
block = CrossBlock(design, crossing, [])


def test_generate_crossing_instances():
    enumerator = UCSolutionEnumerator(block)
    crossing_instances = enumerator._UCSolutionEnumerator__generate_crossing_instances()
    simplified_names = []
    for d in crossing_instances:
        d_simple = {}
        for (f, l) in d.items():
            d_simple[f.name] = l.name
        simplified_names.append(d_simple)

    assert simplified_names == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


def test_generate_source_combinations():
    block = CrossBlock([color, text, congruency], [congruency], list(map(Reify, design)))
    enumerator = UCSolutionEnumerator(block)
    crossing_source_combos = enumerator._UCSolutionEnumerator__generate_source_combinations()
    simplified_names = []
    for d in crossing_source_combos:
        d_simple = {}
        for (f, l) in d.items():
            d_simple[f.name] = l.name
        simplified_names.append(d_simple)

    assert simplified_names == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


@pytest.mark.parametrize('sequence_number, expected_solution', [
[0, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'red', 'blue']}],
[1, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'red', 'blue']}],
[2, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue']}],
[3, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'red', 'blue', 'red']}],
[4, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue']}],
[5, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'red', 'red', 'blue']}],
[6, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'blue', 'red', 'blue']}],
[7, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red']}],
[8, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'blue', 'blue', 'red']}],
[9, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red']}],
[10, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'red', 'blue']}],
[11, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'red', 'blue']}],
[12, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'blue', 'red']}],
[13, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'blue', 'red']}],
[14, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue']}],
[15, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'red', 'red', 'blue']}],
[16, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue']}],
[17, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'red', 'blue', 'red']}],
[18, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'blue', 'blue', 'red']}],
[19, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red']}],
[20, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'blue', 'red', 'blue']}],
[21, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red']}],
[22, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'blue', 'red']}],
[23, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'blue', 'red']}]
])
def test_generate_sample_basic_stroop(sequence_number, expected_solution):
    block = CrossBlock([color, text, congruency],
                       [color, text],
                       [Reify(congruency)]) # even so, will not show up in enumerator output
    enumerator = UCSolutionEnumerator(block)
    assert enumerator.factors_and_levels_to_names(enumerator.generate_sample(sequence_number)) == expected_solution

@pytest.mark.parametrize('sequence_number, expected_solution', [
[0, {'color': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent'], 'text': ['red', 'blue', 'blue', 'red']}],
[1, {'color': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent'], 'text': ['blue', 'red', 'blue', 'red']}],
[2, {'color': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent'], 'text': ['blue', 'red', 'blue', 'red']}],
[3, {'color': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent'], 'text': ['red', 'red', 'blue', 'blue']}],
[4, {'color': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent'], 'text': ['red', 'blue', 'blue', 'red']}],
[5, {'color': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent'], 'text': ['blue', 'blue', 'red', 'red']}],
[6, {'color': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent'], 'text': ['blue', 'blue', 'red', 'red']}],
[7, {'color': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent'], 'text': ['red', 'blue', 'red', 'blue']}],
[8, {'color': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent'], 'text': ['red', 'red', 'blue', 'blue']}],
[9, {'color': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent'], 'text': ['blue', 'red', 'red', 'blue']}],
[10, {'color': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent'], 'text': ['blue', 'red', 'red', 'blue']}],
[11, {'color': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent'], 'text': ['red', 'blue', 'red', 'blue']}],
[12, {'color': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent'], 'text': ['red', 'blue', 'red', 'blue']}],
[13, {'color': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent'], 'text': ['blue', 'red', 'red', 'blue']}],
[14, {'color': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent'], 'text': ['blue', 'red', 'red', 'blue']}],
[15, {'color': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent'], 'text': ['red', 'red', 'blue', 'blue']}],
[16, {'color': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent'], 'text': ['red', 'blue', 'red', 'blue']}],
[17, {'color': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent'], 'text': ['blue', 'blue', 'red', 'red']}],
[18, {'color': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent'], 'text': ['blue', 'blue', 'red', 'red']}],
[19, {'color': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent'], 'text': ['red', 'blue', 'blue', 'red']}],
[20, {'color': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent'], 'text': ['red', 'red', 'blue', 'blue']}],
[21, {'color': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent'], 'text': ['blue', 'red', 'blue', 'red']}],
[22, {'color': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent'], 'text': ['blue', 'red', 'blue', 'red']}],
[23, {'color': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent'], 'text': ['red', 'blue', 'blue', 'red']}]
])
def test_generate_sample_basic_stroop_variation(sequence_number, expected_solution):
    block = CrossBlock([color, text, congruency],
                       [color, congruency],
                       [])
    enumerator = UCSolutionEnumerator(block)
    assert enumerator.factors_and_levels_to_names(enumerator.generate_sample(sequence_number)) == expected_solution

# ---------------------------------------------------------------
# |   Trial |  color   |      text      |      congruency       |
# |       # | red blue | red blue green | congruent incongruent |
# ---------------------------------------------------------------
# |       1 |  1   2   |  3   4     5   |     6          7      |
# |       2 |  8   9   | 10   11   12   |    13         14      |
# |       3 | 15   16  | 17   18   19   |    20         21      |
# |       4 | 22   23  | 24   25   26   |    27         28      |
# ---------------------------------------------------------------
@pytest.mark.parametrize('sequence_number, expected_solution', [
[0, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[1, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[41, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['green', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}]
])
def test_generate_sample_basic_stroop_uneven_colors(sequence_number, expected_solution):
    text = Factor("text", ["red", "blue", "green"])
    congruency = Factor("congruency", [
        DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
        DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
    ])

    block = CrossBlock([color, text, congruency],
                       [color, congruency],
                       [])
    enumerator = UCSolutionEnumerator(block)
    assert enumerator.factors_and_levels_to_names(enumerator.generate_sample(sequence_number)) == expected_solution
