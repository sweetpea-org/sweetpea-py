import operator as op

from sweetpea import CrossBlock, Factor, DerivedLevel, WithinTrial


color      = Factor("color",      ["red", "blue"])
text       = Factor("text",       ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

design   = [color, text, congruency]
crossing = [color, congruency]
block    = CrossBlock(design, crossing, [])

# ASSERT COUNT = 24
