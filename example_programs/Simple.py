# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import *

# This experiment is simple enough that all solvers can handle it

color      = Factor("color", ["red", "blue"])
size       = Factor("size",  ["large", "small"])

def is_yelling(color, size):
    return color == "red" and size == "large"

volume = Factor("volume",
                [DerivedLevel("yelling", WithinTrial(is_yelling, [color, size])),
                 ElseLevel("normal")])

constraints = [AtMostKInARow(1, color)]

# Adding this constraint would make the design unsatisfiable:
# constraints += [AtLeastKInARow(2, volume)]

design       = [color, size, volume]
crossing     = [color, size]
block        = CrossBlock(design, crossing, constraints)

# We can ask for 10 experiments, but only 8 unique experiments are possible
N = 10

experiments  = synthesize_trials(block, N, CMSGen)
# Or:
# experiments  = synthesize_trials(block, N, UniformGen)
# experiments  = synthesize_trials(block, N, IterateGen)
# experiments  = synthesize_trials(block, N, UniGen)
# experiments  = synthesize_trials(block, N, IterateSATGen)
# experiments  = synthesize_trials(block, N, IterateILPGen)
# experiments  = synthesize_trials(block, N, RandomGen)

print_experiments(block, experiments)
