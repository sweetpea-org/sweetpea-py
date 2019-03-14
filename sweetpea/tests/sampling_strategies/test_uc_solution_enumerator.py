import operator as op
import pytest

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.sampling_strategies.uniform_combinatoric import UCSolutionEnumerator


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

    assert enumerator._UCSolutionEnumerator__generate_crossing_instances() == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


def test_generate_source_combinations():
    block = fully_cross_block(design, [congruency], [])
    enumerator = UCSolutionEnumerator(block)

    assert enumerator._UCSolutionEnumerator__generate_source_combinations() == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


@pytest.mark.parametrize('sequence_number, expected_solution', [
    [0,  [1, 3, 5, 7, 10, 12, 14, 15, 18, 20, 22, 23]],
    [1,  [1, 4, 6, 7, 9,  11, 14, 15, 18, 20, 22, 23]],
    [2,  [1, 4, 6, 8, 9,  12, 13, 15, 17, 20, 22, 23]],
    [3,  [1, 4, 6, 8, 9,  12, 14, 16, 17, 19, 21, 23]],
    [4,  [1, 3, 5, 8, 9,  12, 13, 16, 18, 20, 22, 23]],
    [5,  [2, 3, 6, 7, 9,  11, 13, 16, 18, 20, 22, 23]],
    [6,  [2, 3, 6, 7, 10, 12, 13, 15, 17, 20, 22, 23]],
    [7,  [2, 3, 6, 7, 10, 12, 14, 16, 17, 19, 21, 23]],
    [8,  [1, 3, 5, 8, 9,  12, 14, 16, 17, 19, 22, 24]],
    [9,  [2, 3, 6, 7, 9,  11, 14, 16, 17, 19, 22, 24]],
    [10, [2, 3, 6, 8, 10, 11, 13, 15, 17, 19, 22, 24]],
    [11, [2, 3, 6, 8, 10, 11, 13, 16, 18, 19, 21, 23]],
    [12, [1, 3, 5, 7, 10, 12, 14, 16, 17, 20, 21, 24]],
    [13, [1, 4, 6, 7, 9,  11, 14, 16, 17, 20, 21, 24]],
    [14, [1, 4, 6, 8, 10, 11, 13, 15, 17, 20, 21, 24]],
    [15, [1, 4, 6, 8, 10, 11, 14, 15, 18, 19, 21, 23]],
    [16, [1, 3, 5, 8, 10, 11, 13, 16, 18, 20, 21, 24]],
    [17, [2, 4, 5, 7, 9,  11, 13, 16, 18, 20, 21, 24]],
    [18, [2, 4, 5, 7, 10, 12, 13, 15, 17, 20, 21, 24]],
    [19, [2, 4, 5, 7, 10, 12, 14, 15, 18, 19, 21, 23]],
    [20, [1, 3, 5, 8, 10, 11, 14, 15, 18, 19, 22, 24]],
    [21, [2, 4, 5, 7, 9,  11, 14, 15, 18, 19, 22, 24]],
    [22, [2, 4, 5, 8, 9,  12, 13, 15, 17, 19, 22, 24]],
    [23, [2, 4, 5, 8, 9,  12, 13, 16, 18, 19, 21, 23]]
])
def test_generate_sample_basic_stroop(sequence_number, expected_solution):
    block = fully_cross_block([color, text, congruency],
                              [color, text],
                              [])
    enumerator = UCSolutionEnumerator(block)
    assert enumerator.generate_sample(sequence_number) == expected_solution


@pytest.mark.parametrize('sequence_number, expected_solution', [
    [0,  [1, 3, 5, 7, 10, 12, 14, 16, 17, 20, 21, 24]],
    [1,  [1, 4, 6, 7, 9,  11, 14, 16, 17, 20, 21, 24]],
    [2,  [1, 4, 6, 8, 10, 11, 13, 15, 17, 20, 21, 24]],
    [3,  [1, 4, 6, 8, 10, 11, 14, 15, 18, 19, 21, 23]],
    [4,  [1, 3, 5, 8, 10, 11, 13, 16, 18, 20, 21, 24]],
    [5,  [2, 4, 5, 7, 9,  11, 13, 16, 18, 20, 21, 24]],
    [6,  [2, 4, 5, 7, 10, 12, 13, 15, 17, 20, 21, 24]],
    [7,  [2, 4, 5, 7, 10, 12, 14, 15, 18, 19, 21, 23]],
    [8,  [1, 3, 5, 8, 10, 11, 14, 15, 18, 19, 22, 24]],
    [9,  [2, 4, 5, 7, 9,  11, 14, 15, 18, 19, 22, 24]],
    [10, [2, 4, 5, 8, 9,  12, 13, 15, 17, 19, 22, 24]],
    [11, [2, 4, 5, 8, 9,  12, 13, 16, 18, 19, 21, 23]],
    [12, [1, 3, 5, 7, 10, 12, 14, 15, 18, 20, 22, 23]],
    [13, [1, 4, 6, 7, 9,  11, 14, 15, 18, 20, 22, 23]],
    [14, [1, 4, 6, 8, 9,  12, 13, 15, 17, 20, 22, 23]],
    [15, [1, 4, 6, 8, 9,  12, 14, 16, 17, 19, 21, 23]],
    [16, [1, 3, 5, 8, 9,  12, 13, 16, 18, 20, 22, 23]],
    [17, [2, 3, 6, 7, 9,  11, 13, 16, 18, 20, 22, 23]],
    [18, [2, 3, 6, 7, 10, 12, 13, 15, 17, 20, 22, 23]],
    [19, [2, 3, 6, 7, 10, 12, 14, 16, 17, 19, 21, 23]],
    [20, [1, 3, 5, 8, 9,  12, 14, 16, 17, 19, 22, 24]],
    [21, [2, 3, 6, 7, 9,  11, 14, 16, 17, 19, 22, 24]],
    [22, [2, 3, 6, 8, 10, 11, 13, 15, 17, 19, 22, 24]],
    [23, [2, 3, 6, 8, 10, 11, 13, 16, 18, 19, 21, 23]]
])
def test_generate_sample_basic_stroop_variation(sequence_number, expected_solution):
    block = fully_cross_block([color, text, congruency],
                              [color, congruency],
                              [])
    enumerator = UCSolutionEnumerator(block)
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
    [0,  [1, 3, 6, 8, 11, 14, 16, 18, 20, 23, 24, 28]],
    [1,  [1, 4, 7, 8, 10, 13, 16, 18, 20, 23, 24, 28]],
    [41, [2, 3, 7, 8, 10, 13, 15, 19, 21, 23, 25, 27]]
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
    assert enumerator.generate_sample(sequence_number) == expected_solution
