# Make SweetPea visible regardless of whether it's been installed.
import sys

sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, AtLeastKInARow, Exclude, ExactlyK,
    CrossBlock, synthesize_trials, print_experiments, tabulate_experiments, sample_mismatch_experiment,
    CMSGen, IterateGen, RandomGen, IterateILPGen,
)
from sweetpea._internal.sampling_strategy.random import UCSolutionEnumerator
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

color = Factor("color", ["red", "green"])
word = Factor("word", ["red", "green"])


# DEFINE CONGRUENCY FACTOR

def congruent(color, word):
    return color == word


def incongruent(color, word):
    return not congruent(color, word)


conLevel = DerivedLevel("con", WithinTrial(congruent, [color, word]))
incLevel = DerivedLevel("inc", WithinTrial(incongruent, [color, word]))

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
    DerivedLevel("up", WithinTrial(response_up, [color])),
    DerivedLevel("down", WithinTrial(response_down, [color])),
    DerivedLevel("left", WithinTrial(response_left, [color])),
    DerivedLevel("right", WithinTrial(response_right, [color])),
])


# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(response):
    return response[0] == response[-1]


def response_switch(response):
    return not response_repeat(response)


resp_transition = Factor("response_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [response])),
    DerivedLevel("switch", Transition(response_switch, [response]))
])

# DEFINE SEQUENCE CONSTRAINTS

k = 2
constraints = [AtLeastKInARow(k, resp_transition)]

# DEFINE EXPERIMENT

design = [color, word, congruency, resp_transition, response]
crossing = [color, word]
block = CrossBlock(design, crossing, constraints)

# SOLVE

experiment_correct = synthesize_trials(block, 1)[0]


# constraint and crossing error
experiment_error_constraint = {'color': ['red', 'green', 'red', 'red'],
                      'word': ['red', 'red', 'green', 'green'],
                      'response': ['up', 'left', 'up', 'up'],
                      'congruency': ['con', 'inc', 'inc', 'inc'],
                      'response_transition': ['', 'switch', 'switch', 'repeat']}

# This sequences test fails, since the last trial response is labeled incorrect (should be up)
experiment_error_response = {'color': ['red', 'green', 'red', 'green'],
                             'word': ['red', 'red', 'green', 'green'],
                             'response': ['up', 'left', 'up', 'left'],
                             'congruency': ['con', 'inc', 'inc', 'inc'],
                             'response_transition': ['', 'switch', 'switch', 'switch']}

# This sequences test fails, since the third trial congruency is labeled con (should be inc)
experiment_error_congruency = {'color': ['red', 'green', 'red', 'green'],
                               'word': ['red', 'red', 'green', 'green'],
                               'response': ['up', 'left', 'up', 'up'],
                               'congruency': ['con', 'inc', 'con', 'inc'],
                               'response_transition': ['', 'switch', 'switch', 'repeat']}

# This sequences test fails, since the second trial response transition is labeled repeat (should be switch)
experiment_error_response_transition = {'color': ['red', 'green', 'red', 'red'],
                                        'word': ['red', 'red', 'green', 'green'],
                                        'response': ['up', 'left', 'up', 'up'],
                                        'congruency': ['con', 'inc', 'inc', 'inc'],
                                        'response_transition': ['', 'repeat', 'switch', 'repeat']}

test_correct = sample_mismatch_experiment(block, experiment_correct)
test_error_constraint = sample_mismatch_experiment(block, experiment_error_constraint)
test_error_response = sample_mismatch_experiment(block, experiment_error_response)
test_error_congruency = sample_mismatch_experiment(block, experiment_error_congruency)
test_error_response_transition = sample_mismatch_experiment(block, experiment_error_response_transition)

print(test_correct)
print(test_error_constraint)
print(test_error_response)
print(test_error_congruency)
print(test_error_response_transition)



