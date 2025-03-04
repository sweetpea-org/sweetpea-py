from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ConstinuousConstraint
)

import math
import random

###  Create a ContinuousFactor
# ContinuousFactor can be defined with either a sampling function 
# or a sampling method (uniform, gaussian, exponential, lognormal)

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


color_time = Factor("color_time", [
    color], sampling_function=color2time)

color_word_time = Factor("color_word_time", [
    color, word], sampling_function=color_word)

design = [color, word, color_time, color_word_time]

crossing = [color, word]

constraints = [MinimumTrials(5)]

block        = CrossBlock(design, crossing, constraints)

experiments  = synthesize_trials(block, 2, CMSGen)

print_experiments(block, experiments)



