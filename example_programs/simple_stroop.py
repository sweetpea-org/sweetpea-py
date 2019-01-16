import operator as op

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.constraints import AtMostKInARow
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments


color_list = ["red", "green", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]
crossing     = [color, text]

constraints = [AtMostKInARow(1, ("congruent?", "con"))]

block        = fully_cross_block(design, crossing, constraints)

# Synthesize 5 unique, but non-uniformly sampled, trials.
experiments  = synthesize_trials_non_uniform(block, 5)

print_experiments(block, experiments)
