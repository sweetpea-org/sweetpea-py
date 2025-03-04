from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ConstinuousConstraint
)
import random

###  Create a ContinuousFactor
# ContinuousFactor can be defined with either a sampling function 
# or a sampling method (uniform, gaussian, exponential, lognormal)

def sample_continuous():
    return random.uniform(0.5, 1.5)  # Response times between 0.5 and 1.5 seconds

completion_time = Factor("completion_time", [], sampling_method='lognormal')
response_time = Factor("response_time", [], sampling_function=sample_continuous)

def difference(t1, t2):
    return t1-t2
difference_time = Factor("difference_time", [
    completion_time, response_time], sampling_function=difference)

difference_time2 = Factor("difference_time2", [
    1.5, response_time], sampling_function=difference)

difference_time3 = Factor("difference_time3", [
    difference_time, difference_time2], sampling_function=difference)

color      = Factor("color",  ["red", "blue", "green"])

# # Create the experimental design using the factors
design = [color, completion_time, response_time, \
            difference_time, difference_time2, difference_time3]

crossing = [color]

def test_function(a, b):
    return (a+b>2)

cc = ConstinuousConstraint([difference_time3, difference_time], test_function)
constraints = [MinimumTrials(5), cc]

block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 2, CMSGen)

print_experiments(block, experiments)



