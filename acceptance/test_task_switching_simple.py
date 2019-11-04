import pytest

from itertools import repeat, permutations
from random import shuffle

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row
from sweetpea import fully_cross_block, print_experiments, synthesize_trials_non_uniform, __generate_cnf
from acceptance import assert_atmostkinarow

# Simple Factors
color  = factor("color",  ["red", "blue"])
motion = factor("motion", ["up", "down"])
task   = factor("task",   ["color", "motion"])

# Response Definition
def response_left(task, color, motion):
    return (task == "color"  and color  == "red") or \
           (task == "motion" and motion == "up")

def response_right(task, color, motion):
    return not response_left(task, color, motion)

response = factor("response", [
    derived_level("left",  within_trial(response_left,  [task, color, motion])),
    derived_level("right", within_trial(response_right, [task, color, motion]))
])

# Congruency Definition
def color_motion_congruent(color, motion):
    return ((color == "red") and (motion == "up")) or \
           ((color == "blue") and (motion == "down"))

def color_motion_incongruent(color, motion):
    return not color_motion_congruent(color, motion)

congruency = factor("congruency", [
    derived_level("con", within_trial(color_motion_congruent,   [color, motion])),
    derived_level("inc", within_trial(color_motion_incongruent, [color, motion]))
])

# Task transition
task_transition = factor("task transition", [
    derived_level("repeat", transition(lambda tasks: tasks[0] == tasks[1], [task])),
    derived_level("switch", transition(lambda tasks: tasks[0] != tasks[1], [task]))
])

# Response transition
response_transition = factor("response transition", [
    derived_level("repeat", transition(lambda responses: responses[0] == responses[1], [response])),
    derived_level("switch", transition(lambda responses: responses[0] != responses[1], [response]))
])


def __shuffled_design_sample():
    perms = list(permutations([color, motion, task, response, congruency, task_transition, response_transition]))
    shuffle(perms)
    return perms[:6]


@pytest.mark.parametrize('design', __shuffled_design_sample())
def test_that_design_is_correctly_constrained(design):
    crossing = [color, motion, task]

    k = 2
    constraints = [
        at_most_k_in_a_row(k, task_transition),
        at_most_k_in_a_row(k, response_transition)
    ]

    block = fully_cross_block(design, crossing, constraints)
    experiments = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 100, "Design: %s" % str(list(map(lambda f: f.name, design)))
    for c in constraints:
        assert_atmostkinarow(c, experiments)
