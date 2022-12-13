# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition,
    CrossBlock, synthesize_trials, print_experiments, 
    CMSGen, RandomGen
)

import numpy as np

"""
Gratton (1992) design
***********************
factors (levels):
- target direction (1, -1)
- flanker direction (1, -1), Factor dependent on target response and congruency
- correct response (left, right), Factor dependent on target response
- response Transition (repetition, switch). Factor dependent on response
- congruency (congruent, incongruent)
- congruency Transition (congruent-congruent, congruent-incongruent, congruent-neutral, incongruent-congruent, incongruent-incongruent, incongruent-neutral, neutral-congruent, neutral-incongruent, neutral-neutral)

design:
- counterbalancing reward x response x response_transition x congruency_transition

"""

# DEFINE REWARD, RESPONSE and CONGRUENCY FACTORS

target_direction    = Factor("target direction",   ["1", "-1"])
congruency  = Factor("congruency",  ["congruent", "incongruent"])


# DEFINE CONGRUENCY TRANSITION FACTOR

def con_con(congruency):
    return congruency[-1] == "congruent" and congruency[0] == "congruent"
def con_inc(congruency):
    return congruency[-1] == "congruent" and congruency[0] == "incongruent"
def inc_con(congruency):
    return congruency[-1] == "incongruent" and congruency[0] == "congruent"
def inc_inc(congruency):
    return congruency[-1] == "incongruent" and congruency[0] == "incongruent"


congruency_transition = Factor("congruency Transition", [
    DerivedLevel("congruent-congruent", Transition(con_con, [congruency])),
    DerivedLevel("congruent-incongruent", Transition(con_inc, [congruency])),
    DerivedLevel("incongruent-congruent", Transition(inc_con, [congruency])),
    DerivedLevel("incongruent-incongruent", Transition(inc_inc, [congruency])),
])

# DEFINE FLANKER RESPONSE FACTOR
def flanker_left(target_direction, congruency):
    return ((target_direction == "1" and congruency == "congruent") or (target_direction == "-1" and congruency == "incongruent"))

def flanker_right(target_direction, congruency):
    return not flanker_left(target_direction, congruency)

flanker_direction = Factor("flanker direction", [
    DerivedLevel("1", WithinTrial(flanker_left,   [target_direction, congruency])),
    DerivedLevel("-1", WithinTrial(flanker_right,   [target_direction, congruency]))
])

# DEFINE CORRECT RESPONSE
def response_left(target_direction):
    return target_direction == "1"

def response_right(target_direction):
    return not response_left((target_direction))

correct_response = Factor("correct response", [
    DerivedLevel("left", WithinTrial(response_left,   [target_direction])),
    DerivedLevel("right", WithinTrial(response_right,   [target_direction]))
])

# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(responses):
    return responses[-1] == responses[0]

def response_switch(responses):
    return not response_repeat(responses)

response_transition = Factor("resp_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [correct_response])),
    DerivedLevel("switch", Transition(response_switch, [correct_response]))
])

# DEFINE SEQUENCE CONSTRAINTS

constraints = []

# DEFINE EXPERIMENT

design       = [target_direction, congruency, flanker_direction, congruency_transition, correct_response, response_transition]
crossing     = [target_direction, congruency_transition, response_transition]
block        = CrossBlock(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials(block, 5, RandomGen)

print_experiments(block, experiments)


target_sequence = np.asarray(experiments[0]["target direction"]).astype(float)
flanker_sequence = np.asarray(experiments[0]["flanker direction"]).astype(float)
congruency_sequence = experiments[0]["congruency"]
congruency_transition_sequence = experiments[0]["congruency Transition"]

print("target sequence", target_sequence)
print("flanker sequence", target_sequence)
print("congruency sequence", congruency_sequence)
print("congruency Transition sequence", congruency_transition_sequence)
