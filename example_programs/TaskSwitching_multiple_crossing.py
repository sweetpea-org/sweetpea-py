# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen
)

"""
Task Switching Design (challenging)
***********************************
factors (levels):
- current color (red, blue)
- current motion (up, down)
- current size (large, small)
- current task (color, motion, size)

- correct response (left, right): dependent factor.
- congruency (congruent, incongruent): dependent factor.
- task transition (repetition, switch). dependent factor of task: <-- difference between task transition & tt-type
- task transition type (color switch, color repetition, motion switch, motion repetition, size switch, size repetition).
dependent on factor task transition of current trial and factor task on previous trial:
color switch: The previous trial was a color task and the current trial is not
color repetition: The previous and current trial are a color task
motion switch: The previous trial was a motion task and the current trial is not
motion repetition: The previous and current trial are a motion task
size switch: The previous trial was a size task and the current trial is not
size repetition: The previous and current trial are a size task

- response transition (repetition, switch). dependent factor of correct response:
if left-left then task transition = repetition
if right-right then task transition = repetition
if left-right then task transition = switch
if right-left then task transition = switch

constraints:
- counterbalancing congruency x response x task x response-transition x color x motion x size x transition type
- no more than 7 task repetitions in a row
- no more than 7 task switches in a row
- no more than 7 response repetitions in a row
- no more than 7 response switches in a row
- this is the toughest constraint: I want to define the probability for each transition type:
color-switch: should occur at 70% of the time
motion-switch: should occur at 70% of the time
size-switch: should occur at 25% of the time
If the probabilistic constraint is too hard to implement then it can be made deterministic:
color-switch and motion-switch should occur twice as frequently as size-switch"""

# Is it possible to counterbalance 
# congruency x response x task x response-transition x color x motion x size x transition type ???
# Does it not have task transition? 

color  = Factor("color",  ["red", "blue"])
motion = Factor("motion", ["up", "down"])
size   = Factor("size",   ["large", "small"])
task   = Factor("task",   ["color", "motion", "size"])

"""
          correct response (left, right): dependent factor.
if task == color & current color == red then correct response =  left
if task == motion & current motion == up then correct response =  left
if task == size & current size == large then correct response =  left
.
if task == color & current color == blue then correct response =  right
if task == motion & current motion == down then correct response =  right
if task == size & current size == small then correct response =  right
"""

def response_left(task, color, motion, size):
    return (task == "color" and color == "red") or (task == "motion" and motion == "up") or (task == "size" and size == "large")

def response_right(task, color, motion, size):
    return not response_left(task, color, motion, size)

response = Factor("response", [DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion, size])),
                              DerivedLevel("right", WithinTrial(response_right, [task, color, motion, size]))])


"""
          congruency (congruent, incongruent): dependent factor.
if current color == red  & current motion == up & size = large then response = congruent
if current color == blue & current motion == down & size = small then response = congruent
otherwise incongruent
"""

def congruent(color, motion, size):
    return ((color == "red") and (motion == "up") and (size == "large")) or ((color == "blue") and (motion == "down")  and (size == "small"))

def incongruent(color, motion, size):
    return not congruent(color, motion, size)

congruency = Factor("congruency", 
    [DerivedLevel("con", WithinTrial(congruent,   [color, motion, size])),
    DerivedLevel("inc", WithinTrial(incongruent, [color, motion, size]))])




"""
       task transition (repetition, switch). dependent factor of task:
if color-color   then task transition = repetition
if motion-motion then task transition = repetition
if size-size     then task transition = repetition
otherwise switch
"""
# This seems to be defined incorrectly.
# First need to change this to depend on task. 
# Then Will Disucss whether both task transition and task transition type are needed.

# Old Codes
# def task_repeat(color, motion, size):
#     return (color[0] == color[-1]) or (motion[0] == motion[-1]) or (size[0] == size[-1])

# def task_switch(color, motion, size):
#     return not task_repeat(color, motion, size)

# task_transition = Factor("task_transition", [
#     DerivedLevel("repeat", Transition(task_repeat, [color, motion, size])),
#     DerivedLevel("switch", Transition(task_switch, [color, motion, size]))
# ])

def task_repeat(tasks):
    return tasks[0] == tasks[-1]

