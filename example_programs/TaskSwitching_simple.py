from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments


"""
Task Switching Design (simple)
******************************
factors (levels):
- current color (red, blue)
- current motion (up, down)
- current task (color, motion)
- correct response (left, right): dependent factor.
- congruency (congruent, incongruent): dependent factor.
- task transition (repetition, switch). dependent factor of task:
- response transition (repetition, switch). dependent factor of correct response:

constraints:
- counterbalancing congruency x response x task x task-transition x response-transition x color x motion
- no more than 7 task repetitions in a row
- no more than 7 task switches in a row
- no more than 7 response repetitions in a row
- no more than 7 response switches in a row

vv --> does that come from the counterbalancing above?
Total number of trials: we want to have at least 20 instances of each combination of task-transition x congruency
"""

color  = factor("color",  ["red", "blue", "green"])
motion = factor("motion", ["up", "down"])
task   = factor("task",   ["color", "motion"])

"""
          correct response (left, right): dependent factor.
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

response = factor("response", [
    derived_level("left",  within_trial(response_left,  [task, color, motion])),
    derived_level("right", within_trial(response_right, [task, color, motion]))
])


"""
          congruency (congruent, incongruent): dependent factor.
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

congruency = factor("congruency", [
    derived_level("con", within_trial(congruent,   [color, motion])),
    derived_level("inc", within_trial(incongruent, [color, motion]))
])


"""   vvvv <-- does this *also* need a check of which task it is?
task transition (repetition, switch). dependent factor of task:
if color-color   then task transition = repetition
if motion-motion then task transition = repetition
.
if color-motion then task transition = switch
if motion-color then task transition = switch
"""

def task_repeat(tasks):
    return tasks[0] == tasks[1]

def task_switch(tasks):
    return not task_repeat(tasks)

task_transition = factor("task_transition", [
    derived_level("repeat", transition(task_repeat, [task])),
    derived_level("switch", transition(task_switch, [task]))
])

"""
response transition (repetition, switch). dependent factor of correct response:
if left-left then task transition = repetition
if right-right then task transition = repetition
.
if left-right then task transition = switch
if right-left then task transition = switch
"""

def response_repeat(responses):
    return responses[0] == responses[1]

def response_switch(responses):
    return not response_repeat(responses)

resp_transition = factor("resp_transition", [
    derived_level("repeat", transition(response_repeat, [response])),
    derived_level("switch", transition(response_switch, [response]))
])

k = 7
constraints = [at_most_k_in_a_row(k, task_transition),
               at_most_k_in_a_row(k, resp_transition)]

design       = [color, motion, task, congruency, response, task_transition, resp_transition]
crossing     = [color, motion, task]
block        = fully_cross_block(design, crossing, constraints)

experiments  = synthesize_trials_non_uniform(block, 5)

print_experiments(block, experiments)
