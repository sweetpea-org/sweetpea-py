# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row, minimum_trials
from sweetpea import fully_cross_block, synthesize_trials, print_experiments, tabulate_experiments
from sweetpea import NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy


"""
Stroop Task
******************************
factors (levels):
- current color (red, blue, green, brown)
- current word (red, blue, green, brown)
- congruency (congruent, incongruent): Factor dependent on color and word.
- correct response (up, down, left right): Factor dependent on color.
- response Transition (repetition, switch). Factor dependent on response:

design:
- counterbalancing color x word x response Transition
- no more than 7 response repetitions in a row
- no more than 7 response switches in a row

"""

# DEFINE COLOR AND WORD FACTORS

color      = Factor("color",  ["red", "blue", "green", "brown"])
word       = Factor("motion", ["red", "blue", "green", "brown"])

# DEFINE CONGRUENCY FACTOR

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

# DEFINE RESPONSE FACTOR

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

# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(response):
    return response[0] == response[1]

def response_switch(response):
    return not response_repeat(response)

resp_transition = Factor("response_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [response])),
    DerivedLevel("switch", Transition(response_switch, [response]))
])

# DEFINE SEQUENCE CONSTRAINTS

k = 7
constraints = [at_most_k_in_a_row(k, resp_transition)]

# DEFINE EXPERIMENT

design       = [color, word, congruency, resp_transition, response]
crossing     = [color, word, resp_transition]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials(block, 5, NonUniformSamplingStrategy())
# Or:
# experiments  = synthesize_trials(block, 5, UniformCombinatoricSamplingStrategy(acceptable_error=3))

print_experiments(block, experiments)

# tabulate_experiments(experiments, crossing)
