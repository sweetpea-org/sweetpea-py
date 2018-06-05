"""
Padmala & Pessoa design
***********************
factors (levels):
- congruency (congruent, incongruent, neutral)
- reward (rewarded, non-rewarded)
- response (left, right)
- congruency transition (congruent-congruent, congruent-incongruent, congruent-neutral, incongruent-congruent, incongruent-incongruent, incongruent-neutral, neutral-congruent, neutral-incongruent, neutral-neutral)
constraints:
- counterbalancing congruency x reward x response x congruency transition (3*2*2*9 = 108)
- counterbalancing all transitions <-- ????
Total number of trials: around 120
"""

congruency = Factor("congruency", ["congruent", "incongruent", "neutral"])
reward     = Factor("reward",     ["rewarded", "non-rewarded"])
response   = Factor("response",   ["left", "right"])

congruency_transitions = Factor("congruent?", allTransitions(congruency, congruency))
# con_con_trans_level = DerivedLevel("con_con", Transition("congruent", "congruent", [congruency, congruency]))
# con_inc_trans_level = DerivedLevel("con_inc", Transition(con_inc_trans, [congruency, congruency]))

design       = [congruency, reward, response, congruency_transitions]

crossing     = design
block        = fullyCrossedBlock(design, crossing, [])
experiment   = [block]
(nVars, cnf) = synthesizeTrials(experiment)















# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Notes to self
def allTransitions(the_trial_factor, the_following_trial_factor):
    # TODO iterate and generate all the derivedLevel transitions
    # con_inc_trans_level = DerivedLevel("con_inc", Transition(con_inc_trans, [congruency, congruency]))
    return

# implicit transition function
def which_transition(first_congruency, following_congruency):
    def transition(the_trial, the_next_trial):
        return (the_trial==first_congruency && the_next_trial==following_congruency)
    return transition
