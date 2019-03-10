import operator as op

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial

# Stroop 3, but the text value must always follow color.
color      = Factor("color",      ["red", "blue", "green"])
text       = Factor("text",       ["red", "blue", "green"])

# Global keyword needed to make this work when the tests exec() this file
global correct_order
def correct_order(color, text):
    return (color == "red"   and text == "blue") or \
           (color == "blue"  and text == "green") or \
           (color == "green" and text == "red")

global incorrect_order
def incorrect_order(color, text):
    return not correct_order(color, text)

order = Factor("order", [
    DerivedLevel("correct",   WithinTrial(correct_order,   [color, text])),
    DerivedLevel("incorrect", WithinTrial(incorrect_order, [color, text]))
])

design   = [color, text, order]
crossing = [color, order]
block    = fully_cross_block(design, crossing, [])

# ASSERT COUNT = 5760
