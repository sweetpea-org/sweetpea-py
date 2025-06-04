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

reward = ContinuousFactor("reward", distribution=CustomDistribution(sample_continuous))

# DW: Currently stride has not been implemented yet
# Derived ContinuousFactor that computes the difference between 
# current trial and the previous trial for another factor using ContinuousFactorWindow

print('Difference between current trial of previous trial for reward')
def difference(factor1):
    return  factor1[0]-factor1[-1]

reward_diff = ContinuousFactor("reward_diff", \
            distribution=CustomDistribution(difference, [ContinuousFactorWindow([reward], 2, 1)]))

design = [color, text, reward, reward_diff]
crossing = [color, text]
constraints = [MinimumTrials(10)]

block        = CrossBlock(design, crossing, constraints)
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)

