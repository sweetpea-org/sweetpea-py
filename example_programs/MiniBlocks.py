# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import *

# This experiment is simple enough that all solvers can handle it

color      = Factor("color", ["red", "blue"])
size       = Factor("size",  ["large", "small"])
context      = Factor("context", ["high", "low"])
task       = Factor("task",  ["A", "B"])

language       = Factor("language",  ["English", "Chinese"])

def is_yelling(color, size):
    return color == "red" and size == "large"

volume = Factor("volume",
                [DerivedLevel("yelling", WithinTrial(is_yelling, [color, size])),
                 ElseLevel("normal")])

design       = [size, context]
crossing     = [size, context]
block        = CrossBlock(design, crossing, [])
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)


nested_design = [color, task, block]
nested_block = NestedBlock(nested_design)
experiments  = synthesize_trials(nested_block, 1, CMSGen)
print_experiments(nested_block, experiments)


nested_design2 = [language, nested_block]
nested_block2 = NestedBlock(nested_design2)
experiments  = synthesize_trials(nested_block2, 1, CMSGen)
print_experiments(nested_block2, experiments)



# permuted_block = PermutedCrossBlock(block=block, external_factor=size)
# permuted_block = PermutedCrossBlock(block=block, external_factor=size)
# experiments = synthesize_trials(permuted_block, 1)
# print_experiments(permuted_block, experiments)


