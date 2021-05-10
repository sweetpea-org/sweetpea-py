# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments


"""
Padmala & Pessoa (2011) design
***********************
factors (levels):
- reward (rewarded, non-rewarded)
- response (left, right)
- response transition (repetition, switch). factor dependent on response:
- congruency (congruent, incongruent, neutral)
- congruency transition (congruent-congruent, congruent-incongruent, congruent-neutral, incongruent-congruent, incongruent-incongruent, incongruent-neutral, neutral-congruent, neutral-incongruent, neutral-neutral)

design:
- counterbalancing reward x response x response_transition x congruency_transition

"""

# DEFINE REWARD, RESPONSE and CONGRUENCY FACTORS

reward      = factor("reward", ["rewarded", "non-rewarded"])
response    = factor("response",   ["building", "house"])
congruency  = factor("congruency",  ["congruent", "incongruent", "neutral"])

# DEFINE CONGRUENCY TRANSITION FACTOR

def con_con(congruency):
    return congruency[0] == "congruent" and congruency[1] == "congruent"
def con_inc(congruency):
    return congruency[0] == "congruent" and congruency[1] == "incongruent"
def con_ntr(congruency):
    return congruency[0] == "congruent" and congruency[1] == "neutral"
def inc_con(congruency):
    return congruency[0] == "incongruent" and congruency[1] == "congruent"
def inc_inc(congruency):
    return congruency[0] == "incongruent" and congruency[1] == "incongruent"
def inc_ntr(congruency):
    return congruency[0] == "incongruent" and congruency[1] == "neutral"
def ntr_con(congruency):
    return congruency[0] == "neutral" and congruency[1] == "congruent"
def ntr_inc(congruency):
    return congruency[0] == "neutral" and congruency[1] == "incongruent"
def ntr_ntr(congruency):
    return congruency[0] == "neutral" and congruency[1] == "neutral"


congruency_transition = factor("congruency_transition", [
    derived_level("congruent-congruent", transition(con_con, [congruency])),
    derived_level("congruent-incongruent", transition(con_inc, [congruency])),
    derived_level("congruent-neutral", transition(con_ntr, [congruency])),
    derived_level("incongruent-congruent", transition(inc_con, [congruency])),
    derived_level("incongruent-incongruent", transition(inc_inc, [congruency])),
    derived_level("incongruent-neutral", transition(inc_ntr, [congruency])),
    derived_level("neutral-congruent", transition(ntr_con, [congruency])),
    derived_level("neutral-incongruent", transition(ntr_inc, [congruency])),
    derived_level("neutral-neutral", transition(ntr_ntr, [congruency]))
])

# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(responses):
    return responses[0] == responses[1]

def response_switch(responses):
    return not response_repeat(responses)

response_transition = factor("resp_transition", [
    derived_level("repeat", transition(response_repeat, [response])),
    derived_level("switch", transition(response_switch, [response]))
])

# DEFINE SEQUENCE CONSTRAINTS

constraints = []

# DEFINE EXPERIMENT

design       = [congruency, reward, response, congruency_transition, response_transition]
crossing     = [reward, response, congruency_transition, response_transition]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials_non_uniform(block, 5)

print_experiments(block, experiments)
