# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

# Ported to new API

import operator
from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition,
    CrossBlock, AtMostKInARow,
    synthesize_trials, RandomGen,
    print_experiments
)

color_list = ["red", "green", "blue"]

color = Factor("color", color_list)
word  = Factor("word",  color_list)

congruent   = DerivedLevel("con", WithinTrial(operator.eq, [color, word]))
incongruent = DerivedLevel("inc", WithinTrial(operator.ne, [color, word]))

congruence  = Factor("congruence", [congruent, incongruent])

one_con_at_a_time = AtMostKInARow(1, (congruence, congruent))


def one_diff(colors, words):
    if (colors[0] == colors[-1]):
        return words[0] != words[-1]
    else:
        return words[0] == words[-1]

def both_diff(colors, words):
    return (colors[0] != colors[-1]) and (words[0] != words[-1])

one = DerivedLevel("one", Transition(one_diff, [color, word]))
both = DerivedLevel("both", Transition(both_diff, [color, word]))
changed = Factor("changed", [one, both])

block        = CrossBlock([color,word,congruence,changed], [color,word,changed], [])

experiments  = synthesize_trials(block, 1)

# experiments  = synthesize_trials(block, 1, RandomGen)
#
# In the RandomGen rejection-sampling mode, there's about a 1-in-2^18 (= 1-in-260k)
# chance that a random assignment of the `changed` level will work, based on
# a roughly 50% chance of each trial being right and 18 trials. That's in range
# to find solutions, but it's not fast.

print_experiments(block, experiments)
