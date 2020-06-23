from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.constraints import minimum_trials, exclude
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments

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

min_20_trials = minimum_trials(20)
exclude_congruent_trials = [exclude(congruency, conLevel)]

constraints = [min_20_trials, exclude_congruent_trials]

# experiment

design       = [color, word, congruency, response]
crossing     = [color, word]
block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials_non_uniform(block, 1)

print_experiments(block, experiments)
