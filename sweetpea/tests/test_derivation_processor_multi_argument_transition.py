import operator as op
import pytest

from sweetpea._internal.primitive import Factor, DerivedLevel, Transition
from sweetpea._internal.constraint import Derivation, Reify
from sweetpea._internal.derivation_processor import DerivationProcessor
from sweetpea import CrossBlock


color_list = ["red", "green"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)


def one_different(colors, texts):
    if (colors[0] == colors[-1]):
        return texts[0] != texts[-1]
    else:
        return texts[0] == texts[-1]

def other_different(colors, texts):
    return not one_different(colors, texts)

one_level   = DerivedLevel("one",  Transition(one_different, [color, text]))
other_level = DerivedLevel("other", Transition(other_different, [color, text]))
change = Factor("change", [one_level, other_level])

design      = [color, text, change]
crossing    = [color, text]
block       = CrossBlock(design, crossing, [Reify(change)])


# Encoding diagram minus 1
# -----------------------------------------------
# |   Trial |   color   |   text    |  change   |
# |       # | red green | red green | one other |
# -----------------------------------------------
# |       1 |  0    1   |  2    3   |           |
# |       2 |  4    5   |  6    7   | 16   17   |
# |       3 |  8    9   | 10   11   | 18   19   |
# |       4 | 12   13   | 14   15   | 20   21   |
# -----------------------------------------------
def test_generate_derivations():
    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [
            [0, 4, 2, 7],
            [0, 4, 3, 6],
            [0, 5, 2, 6],
            [0, 5, 3, 7],
            [1, 4, 2, 6],
            [1, 4, 3, 7],
            [1, 5, 2, 7],
            [1, 5, 3, 6]], change),
        Derivation(17, [
            [0, 4, 2, 6],
            [0, 4, 3, 7],
            [0, 5, 2, 7],
            [0, 5, 3, 6],
            [1, 4, 2, 7],
            [1, 4, 3, 6],
            [1, 5, 2, 6],
            [1, 5, 3, 7]], change)
    ]


def test_shift_window():
    assert DerivationProcessor.shift_window([[0, 0, 2, 3]], one_level.window, 4) == [[0, 4, 2, 7]]
    assert DerivationProcessor.shift_window([[1, 1, 3, 2]], one_level.window, 4) == [[1, 5, 3, 6]]

    assert DerivationProcessor.shift_window([[0, 0, 2, 2]], other_level.window, 4) == [[0, 4, 2, 6]]
    assert DerivationProcessor.shift_window([[0, 0, 3, 3]], other_level.window, 4) == [[0, 4, 3, 7]]
