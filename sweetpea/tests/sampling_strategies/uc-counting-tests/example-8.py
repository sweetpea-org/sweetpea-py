import operator as op

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial

color_list = ["red", "orange", "yellow", "green", "blue", "indigo"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

design   = [color, text, congruency]
crossing = [color, text]
block    = fully_cross_block(design, crossing, [])

# ASSERT COUNT = 371993326789901217467999448150835200000000
