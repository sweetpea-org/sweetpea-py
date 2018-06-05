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

color  = Factor("color",  ("red","blue", "green"))
motion = Factor("motion", ("up", "down"))
task   = Factor("task",   ("color","motion"))

"""
          correct response (left, right): dependent factor.
if task == color & current color == red then correct response =  left
if task == motion & current motion == up then correct response =  left
.
if task == color & current color == blue then correct response =  right
if task == motion & current motion == down then correct response =  right
"""

def response_left(task, color, motion):
    if (task == "color" && color == "red") || (task == "motion" && motion == "up"):
        return True
    else
        return False

"""
btw, this is the same as:
def response_left(task, color, motion):
    return (task == color && color == red) || (task == motion && motion == up)
"""

def response_right(task, color, motion):
    return not response_left(task, color, motion)

response = Factor("response", DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
                              DerivedLevel("right", WithinTrial(response_right, [task, color, motion])))


"""
          congruency (congruent, incongruent): dependent factor.
if current color == red  & current motion == up then response = congruent
if current color == blue & current motion == down then response = congruent
.
if current color == red & current  motion == down then response = incongruent
if current color == blue & current  motion == up then response = incongruent
"""

def congruent(color, motion):
    return ((color == "red") && (motion == "up")) || ((color == "blue") && (motion == "down"))

def incongruent(color, motion):
    return not congruent(color, motion)

congruency = Factor("congruency", DerivedLevel("con", WithinTrial(congruent,   [color, motion])),
                                  DerivedLevel("inc", WithinTrial(incongreunt, [color, motion])))


"""   vvvv <-- does this *also* need a check of which task it is?
       task transition (repetition, switch). dependent factor of task:
if color-color   then task transition = repetition
if motion-motion then task transition = repetition
.
if color-motion then task transition = switch
if motion-color then task transition = switch
"""

def task_repeat(color0, color1, motion0, motion1):
    return (color0 == color1) || (motion0 == motion1)

def task_switch(color0, color1, motion0, motion1):
    return not task_repeat(color0, color1, motion0, motion1)

task_transition = Factor("task_transition", DerivedLevel("repeat", Transition(task_repeat, [color, motion], [color, motion])),
                                            DerivedLevel("switch", Transition(task_switch, [task], [task])))

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
constraints = [ NoMoreThanKInARow k task_transition,
                NoMoreThanKInARow k resp_transition ]

design       = [congruency, response, task, task_transition, resp_transition, color, motion]

crossing     = design
block        = fullyCrossedBlock(design, crossing, constraints)
experiment   = [block]
(nVars, cnf) = synthesizeTrials(experiment)
