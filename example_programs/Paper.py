# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

import operator
from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea import fully_cross_block, at_most_k_in_a_row, exclude
from sweetpea import synthesize_trials_non_uniform, synthesize_trials, print_experiments

color_list = ["red", "green", "blue"]

color = factor("color", color_list)
word  = factor("word",  color_list)

congruent   = derived_level("con", within_trial(operator.eq, [color, word]))
incongruent = derived_level("inc", within_trial(operator.ne, [color, word]))

congruence  = factor("congruence", [congruent, incongruent])

one_con_at_a_time = at_most_k_in_a_row(1, (congruence, congruent))


def one_diff(colors, words):
    if (colors[0] == colors[1]):
        return words[0] != words[1]
    else:
        return words[0] == words[1]

def both_diff(colors, words):
    return not one_diff(colors, words)

one = derived_level("one", transition(one_diff, [color, word]))
both = derived_level("both", transition(both_diff, [color, word]))
changed = factor("changed", [one, both])

block        = fully_cross_block([color,word,congruence,changed], [color,word,changed], [])

experiments  = synthesize_trials_non_uniform(block, 1)

# experiments  = synthesize_trials(block, 1, UniformCombinatoricSamplingStrategy)
#
# In the above rejection-sampling mode, there's about a 1-in-2^18 (= 1-in-260k)
# chance that a random assignment of the `changed` level will work, based on
# a roughly 50% chance of each trial being right and 18 trials. That's in range
# to find solutions, but it's not fast.

print_experiments(block, experiments)
