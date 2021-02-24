# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import no_more_than_k_in_a_row
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments


"""
Stroop Task
******************************
factors (levels):
- current color (red, blue, green, brown)
- current word (red, blue, green, brown)
- congruency (congruent, incongruent): factor dependent on color and word.
- correct response (up, down, left right): factor dependent on color.
- response transition (repetition, switch). factor dependent on response:

design:
- counterbalancing color x congruency x response transition
- no more than 7 response repetitions in a row
- no more than 7 response switches in a row

"""

# DEFINE COLOR AND WORD factorS

color      = factor("color",  ["red", "blue", "green", "brown"])
word       = factor("motion", ["red", "blue", "green", "brown"])

# DEFINE CONGRUENCY FACTOR

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

# DEFINE RESPONSE FACTOR

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

# DEFINE RESPONSE transition FACTOR

def response_repeat(response):
    return response[0] == response[1]

def response_switch(response):
    return not response_repeat(response)

resp_transition = factor("response_transition", [
    derived_level("repeat", transition(response_repeat, [response])),
    derived_level("switch", transition(response_switch, [response]))
])

# DEFINE SEQUENCE CONSTRAINTS

k = 7
constraints = [no_more_than_k_in_a_row(k, resp_transition)]

# DEFINE EXPERIMENT

design       = [color, word, congruency, resp_transition, response]
crossing     = [color, congruency, resp_transition]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials_non_uniform(block, 5)

print_experiments(block, experiments)
