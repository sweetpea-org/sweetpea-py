import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, AcrossTrials


# Common variables for stroop.
color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("color repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

text_repeats_factor = Factor("text repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [text])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [text]))
])

congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", AcrossTrials(lambda color, text: color == text, [color, text], 1, 3)),
    DerivedLevel("no",  AcrossTrials(lambda color, text: color != text, [color, text], 1, 3))
])
