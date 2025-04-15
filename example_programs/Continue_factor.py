from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ContinuousConstraint, ContinuousFactor,
    UniformDistribution, GaussianDistribution, 
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)
import random

def sample_continuous():
    return random.uniform(0.5, 1.5)  # Response times between 0.5 and 1.5 seconds

completion_time = ContinuousFactor("completion_time", distribution=LogNormalDistribution(0, 1))
response_time = ContinuousFactor("response_time", distribution=CustomDistribution(sample_continuous))

def difference(t1, t2):
    return t1-t2
difference_time = ContinuousFactor("difference_time", distribution=CustomDistribution(difference, [completion_time, response_time]))

difference_time2 = ContinuousFactor("difference_time2", distribution=CustomDistribution(lambda t2: difference(1.5, t2), [response_time]))

difference_time3 = ContinuousFactor("difference_time3", distribution=CustomDistribution(difference, [difference_time, difference_time2]))

color      = Factor("color",  ["red", "blue", "green"])

# # Create the experimental design using the factors
design = [color, completion_time, response_time, \
            difference_time, difference_time2, difference_time3]

crossing = [color]

# Modify this to see the messages when continuous constraints cannot be met.
def test_function(a, b):
    return (a+b>3)

cc = ContinuousConstraint([difference_time3, difference_time], test_function)
constraints = [MinimumTrials(5), cc]

block        = CrossBlock(design, crossing, constraints)
experiments  = synthesize_trials(block, 2, CMSGen)

print_experiments(block, experiments)



