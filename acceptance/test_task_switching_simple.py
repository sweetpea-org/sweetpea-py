import pytest

from itertools import repeat, permutations
from random import shuffle

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import NoMoreThanKInARow
from sweetpea import fully_cross_block, print_experiments, synthesize_trials_non_uniform, print_encoding_diagram, __generate_cnf
from acceptance import assert_nomorethankinarow

# Simple Factors
color  = Factor("color",  ["red", "blue"])
motion = Factor("motion", ["up", "down"])
task   = Factor("task",   ["color", "motion"])

# Response Definition
def response_left(task, color, motion):
    return (task == "color"  and color  == "red") or \
           (task == "motion" and motion == "up")

def response_right(task, color, motion):
    return not response_left(task, color, motion)

response = Factor("response", [
    DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
    DerivedLevel("right", WithinTrial(response_right, [task, color, motion]))
])

# Congruency Definition
def color_motion_congruent(color, motion):
    return ((color == "red") and (motion == "up")) or \
           ((color == "blue") and (motion == "down"))

def color_motion_incongruent(color, motion):
    return not color_motion_congruent(color, motion)

congruency = Factor("congruency", [
    DerivedLevel("con", WithinTrial(color_motion_congruent,   [color, motion])),
    DerivedLevel("inc", WithinTrial(color_motion_incongruent, [color, motion]))
])

# Task Transition
task_transition = Factor("task transition", [
    DerivedLevel("repeat", Transition(lambda tasks: tasks[0] == tasks[1], [task])),
    DerivedLevel("switch", Transition(lambda tasks: tasks[0] != tasks[1], [task]))
])

# Response Transition
response_transition = Factor("response transition", [
    DerivedLevel("repeat", Transition(lambda responses: responses[0] == responses[1], [response])),
    DerivedLevel("switch", Transition(lambda responses: responses[0] != responses[1], [response]))
])


def __shuffled_design_sample():
    perms = list(permutations([color, motion, task, response, congruency, task_transition, response_transition]))
    shuffle(perms)
    return perms[:6]


# TODO: For some reason, some orderings are UNSAT
@pytest.mark.parametrize('design', __shuffled_design_sample())
def test_that_design_is_correctly_constrained(design):
    crossing = [color, motion, task]

    k = 2
    constraints = [
        NoMoreThanKInARow(k, task_transition),
        NoMoreThanKInARow(k, response_transition)
    ]

    block = fully_cross_block(design, crossing, constraints)
    experiments = synthesize_trials_non_uniform(block, 100)

    assert len(experiments) == 100, "Design: %s" % str(list(map(lambda f: f.name, design)))
    for c in constraints:
        assert_nomorethankinarow(c, experiments)

