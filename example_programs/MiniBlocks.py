# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import *

# This experiment is simple enough that all solvers can handle it


print('Define block with single factor size')

size       = Factor("size",  ["large", "small"])

design       = [size]
crossing     = [size]
block        = CrossBlock(design, crossing, [])
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)

print('Nested block with an additional factor color without crossing the block')
color      = Factor("color", ["red", "blue"]) 

nested_design = [color, block]
nested_block = NestedBlock(nested_design, [color], [])
experiments  = synthesize_trials(nested_block, 1, CMSGen)
print_experiments(nested_block, experiments)

print('Nested block with two additional factors context, task')
context      = Factor("context", ["high", "low"])
task       = Factor("task",  ["A", "B"])

nested_design2 = [context, task, nested_block]
nested_block2 = NestedBlock(nested_design2, [context, task], [])
experiments  = synthesize_trials(nested_block2, 1, CMSGen)
print_experiments(nested_block2, experiments)

print('Nested block with an additional factor on original block and crossing with color')
print("run_len =", block.preamble_size(block.crossings[0]) + block.crossing_size(block.crossings[0]))
permuted_block = NestedBlock(nested_design, nested_design, [], num_permutations=None)
print("trials_per_sample =", permuted_block.trials_per_sample())
experiments = synthesize_trials(permuted_block, 1)#, CMSGen)
print_experiments(permuted_block, experiments)

print('Nested block of a block (of two factors size, color) that crosses with factor task')
print('This could be slow with some generators!')

design       = [size, color]
crossing     = [size, color]
block        = CrossBlock(design, crossing, [])
print("run_len =", block.preamble_size(block.crossings[0]) + block.crossing_size(block.crossings[0]))
nested_design = [task, block]
permuted_block2 = NestedBlock(nested_design, nested_design, [])
print("trials_per_sample =", permuted_block2.trials_per_sample())
experiments  = synthesize_trials(permuted_block2, 1)#, CMSGen)
print_experiments(permuted_block2, experiments)


