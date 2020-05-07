import operator as op
import pytest

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, get_external_level_name
from sweetpea.sampling_strategies.uniform_combinatoric import UCSolutionEnumerator
from sweetpea.tests.test_utils import get_level_from_name

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

crossing = [color, text]
design = [color, text]
block = fully_cross_block(design, crossing, [])


def test_generate_crossing_instances():
    enumerator = UCSolutionEnumerator(block)
    crossing_instances = enumerator._UCSolutionEnumerator__generate_crossing_instances()
    simplified_names = []
    for d in crossing_instances:
        d_simple = {}
        for (f, l) in d.items():
            d_simple[f.factor_name] = get_external_level_name(l)
        simplified_names.append(d_simple)

    assert simplified_names == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


def test_generate_source_combinations():
    block = fully_cross_block(design, [congruency], [])
    enumerator = UCSolutionEnumerator(block)
    crossing_source_combos = enumerator._UCSolutionEnumerator__generate_source_combinations()
    simplified_names = []
    for d in crossing_source_combos:
        d_simple = {}
        for (f, l) in d.items():
            d_simple[f.factor_name] = get_external_level_name(l)
        simplified_names.append(d_simple)

    assert simplified_names == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


@pytest.mark.parametrize('sequence_number, expected_solution', [
[0, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[1, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[2, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[3, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[4, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[5, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[6, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[7, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[8, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[9, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[10, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[11, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[12, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[13, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[14, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[15, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[16, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[17, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[18, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[19, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[20, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[21, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[22, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[23, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}]
])
def test_generate_sample_basic_stroop(sequence_number, expected_solution):
    block = fully_cross_block([color, text, congruency],
                              [color, text],
                              [])
    enumerator = UCSolutionEnumerator(block)
    assert enumerator.generate_sample(sequence_number) == expected_solution


@pytest.mark.parametrize('sequence_number, expected_solution', [
[0, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[1, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[2, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[3, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[4, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[5, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[6, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[7, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'blue', 'red', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[8, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[9, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'congruent', 'incongruent', 'incongruent']}],
[10, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[11, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[12, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[13, {'color': ['red', 'red', 'blue', 'blue'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[14, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['blue', 'red', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[15, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['blue', 'red', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[16, {'color': ['red', 'blue', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'incongruent', 'congruent']}],
[17, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}],
[18, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[19, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'incongruent', 'congruent', 'congruent']}],
[20, {'color': ['red', 'blue', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['congruent', 'incongruent', 'congruent', 'incongruent']}],
[21, {'color': ['blue', 'red', 'blue', 'red'], 'text': ['red', 'red', 'blue', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[22, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'red', 'blue'], 'congruency': ['incongruent', 'congruent', 'congruent', 'incongruent']}],
[23, {'color': ['blue', 'blue', 'red', 'red'], 'text': ['red', 'blue', 'blue', 'red'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}]
])
def test_generate_sample_basic_stroop_variation(sequence_number, expected_solution):
    block = fully_cross_block([color, text, congruency],
                              [color, congruency],
                              [])
    enumerator = UCSolutionEnumerator(block)
    print (enumerator.generate_sample(sequence_number))
    assert enumerator.generate_sample(sequence_number) == expected_solution


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
[41, {'color': ['blue', 'red', 'red', 'blue'], 'text': ['red', 'red', 'green', 'blue'], 'congruency': ['incongruent', 'congruent', 'incongruent', 'congruent']}]
])
def test_generate_sample_basic_stroop_uneven_colors(sequence_number, expected_solution):
    text = Factor("text", ["red", "blue", "green"])
    congruency = Factor("congruency", [
        DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
        DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
    ])

    block = fully_cross_block([color, text, congruency],
                              [color, congruency],
                              [])
    enumerator = UCSolutionEnumerator(block)
    print(enumerator.generate_sample(sequence_number))
    assert enumerator.generate_sample(sequence_number) == expected_solution
