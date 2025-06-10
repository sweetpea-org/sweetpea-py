from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ContinuousConstraint, ContinuousFactor, ContinuousFactorWindow,
    UniformDistribution, GaussianDistribution, Window,
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)
import random

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

def sample_continuous():
    return random.uniform(0.5, 1.5)  # Response times between 0.5 and 1.5 seconds

response_time = ContinuousFactor("response_time", distribution=CustomDistribution(sample_continuous))

# Derived ContinuousFactor that computes the cumulative sum of the other factor
print("Derived ContinuousFactor that computes the cumulative sum of the other factor")
response_time_sum = ContinuousFactor("response_time_sum", \
distribution=CustomDistribution(lambda x:x, [response_time], cumulative=True))

design = [color, text, response_time, response_time_sum]
crossing = [color, text]
constraints = [MinimumTrials(10)]

block        = CrossBlock(design, crossing, constraints)
experiments  = synthesize_trials(block, 2, CMSGen)
print_experiments(block, experiments)
