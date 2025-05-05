# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, MultiCrossBlock, RepeatMode, synthesize_trials, print_experiments,
    CMSGen, IterateGen, RandomGen, IterateSATGen
)

# This is an example of comparisons between  experiments on blocks using 
# different values of require_complete_crossing in MultiCrossBlock
# setting require_complete_crossing as True (default)
# should ensure complete crossings in MultiCrossBlock

f1   = Factor("f1",   ["A", "B", "C", "D"])
f2   = Factor("f2",   ["a", "b", "c"])
f3 = Factor("f3", ['1', '2'])
constraints=[]

design       = [f1, f2, f3]
crossing = [[f1, f3], [f2]]
constraints = []

block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.WEIGHT)
experiments  = synthesize_trials(block, 1, RandomGen)#, IterateSATGen)#, CMSGen)
print_experiments(block, experiments)
# tabulate_experiments(block, experiments, [f2])

block        = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT)
experiments  = synthesize_trials(block, 1, RandomGen)#, IterateSATGen)#, CMSGen)
print_experiments(block, experiments)
# tabulate_experiments(block, experiments, [f2])
