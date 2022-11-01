import sys
sys.path.append("..")

from sweetpea.primitives import factor, derived_level, within_trial
from sweetpea.constraints import minimum_trials, exclude
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments

# color and word factors

color      = factor("color",  ["red", "blue", "green", "brown"])
word       = factor("motion", ["red", "blue", "green", "brown"])

# congruency factor

def congruent(color, word):
    return color == word

def incongruent(color, word):
    return not congruent(color, word)

conLevel = derived_level("con", within_trial(congruent,   [color, word]))
incLevel = derived_level("inc", within_trial(incongruent,   [color, word]))

congruency = factor("congruency", [
    conLevel,
    incLevel
])

# response factor

def response_up(color):
    return color == "red"
def response_down(color):
    return color == "blue"
def response_left(color):
    return color == "green"
def response_right(color):
    return color == "brown"

response = factor("response", [
    derived_level("up", within_trial(response_up,   [color])),
    derived_level("down", within_trial(response_down,   [color])),
    derived_level("left", within_trial(response_left,   [color])),
    derived_level("right", within_trial(response_right,   [color])),
])

# constraints

constraints = [minimum_trials(20)]

# experiment

design       = [color, word, congruency, response]
crossing     = [color, word]
block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials_non_uniform(block, 1)

print_experiments(block, experiments)
