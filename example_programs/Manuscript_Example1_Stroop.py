import sys
sys.path.append("..")

# Ported to new API

from sweetpea import (
    Factor, DerivedLevel, WithinTrial,
    MinimumTrials,
    CrossBlock, synthesize_trials,
    print_experiments
)

# color and word factors

color      = Factor("color",  ["red", "blue", "green", "brown"])
word       = Factor("motion", ["red", "blue", "green", "brown"])

# congruency factor

def congruent(color, word):
    return color == word

def incongruent(color, word):
    return not congruent(color, word)

conLevel = DerivedLevel("con", WithinTrial(congruent,   [color, word]))
incLevel = DerivedLevel("inc", WithinTrial(incongruent,   [color, word]))

congruency = Factor("congruency", [
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

response = Factor("response", [
    DerivedLevel("up", WithinTrial(response_up,   [color])),
    DerivedLevel("down", WithinTrial(response_down,   [color])),
    DerivedLevel("left", WithinTrial(response_left,   [color])),
    DerivedLevel("right", WithinTrial(response_right,   [color])),
])

# constraints

constraints = [MinimumTrials(20)]

# experiment

design       = [color, word, congruency, response]
crossing     = [color, word]
block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 1)

print_experiments(block, experiments)
