# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import *

# This experiment is simple enough that all solvers can handle it

color      = Factor("color", ["red", "blue"])
size       = Factor("size",  ["large", "small"])
context      = Factor("context", ["high", "low"])
task       = Factor("task",  ["A", "B"])


def is_yelling(color, size):
    return color == "red" and size == "large"

volume = Factor("volume",
                [DerivedLevel("yelling", WithinTrial(is_yelling, [color, size])),
                 ElseLevel("normal")])

# constraints = [MinimumTrials(16)]
# constraints +=[ExactlyKInARow(4, color), AtLeastKInARow(4, size)]
# design       = [color, size, volume]
# crossing     = [color, size]#, task_transition]]
# block        = CrossBlock(design, crossing, constraints)#, alignment=AlignmentMode.PARALLEL_START)
# # Adding this constraint would make the design unsatisfiable:
# # constraints += [ExactlyKInARow(3, color)]#, ExactlyKInARow(3, size)]
# experiments  = synthesize_trials(block, 1, CMSGen)
# print_experiments(block, experiments)


constraints = [MinimumTrials(8)]
constraints +=[ExactlyKInARow(4, color)]#, AtMostKInARow(2, size),AtMostKInARow(2, context)]
design       = [color, size, context]
crossing     = [[color], [size,context]]#, task_transition]]
block        = MultiCrossBlock(design, crossing, constraints, mode=[RepeatMode.WEIGHT,RepeatMode.REPEAT])#, alignment=AlignmentMode.PARALLEL_START)
# Adding this constraint would make the design unsatisfiable:
# constraints += [ExactlyKInARow(3, color)]#, ExactlyKInARow(3, size)]
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)







def is_switch(task):
    return task[-1]!=task[0]

def is_repeat(task):
    return not is_switch(task)

task_transition = Factor("task_transition", [
    DerivedLevel("repeat", Transition(is_repeat, [task])),
    DerivedLevel("switch", Transition(is_switch, [task]))
])

constraints = [MinimumTrials(9)]
constraints +=[AtLeastKInARow(4, context)]

design       = [context, task, task_transition]
crossing     = [[context], [task, task_transition]]#, task_transition]]
block        = MultiCrossBlock(design, crossing, constraints, mode=[RepeatMode.WEIGHT,RepeatMode.REPEAT], alignment=AlignmentMode.POST_PREAMBLE)

# We can ask for 10 experiments, but only 8 unique experiments are possible
# N = 10

experiments  = synthesize_trials(block, 1, CMSGen)
# Or:
# experiments  = synthesize_trials(block, N, UniformGen)
# experiments  = synthesize_trials(block, N, IterateGen)
# experiments  = synthesize_trials(block, N, UniGen)
# experiments  = synthesize_trials(block, N, IterateSATGen)
# experiments  = synthesize_trials(block, N, IterateILPGen)
# experiments  = synthesize_trials(block, N, RandomGen)

print_experiments(block, experiments)



# design       = [color, size, volume]
# crossing     = [[color, volume],[size]]
# block        = MultiCrossBlock(design, crossing, [], mode=RepeatMode.REPEAT, alignment=AlignmentMode.POST_PREAMBLE)


# experiments  = synthesize_trials(block, 1, CMSGen)
# # Or:
# # experiments  = synthesize_trials(block, N, UniformGen)
# # experiments  = synthesize_trials(block, N, IterateGen)
# # experiments  = synthesize_trials(block, N, UniGen)
# # experiments  = synthesize_trials(block, N, IterateSATGen)
# # experiments  = synthesize_trials(block, N, IterateILPGen)
# # experiments  = synthesize_trials(block, N, RandomGen)

# print_experiments(block, experiments)
