import operator as op

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.blocks import FullyCrossBlock

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
size  = Factor("size",  ["big", "small", "tiny"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])


def test_fully_cross_block_trials_per_sample():
    text  = Factor("text",  ["red"])

    assert FullyCrossBlock([], [color, color], []).trials_per_sample() == 4
    assert FullyCrossBlock([], [color, color, color], []).trials_per_sample() == 8
    assert FullyCrossBlock([], [size, text], []).trials_per_sample() == 3
    assert FullyCrossBlock([], [size, color], []).trials_per_sample() == 6
    assert FullyCrossBlock([], [text], []).trials_per_sample() == 1


def test_fully_cross_block_variables_per_trial():
    assert FullyCrossBlock([color, text], [], []).variables_per_trial() == 4
    assert FullyCrossBlock([color, text, con_factor], [], []).variables_per_trial() == 6


def test_fully_cross_block_variables_per_sample():
    assert FullyCrossBlock([color, text, con_factor],
                           [color, text], []).variables_per_sample() == 24