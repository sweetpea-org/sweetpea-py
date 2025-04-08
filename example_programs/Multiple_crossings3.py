# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, Level, Window, IterateSATGen
)

color  = Factor("color",  ["red", "blue", "green"])
motion = Factor("motion", ["up", "down"])
task   = Factor("task",   ["color", "motion"])

# Example of cases when different crossings in MultiCrossBlock have different preamble sizes
# As shown in the example, the preamble trials in individual crossings are not added to the 
# maximum number of trials determined by an individual crossing in crossings

def task_repeat(tasks):
    return tasks[0] == tasks[-1]

def task_switch(tasks):
    return not task_repeat(tasks)

task_transition = Factor("task_transition", [
    DerivedLevel("repeat", Transition(task_repeat, [task])),
    DerivedLevel("switch", Transition(task_switch, [task]))
])

design       = [color, motion, task, task_transition]
constraints=[]
crossing = [[color, motion], [task_transition]]
block        = MultiCrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)
tabulate_experiments(block, experiments, [task_transition])

