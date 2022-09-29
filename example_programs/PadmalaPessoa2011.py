# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row
from sweetpea import fully_cross_block, synthesize_trials, print_experiments, save_cnf
from sweetpea import NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy


"""
Padmala & Pessoa (2011) design
***********************
factors (levels):
- reward (rewarded, non-rewarded)
- response (left, right)
- response Transition (repetition, switch). Factor dependent on response:
- congruency (congruent, incongruent, neutral)
- congruency Transition (congruent-congruent, congruent-incongruent, congruent-neutral, incongruent-congruent, incongruent-incongruent, incongruent-neutral, neutral-congruent, neutral-incongruent, neutral-neutral)

design:
- counterbalancing reward x response x response_transition x congruency_transition

"""

# DEFINE REWARD, RESPONSE and CONGRUENCY FACTORS

reward      = Factor("reward", ["rewarded", "non-rewarded"])
response    = Factor("response",   ["building", "house"])
congruency  = Factor("congruency",  ["congruent", "incongruent", "neutral"])

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


congruency_transition = Factor("congruency_transition", [
    DerivedLevel("congruent-congruent", Transition(con_con, [congruency])),
    DerivedLevel("congruent-incongruent", Transition(con_inc, [congruency])),
    DerivedLevel("congruent-neutral", Transition(con_ntr, [congruency])),
    DerivedLevel("incongruent-congruent", Transition(inc_con, [congruency])),
    DerivedLevel("incongruent-incongruent", Transition(inc_inc, [congruency])),
    DerivedLevel("incongruent-neutral", Transition(inc_ntr, [congruency])),
    DerivedLevel("neutral-congruent", Transition(ntr_con, [congruency])),
    DerivedLevel("neutral-incongruent", Transition(ntr_inc, [congruency])),
    DerivedLevel("neutral-neutral", Transition(ntr_ntr, [congruency]))
])

# DEFINE RESPONSE TRANSITION FACTOR

def response_repeat(responses):
    return responses[0] == responses[1]

def response_switch(responses):
    return not response_repeat(responses)

response_transition = Factor("resp_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [response])),
    DerivedLevel("switch", Transition(response_switch, [response]))
])

# DEFINE SEQUENCE CONSTRAINTS

constraints = []

# DEFINE EXPERIMENT

design       = [congruency, reward, response, congruency_transition, response_transition]
crossing     = [reward, response, congruency_transition, response_transition]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials(block, 5, NonUniformSamplingStrategy)
# Or:
# experiments  = synthesize_trials(block, 5, UniformCombinatoricSamplingStrategy(acceptable_error = 15))

print_experiments(block, experiments)
