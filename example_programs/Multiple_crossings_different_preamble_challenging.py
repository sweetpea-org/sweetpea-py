# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, MultiCrossBlock, RepeatMode, synthesize_trials, print_experiments,
    CMSGen, IterateGen, RandomGen, IterateSATGen, Repeat, DerivedLevel, Transition,
    MinimumTrials, Window, AlignmentMode, CrossBlock
)

# This is an example of comparisons between  experiments on blocks using 
# different values of require_complete_crossing in MultiCrossBlock
# setting require_complete_crossing as True (default)
# should ensure complete crossings in MultiCrossBlock

f1   = Factor("f1",   ["A", "B", "C", "D"])
f2   = Factor("f2",   ["a", "b", "c"])
f3 = Factor("f3", ['1', '2'])
f4 = Factor("f4", ['1', '2'])

def task_repeat(f3):
    return f3[0] == f3[-1]

def task_switch(f3):
    return not task_repeat(f3)

task_transition = Factor("task_transition", [
    DerivedLevel("repeat", Transition(task_repeat, [f3])),
    DerivedLevel("switch", Transition(task_switch, [f3]))
])

congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", Window(lambda f3, f4: f3 == f4, [f3, f4], 3, 1)),
    DerivedLevel("no",  Window(lambda f3, f4: f3 != f4, [f3, f4], 3, 1))
])

constraints=[]

design       = [f1, f2, f3, f4, task_transition, congruent_bookend]
crossing = [[task_transition], [f3, f2], [congruent_bookend]]

constraints = []

block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.WEIGHT, alignment=AlignmentMode.PARALLEL_START)
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)

# block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT, alignment=AlignmentMode.PARALLEL_START)
# experiments  = synthesize_trials(block, 1, RandomGen)
# print_experiments(block, experiments)


block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.WEIGHT, alignment=AlignmentMode.POST_PREAMBLE)
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)

# block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT, alignment=AlignmentMode.POST_PREAMBLE)
# experiments  = synthesize_trials(block, 1, RandomGen)
# print_experiments(block, experiments)


# crossing = [task_transition, congruent_bookend, f2]
# block        = CrossBlock(design, crossing, constraints)#, mode=RepeatMode.REPEAT, alignment=AlignmentMode.POST_PREAMBLE)
# experiments  = synthesize_trials(block, 1, RandomGen)
# print_experiments(block, experiments)
