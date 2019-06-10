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
- task transition type, dependent on factor task transition of current trial and factor task on previous trial:
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


color  = Factor("color",  [Level("red"),   Level("blue")])
motion = Factor("motion", [Level("up"),    Level("down")])
size   = Factor("size",   [Level("large"), Level("small")])
task   = Factor("task",   [color, motion, size])

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
    return (task == "color" && color == "red") || (task == "motion" && motion == "up") || (task == "size" && size == "large")

def response_right(task, color, motion, size):
    return not response_left(task, color, motion, size)

response = Factor("response", DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion, size])),
                              DerivedLevel("right", WithinTrial(response_right, [task, color, motion, size])))


"""
          congruency (congruent, incongruent): dependent factor.
if current color == red  & current motion == up & size = large then response = congruent
if current color == blue & current motion == down & size = small then response = congruent
otherwise incongruent
"""

def congruent(color, motion):
    return ((color == "red") && (motion == "up") && (size == "large")) || ((color == "blue") && (motion == "down")  && (size == "small"))

def incongruent(color, motion):
    return not congruent(color, motion)

congruency = Factor("congruency", DerivedLevel("con", WithinTrial(congruent,   [color, motion])),
                                  DerivedLevel("inc", WithinTrial(incongreunt, [color, motion])))


"""
       task transition (repetition, switch). dependent factor of task:
if color-color   then task transition = repetition
if motion-motion then task transition = repetition
if size-size     then task transition = repetition
otherwise switch
"""

def task_repeat(color0, color1, motion0, motion1, size0, size1):
    return (color0 == color1) || (motion0 == motion1) || (size0 == size1)

def task_switch(color0, color1, motion0, motion1):
    return not task_repeat(color0, color1, motion0, motion1)

task_transition = Factor("task_transition", DerivedLevel("repeat", Transition(congruent,   [color0, color1, motion0, motion1])),
                                            DerivedLevel("switch", Transition(incongreunt, [color0, color1, motion0, motion1])))

"""
    task transition type, dependent on factor task transition of current trial and factor task on previous trial:
if task on previous trial = color & task transition on current trial =  switch then task transition type = color switch
if task on previous trial = motion & task transition on current trial =  switch then task transition type = motion switch
if task on previous trial = size & task transition on current trial =  switch then task transition type = size switch
if task on previous trial = color & task transition on current trial =  repetition then task transition type = color repetition
if task on previous trial = motion & task transition on current trial =  repetition then task transition type = motion repetition
if task on previous trial = size & task transition on current trial =  repetition then task transition type = size repetition
"""
def task_

"""
         response transition (repetition, switch). dependent factor of correct response:
if left-left then task transition = repetition
if right-right then task transition = repetition
.
if left-right then task transition = switch
if right-left then task transition = switch
"""

def response_repeat(response0, response1):
    return (response0 == response1)

def response_switch(response0, response1):
    return not response_repeat(response0, response1)

resp_transition = Factor("resp_transition", DerivedLevel("repeat", Transition(resp_repeat, [color0, color1])),
                                            DerivedLevel("switch", Transition(resp_switch, [color0, color1])))

k = 7
constraints = [ AtMostKInARow k task_transition,
                AtMostKInARow k resp_transition ]

design       = [congruency, response, task, task_transition, resp_transition, color, motion]

crossing     = design
block        = fullyCrossedBlock(design, crossing, constraints)
experiment   = [block]
(nVars, cnf) = synthesizeTrials(experiment)
