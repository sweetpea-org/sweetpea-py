import operator as op

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial


color      = Factor("color",      ["red", "blue"])
text       = Factor("text",       ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

direction  = Factor("direction",  ["up", "down"])

design   = [color, text, congruency, direction]
crossing = [congruency, direction]
block    = fully_cross_block(design, crossing, [])

# ASSERT COUNT = 384
