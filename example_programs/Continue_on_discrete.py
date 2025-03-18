from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ConstinuousConstraint, ContinuousFactor,
    UniformDistribution, GaussianDistribution, 
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)


import math
import random

###  Create a ContinuousFactor
# ContinuousFactor needs to be defined based on a distribution 

color      = Factor("color",  ["red", "blue", "green", "brown"])
word       = Factor("motion", ["red", "blue", "green", "brown"])

def color2time(color):
    if color == "red":
        return random.uniform(0, 1)
    elif color == "blue":
        return random.gauss(0, 1)
    elif color == "green":
        return -math.log(random.uniform(0, 1)) / 1
    else:
        return math.exp(random.gauss(0, 1))

def color_word(color, word):
    if color == word:
        return random.uniform(-1, 0)
    else:
        return random.uniform(0, 1)


color_time = ContinuousFactor("color_time", distribution=CustomDistribution(color2time, [color]))

color_word_time = ContinuousFactor("color_word_time", distribution=CustomDistribution(color_word, [color, word]))

design = [color, word, color_time, color_word_time]

crossing = [color, word]

constraints = [MinimumTrials(5)]

block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 2, CMSGen)

print_experiments(block, experiments)



