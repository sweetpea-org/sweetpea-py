import operator as op
import pytest

from itertools import permutations

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.blocks import FullyCrossBlock

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
size  = Factor("size",  ["big", "small", "tiny"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

text_repeats_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[1], [text]))
])

color3 = Factor("color3", ["red", "blue", "green"])

yes_fn = lambda colors: colors[0] == colors[1] == colors[2]
no_fn = lambda colors: not yes_fn(colors)
color3_repeats_factor = Factor("color3 repeats?", [
    DerivedLevel("yes", Window(yes_fn, [color3], 3, 1)),
    DerivedLevel("no",  Window(no_fn, [color3], 3, 1))
])


def test_fully_cross_block_validate():
    # Should not allow DerivedLevels in the crossing.
    # I think it makes sense to prohibit this, but I could be wrong. At the very least,
    # this will leave a reminder that, if it does make sense, there is more work in the
    # codebase to allow it correctly. The FullyCross constraint won't handle it right now.
    with pytest.raises(ValueError):
        FullyCrossBlock([color, text, con_factor],
                        [color, text, con_factor],
                        [])


@pytest.mark.parametrize('design,expected',
    [([color, text, color_repeats_factor, text_repeats_factor], [0, 2, 16, 22]),
     ([color, text, text_repeats_factor, color_repeats_factor], [0, 2, 22, 16]),
     ([color_repeats_factor, text, color, text_repeats_factor], [2, 0, 16, 22]),
     ([text_repeats_factor, text, color, color_repeats_factor], [2, 0, 22, 16])])
def test_fully_cross_block_first_variable_for_factor(design, expected):
    block = fully_cross_block(design, [color, text], [])

    assert block.first_variable_for_level("color", "red") == expected[0]
    assert block.first_variable_for_level("color", "blue") == expected[0] + 1
    assert block.first_variable_for_level("text", "red") == expected[1]
    assert block.first_variable_for_level("text", "blue") == expected[1] + 1
    assert block.first_variable_for_level("repeated color?", "yes") == expected[2]
    assert block.first_variable_for_level("repeated color?", "no") == expected[2] + 1
    assert block.first_variable_for_level("repeated text?", "yes") == expected[3]
    assert block.first_variable_for_level("repeated text?", "no") == expected[3] + 1


def test_fully_cross_block_first_variable_for_factor_with_color3():
    block = fully_cross_block([color3_repeats_factor, color3, text], [color3, text], [])

    assert block.first_variable_for_level("color3 repeats?", "yes") == 30
    assert block.first_variable_for_level("color3 repeats?", "no") == 31


def test_fully_cross_block_decode_variable():
    block = fully_cross_block([color, text, color_repeats_factor, text_repeats_factor],
                              [color, text],
                              [])

    assert block.decode_variable(1) == ("color", "red")
    assert block.decode_variable(2) == ("color", "blue")
    assert block.decode_variable(5) == ("color", "red")
    assert block.decode_variable(14) == ("color", "blue")

    assert block.decode_variable(3) == ("text", "red")
    assert block.decode_variable(4) == ("text", "blue")
    assert block.decode_variable(15) == ("text", "red")
    assert block.decode_variable(12) == ("text", "blue")

    assert block.decode_variable(17) == ("repeated color?", "yes")
    assert block.decode_variable(18) == ("repeated color?", "no")
    assert block.decode_variable(19) == ("repeated color?", "yes")
    assert block.decode_variable(22) == ("repeated color?", "no")

    assert block.decode_variable(23) == ("repeated text?", "yes")
    assert block.decode_variable(24) == ("repeated text?", "no")
    assert block.decode_variable(27) == ("repeated text?", "yes")
    assert block.decode_variable(28) == ("repeated text?", "no")


def test_fully_cross_block_decode_variable_with_transition_first():
    block = fully_cross_block([text_repeats_factor, text, color, color_repeats_factor],
                              [color, text],
                              [])

    assert block.decode_variable(1) == ("text", "red")
    assert block.decode_variable(2) == ("text", "blue")
    assert block.decode_variable(5) == ("text", "red")
    assert block.decode_variable(14) == ("text", "blue")

    assert block.decode_variable(3) == ("color", "red")
    assert block.decode_variable(4) == ("color", "blue")
    assert block.decode_variable(15) == ("color", "red")
    assert block.decode_variable(12) == ("color", "blue")

    assert block.decode_variable(17) == ("repeated text?", "yes")
    assert block.decode_variable(18) == ("repeated text?", "no")
    assert block.decode_variable(19) == ("repeated text?", "yes")
    assert block.decode_variable(22) == ("repeated text?", "no")

    assert block.decode_variable(23) == ("repeated color?", "yes")
    assert block.decode_variable(24) == ("repeated color?", "no")
    assert block.decode_variable(27) == ("repeated color?", "yes")
    assert block.decode_variable(28) == ("repeated color?", "no")


def test_fully_cross_block_trials_per_sample():
    text_single  = Factor("text",  ["red"])

    assert FullyCrossBlock([], [color, color], []).trials_per_sample() == 4
    assert FullyCrossBlock([], [color, color, color], []).trials_per_sample() == 8
    assert FullyCrossBlock([], [size, text_single], []).trials_per_sample() == 3
    assert FullyCrossBlock([], [size, color], []).trials_per_sample() == 6
    assert FullyCrossBlock([], [text_single], []).trials_per_sample() == 1

    assert FullyCrossBlock([color, text, color_repeats_factor], [color, text], []).trials_per_sample() == 4


def test_fully_cross_block_variables_per_trial():
    assert FullyCrossBlock([color, text], [], []).variables_per_trial() == 4
    assert FullyCrossBlock([color, text, con_factor], [], []).variables_per_trial() == 6

    # Should exclude Transition and Windows from variables per trial count, as they don't always
    # have a representation in the first few trials. (Depending on the window width)
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_per_trial() == 4


def test_fully_cross_block_grid_variables():
    assert FullyCrossBlock([color, text, con_factor],
                           [color, text], []).grid_variables() == 24

    # Should include grid variables, as well as additional variables for complex windows.
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).grid_variables() == 16


def test_fully_cross_block_variables_per_sample():
    assert FullyCrossBlock([color, text, con_factor],
                           [color, text], []).variables_per_sample() == 24

    # Should include grid variables, as well as additional variables for complex windows.
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_per_sample() == 22

    assert FullyCrossBlock([color, text, color_repeats_factor, text_repeats_factor],
                           [color, text],
                           []).variables_per_sample() == 28


def test_fully_cross_block_variables_for_factor():
    assert FullyCrossBlock([color, text], [color, text], []).variables_for_factor(color) == 8
    assert FullyCrossBlock([color, text], [color, text], []).variables_for_factor(text) == 8

    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_for_factor(color_repeats_factor) == 6
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_for_factor(color_repeats_factor) == 6

    assert FullyCrossBlock([color3_repeats_factor, color3, text],
                           [color3, text],
                           []).variables_for_factor(color3) == 18

    assert FullyCrossBlock([color3_repeats_factor, color3, text],
                           [color3, text],
                           []).variables_for_factor(text) == 12

    assert FullyCrossBlock([color3_repeats_factor, color3, text],
                           [color3, text],
                           []).variables_for_factor(color3_repeats_factor) == 8
