# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, Level, Window, IterateSATGen
)

# This is an example of comparisons between  experiments on blocks using 
# different values of require_complete_crossing in MultiCrossBlock
# setting require_complete_crossing as True (default)
# should ensure complete crossings in MultiCrossBlock

f1   = Factor("f1",   ["A", "B", "C", "D", "E", "F"])
f2   = Factor("f2",   ["a", "b", "c", "d", "e"])

constraints=[]

design       = [f1, f2]
crossing = [[f1], [f2]]
constraints = []

block        = MultiCrossBlock(design, crossing, constraints, require_complete_crossing=True)
experiments  = synthesize_trials(block, 1, RandomGen)#, IterateSATGen)#, CMSGen)
print_experiments(block, experiments)
tabulate_experiments(block, experiments, [f2])

block        = MultiCrossBlock(design, crossing, constraints, require_complete_crossing=False)
experiments  = synthesize_trials(block, 1, RandomGen)#, IterateSATGen)#, CMSGen)
print_experiments(block, experiments)
tabulate_experiments(block, experiments, [f2])
