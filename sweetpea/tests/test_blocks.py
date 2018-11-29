import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.blocks import FullyCrossBlock

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
size  = Factor("size",  ["big", "small", "tiny"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_level   = DerivedLevel("yes", Transition(op.eq, [color, color]))
color_no_repeat_level = DerivedLevel("no", Transition(op.ne, [color, color]))
color_repeats_factor  = Factor("color repeats?", [color_repeats_level, color_no_repeat_level])


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


def test_fully_cross_block_variables_for_window():
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_for_window(color_repeats_level.window) == 6
    assert FullyCrossBlock([color, text, color_repeats_factor],
                           [color, text],
                           []).variables_for_window(color_no_repeat_level.window) == 6