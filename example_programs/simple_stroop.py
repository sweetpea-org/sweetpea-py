import operator as op

from sweetpea import *

color = Factor("color", ["red", "blue", "green"])
text  = Factor("text",  ["red", "blue", "green"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]
crossing     = [color, text]

k = 1
constraints = [NoMoreThanKInARow(k, ("congruent?", "con"))]

block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials(block)

print_experiments(block, experiments)
