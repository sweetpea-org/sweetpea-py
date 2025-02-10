from sweetpea import (
    Factor, ContinuousFactor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen
)

import random

# Define a sampling function for continuous values
def sample_continuous():
    return random.uniform(0.5, 1.5)  # Response times between 0.5 and 1.5 seconds

# Create a ContinuousFactor

def difference(t1, t2):
    return t1-t2


completion_time = ContinuousFactor("completion_time", [], sampling_function=sample_continuous)
response_time = ContinuousFactor("response_time", [], sampling_function=sample_continuous)

difference_time = ContinuousFactor("difference_time", [
    completion_time, response_time], sampling_function=difference)

difference_time2 = ContinuousFactor("difference_time2", [
    1.5, response_time], sampling_function=difference)

difference_time3 = ContinuousFactor("difference_time3", [
    difference_time, difference_time2], sampling_function=difference)

# # Define a discrete factor (color)
color = Factor("color", ["red", "blue", "green"])

# # Create the experimental design using the factors
design = [color, completion_time, response_time, \
            difference_time, difference_time2, difference_time3]

crossing = [color]
constraints = [MinimumTrials(5)]


block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 2, CMSGen)

print_experiments(block, experiments)
tabulate_experiments(block, experiments, [color])#, completion_time])


############




# # Create a ContinuousFactor
# response_time = Factor("response_time", [], sampling_function=sample_continuous, sample_size=3)

# # Define a discrete factor (color)
# color = Factor("color", ["red", "blue", "green"])

# # Create the experimental design using the factors
# design = [color, response_time]

# crossing = design
# constraints = []


# block        = CrossBlock(design, crossing, constraints)

# experiments  = synthesize_trials(block, 1, CMSGen)
# print_experiments(block, experiments)
# tabulate_experiments(block, experiments, [color])


