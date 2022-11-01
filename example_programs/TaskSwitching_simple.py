# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow,
    CrossBlock, synthesize_trials, print_experiments,
    CMSGen, IterateGen, RandomGen
)

"""
Task Switching Design (simple)
******************************
factors (levels):
- current color (red, blue)
- current motion (up, down)
- current task (color, motion)
- correct response (left, right): dependent Factor.
- congruency (congruent, incongruent): dependent Factor.
- task Transition (repetition, switch). dependent Factor of task:
- response Transition (repetition, switch). dependent Factor of correct response:

constraints:
- counterbalancing congruency x response x task x task-Transition x response-Transition x color x motion
- no more than 7 task repetitions in a row
- no more than 7 task switches in a row
- no more than 7 response repetitions in a row
- no more than 7 response switches in a row

vv --> does that come from the counterbalancing above?
Total number of trials: we want to have at least 20 instances of each combination of task-Transition x congruency
"""

color  = Factor("color",  ["red", "blue", "green"])
motion = Factor("motion", ["up", "down"])
task   = Factor("task",   ["color", "motion"])

"""
          correct response (left, right): dependent Factor.
if task == color & current color == red then correct response =  left
if task == motion & current motion == up then correct response =  left
.
if task == color & current color == blue then correct response =  right
if task == motion & current motion == down then correct response =  right
"""

def response_left(task, color, motion):
    if (task == "color" and color == "red") or (task == "motion" and motion == "up"):
        return True
    else:
        return False

"""
btw, this is the same as:
def response_left(task, color, motion):
    return (task == color && color == red) || (task == motion && motion == up)
"""

def response_right(task, color, motion):
    return not response_left(task, color, motion)

response = Factor("response", [
    DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
    DerivedLevel("right", WithinTrial(response_right, [task, color, motion]))
])


"""
          congruency (congruent, incongruent): dependent Factor.
if current color == red  & current motion == up then response = congruent
if current color == blue & current motion == down then response = congruent
.
if current color == red & current  motion == down then response = incongruent
if current color == blue & current  motion == up then response = incongruent
"""

def congruent(color, motion):
    return ((color == "red") and (motion == "up")) or ((color == "blue") and (motion == "down"))

def incongruent(color, motion):
    return not congruent(color, motion)

congruency = Factor("congruency", [
    DerivedLevel("con", WithinTrial(congruent,   [color, motion])),
    DerivedLevel("inc", WithinTrial(incongruent, [color, motion]))
])


"""   vvvv <-- does this *also* need a check of which task it is?
task Transition (repetition, switch). dependent Factor of task:
if color-color   then task Transition = repetition
if motion-motion then task Transition = repetition
.
if color-motion then task Transition = switch
if motion-color then task Transition = switch
"""

def task_repeat(tasks):
    return tasks[0] == tasks[1]

def task_switch(tasks):
    return not task_repeat(tasks)

task_transition = Factor("task_transition", [
    DerivedLevel("repeat", Transition(task_repeat, [task])),
    DerivedLevel("switch", Transition(task_switch, [task]))
])

"""
response Transition (repetition, switch). dependent Factor of correct response:
if left-left then task Transition = repetition
if right-right then task Transition = repetition
.
if left-right then task Transition = switch
if right-left then task Transition = switch
"""

def response_repeat(responses):
    return responses[0] == responses[1]

def response_switch(responses):
    return not response_repeat(responses)

resp_transition = Factor("resp_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [response])),
    DerivedLevel("switch", Transition(response_switch, [response]))
])

k = 7
constraints = [AtMostKInARow(k, task_transition),
               AtMostKInARow(k, resp_transition)]

design       = [color, motion, task, congruency, response, task_transition, resp_transition]
crossing     = [color, motion, task]
block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 5, CMSGen)
# Could also use IterateGen or RandomGen

print_experiments(block, experiments)
