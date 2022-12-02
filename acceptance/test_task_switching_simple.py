import pytest

from sweetpea import *
from acceptance import assert_atmostkinarow, shuffled_design_sample

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
task_transition = Factor("task Transition", [
    DerivedLevel("repeat", Transition(lambda tasks: tasks[0] == tasks[-1], [task])),
    DerivedLevel("switch", Transition(lambda tasks: tasks[0] != tasks[-1], [task]))
])

# Response Transition
response_transition = Factor("response Transition", [
    DerivedLevel("repeat", Transition(lambda responses: responses[0] == responses[-1], [response])),
    DerivedLevel("switch", Transition(lambda responses: responses[0] != responses[-1], [response]))
])


@pytest.mark.parametrize('design', shuffled_design_sample([color, motion, task, response, congruency, task_transition, response_transition], 6))
def test_that_design_is_correctly_constrained(design):
    crossing = [color, motion, task]

    k = 2
    constraints = [
        AtMostKInARow(k, task_transition),
        AtMostKInARow(k, response_transition)
    ]

    block = CrossBlock(design, crossing, constraints)
    experiments = synthesize_trials(block, 100)

    assert len(experiments) == 100, "Design: %s" % str(list(map(lambda f: f.factor_name, design)))
    for c in constraints:
        assert_atmostkinarow(c, experiments)