def task_switch(tasks):
    return not task_repeat(tasks)

task_transition = Factor("task_transition", [
    DerivedLevel("repeat", Transition(task_repeat, [task])),
    DerivedLevel("switch", Transition(task_switch, [task]))
])

"""
    task transition type, dependent on factor task transition of current trial and factor task on previous trial:
if task on previous trial = color & task transition on current trial =  switch then task transition type = color switch
if task on previous trial = motion & task transition on current trial =  switch then task transition type = motion switch
if task on previous trial = size & task transition on current trial =  switch then task transition type = size switch
if task on previous trial = color & task transition on current trial =  repetition then task transition type = color repetition
if task on previous trial = motion & task transition on current trial =  repetition then task transition type = motion repetition
if task on previous trial = size & task transition on current trial =  repetition then task transition type = size repetition
"""
#def task_ currently not used?

# Need to change the definition?

def color_switch(tasks):
    return tasks[0] != tasks[-1] and tasks[-1] == "color"

def color_repeat(tasks):
    return tasks[0] == tasks[-1] and tasks[-1] == "color"

def motion_switch(tasks):
    return tasks[0] != tasks[-1] and tasks[-1] == "motion"

def motion_repeat(tasks):
    return tasks[0] == tasks[-1] and tasks[-1] == "motion"

def size_switch(tasks):
    return tasks[0] != tasks[-1] and tasks[-1] == "size"

def size_repeat(tasks):
    return tasks[0] == tasks[-1] and tasks[-1] == "size"

# Non weighted
# task_transition = Factor("task_transition_type", [
#     DerivedLevel("color_switch", Transition(color_switch, [task])),
#     DerivedLevel("color_repeat", Transition(color_repeat, [task])),
#     DerivedLevel("motion_switch", Transition(motion_switch, [task])),
#     DerivedLevel("motion_repeat", Transition(motion_repeat, [task])),
#     DerivedLevel("size_switch", Transition(size_switch, [task])),
#     DerivedLevel("size_repeat", Transition(size_repeat, [task])),
# ])


# Deterministic constraints:
# color-switch and motion-switch occur twice as frequently as size-switch

task_transition_type = Factor("task_transition_type", [
    DerivedLevel("color_switch", Transition(color_switch, [task]), 1),
    DerivedLevel("color_repeat", Transition(color_repeat, [task]), 1),
    DerivedLevel("motion_switch", Transition(motion_switch, [task]), 1),
    DerivedLevel("motion_repeat", Transition(motion_repeat, [task]), 1),
    DerivedLevel("size_switch", Transition(size_switch, [task]), 1),
    DerivedLevel("size_repeat", Transition(size_repeat, [task]), 1),
])

"""
         response transition (repetition, switch). dependent factor of correct response:
if left-left then task transition = repetition
if right-right then task transition = repetition
.
if left-right then task transition = switch
if right-left then task transition = switch
"""

def response_repeat(response):
    return (response[0] == response[-1])

def response_switch(response):
    return not response_repeat(response)

resp_transition = Factor("resp_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [response])),
    DerivedLevel("switch", Transition(response_switch, [response]))
])

# k = 7

# constraints = [AtMostKInARow(k, task_transition),
#                AtMostKInARow(k, resp_transition)]#,
#               MinimumTrials(25)]
                
design       = [color, motion, size, task, congruency, response, task_transition, task_transition_type, resp_transition]

constraints=[]

# Single Crossing
# crossing     = [response, task_transition_type]#color, motion, size, task]
# crossing     = [color, motion, size, task]
# block        = CrossBlock(design, crossing, constraints)

# When multiple corssing, number of trials is determined by the maximum of number 
# that would be determined by an individual crossing in crossings, which is [color, motion, size, task]
# However, since [task_transition_type] has a warm-up trial due to its transition level,
# the warm-up trial is also added to the minimum number of trials needed, making it 24+1 = 25 trials
crossing = [[color, motion, size, task], [task_transition_type]]
block        = MultiCrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 1, CMSGen)
# Could also use IterateGen or RandomGen

print_experiments(block, experiments)
# tabulate_experiments(block, experiments, [color, motion, size, task])
# tabulate_experiments(block, experiments, [response, task_transition_type])
tabulate_experiments(block, experiments, [task_transition_type])