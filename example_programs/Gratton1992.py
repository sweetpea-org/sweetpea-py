# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
import numpy as np

"""
Gratton (1992) design
***********************
factors (levels):
- target direction (1, -1)
- flanker direction (1, -1), factor dependent on target response and congruency
- correct response (left, right), factor dependent on target response
- response transition (repetition, switch). factor dependent on response
- congruency (congruent, incongruent)
- congruency transition (congruent-congruent, congruent-incongruent, congruent-neutral, incongruent-congruent, incongruent-incongruent, incongruent-neutral, neutral-congruent, neutral-incongruent, neutral-neutral)

design:
- counterbalancing reward x response x response_transition x congruency_transition

"""

# DEFINE REWARD, RESPONSE and CONGRUENCY FACTORS

target_direction    = factor("target direction",   ["1", "-1"])
congruency  = factor("congruency",  ["congruent", "incongruent"])


# DEFINE CONGRUENCY TRANSITION FACTOR

def con_con(congruency):
    return congruency[0] == "congruent" and congruency[1] == "congruent"
def con_inc(congruency):
    return congruency[0] == "congruent" and congruency[1] == "incongruent"
def inc_con(congruency):
    return congruency[0] == "incongruent" and congruency[1] == "congruent"
def inc_inc(congruency):
    return congruency[0] == "incongruent" and congruency[1] == "incongruent"


congruency_transition = factor("congruency transition", [
    derived_level("congruent-congruent", transition(con_con, [congruency])),
    derived_level("congruent-incongruent", transition(con_inc, [congruency])),
    derived_level("incongruent-congruent", transition(inc_con, [congruency])),
    derived_level("incongruent-incongruent", transition(inc_inc, [congruency])),
])

# DEFINE FLANKER RESPONSE FACTOR
def flanker_left(target_direction, congruency):
    return ((target_direction == "1" and congruency == "congruent") or (target_direction == "-1" and congruency == "incongruent"))

def flanker_right(target_direction, congruency):
    return not flanker_left(target_direction, congruency)

flanker_direction = factor("flanker direction", [
    derived_level("1", within_trial(flanker_left,   [target_direction, congruency])),
    derived_level("-1", within_trial(flanker_right,   [target_direction, congruency]))
])

# DEFINE CORRECT RESPONSE
def response_left(target_direction):
    return target_direction == "1"

def response_right(target_direction):
    return not response_left((target_direction))

correct_response = factor("correct response", [
    derived_level("left", within_trial(response_left,   [target_direction])),
    derived_level("right", within_trial(response_right,   [target_direction]))
])

# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(responses):
    return responses[0] == responses[1]

def response_switch(responses):
    return not response_repeat(responses)

response_transition = factor("resp_transition", [
    derived_level("repeat", transition(response_repeat, [correct_response])),
    derived_level("switch", transition(response_switch, [correct_response]))
])

# DEFINE SEQUENCE CONSTRAINTS

constraints = []

# DEFINE EXPERIMENT

design       = [target_direction, congruency, flanker_direction, congruency_transition, correct_response, response_transition]
crossing     = [target_direction, congruency_transition, response_transition]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials_non_uniform(block, 5)

print_experiments(block, experiments)


target_sequence = np.asarray(experiments[0]["target direction"]).astype(float)
flanker_sequence = np.asarray(experiments[0]["flanker direction"]).astype(float)
congruency_sequence = experiments[0]["congruency"]
congruency_transition_sequence = experiments[0]["congruency transition"]

print("target sequence", target_sequence)
print("flanker sequence", target_sequence)
print("congruency sequence", congruency_sequence)
print("congruency transition sequence", congruency_transition_sequence)
