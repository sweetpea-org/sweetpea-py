# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import *

"""
Mini-blocks: keeping one design constant across a run of trials that
realizes another design.

The `Nest` constructor combines two already-constructed blocks: each
combination of the *outer* block's crossing is held constant for one full
instance of the *inner* block. `Merge` runs blocks side by side, and
`Repeat` re-runs a block with extra constraints that span the repetitions.

This experiment is simple enough that all solvers can handle it.
"""

print('=== A plain block with a single crossed factor ===')

size  = Factor("size", ["large", "small"])
block = CrossBlock([size], [size], [])

print("_trials_per_sample =", block._trials_per_sample())
experiments = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)


print('=== Nest: hold `color` constant across each instance of the block ===')

color = Factor("color", ["red", "blue"])
color_block = CrossBlock([color], [color], [])

nested_block = Nest(outer_block=color_block, inner_block=block, constraints=[])
print("_trials_per_sample =", nested_block._trials_per_sample())
experiments = synthesize_trials(nested_block, 1, CMSGen)
print_experiments(nested_block, experiments)


print('=== Nest of a Nest: `context` x `task` around the previous block ===')

context = Factor("context", ["high", "low"])
task    = Factor("task",    ["A", "B"])
ct_block = CrossBlock([context, task], [context, task], [])

nested_block2 = Nest(outer_block=ct_block, inner_block=nested_block, constraints=[])
print("_trials_per_sample =", nested_block2._trials_per_sample())
experiments = synthesize_trials(nested_block2, 1, CMSGen)
print_experiments(nested_block2, experiments)


print('=== Merge + Sequential: force the outer levels into a fixed order ===')

ordered = Merge([nested_block], constraints=[Sequential(color)])
experiments = synthesize_trials(ordered, 1, CMSGen)
print_experiments(ordered, experiments)


print('=== Nest with a 2x2 inner block inside `task` ===')

inner2 = CrossBlock([size, color], [size, color], [])
print("inner run length =",
      inner2.preamble_size(inner2.crossings[0]) + inner2.crossing_size(inner2.crossings[0]))

task_block = CrossBlock([task], [task], [])
nested_block3 = Nest(outer_block=task_block, inner_block=inner2, constraints=[])
print("_trials_per_sample =", nested_block3._trials_per_sample())
experiments = synthesize_trials(nested_block3, 1, CMSGen)
print_experiments(nested_block3, experiments)


print('=== Repeat: run the inner design twice with a constraint spanning both ===')

repeated = Repeat(inner2, [MinimumTrials(8), AtMostKInARow(1, size)])
print("_trials_per_sample =", repeated._trials_per_sample())
experiments = synthesize_trials(repeated, 1, CMSGen)
print_experiments(repeated, experiments)
