from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ContinuousConstraint, ContinuousFactor, ContinuousFactorWindow,
    UniformDistribution, GaussianDistribution, Window,
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)
import random

colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]



stimuli = Factor("stimuli", colors)

target = Factor("target", [
    DerivedLevel("yes", Window(lambda stimuli: stimuli[0] == stimuli[-2], [stimuli], 3, 1)),
    DerivedLevel("no",  Window(lambda stimuli: stimuli[0] != stimuli[-2], [stimuli], 3, 1))
])

def islure(stimuli):
    if stimuli[0]==stimuli[-2]:
        return False
    elif stimuli[0]==stimuli[-1]:
        return True
    else:
        return stimuli[0]==stimuli[-3]
def notlure(stimuli):
    return not islure(stimuli)

lure = Factor("lure", [
    DerivedLevel("yes", Window(islure, [stimuli], 4, 1, 1)),
    DerivedLevel("no",  Window(notlure, [stimuli], 4, 1, 1))
])

sigma, tolerance = 10, 15
# sigma, tolerance = 20, 25

def continuous_color(color, sigma):
    index = colors.index(color)
    return random.gauss(index*60, sigma)%360


stimuli_continue = ContinuousFactor("stimuli_continue", distribution=CustomDistribution(lambda c: continuous_color(c, sigma), [stimuli]))

def circular_distance(h1, h2):
    return abs((h1 - h2 + 180) % 360 - 180)


def color_diff_2(factor1, tolerance):
    if circular_distance(factor1[0],factor1[-2])<=tolerance:
        return True
    elif circular_distance(factor1[0],factor1[-2])>tolerance:
        return False
    else:
        return None

target_continue = ContinuousFactor("target_continue", \
            distribution=CustomDistribution(lambda c: color_diff_2(c, tolerance), [ContinuousFactorWindow([stimuli_continue], 3, 1)]))

def is_continue_lure(factor1, tolerance):
    if circular_distance(factor1[0],factor1[-2])<=tolerance:
        return False
    elif circular_distance(factor1[0],factor1[-1])<=tolerance:
        return True
    elif circular_distance(factor1[0],factor1[-3])<=tolerance:
        return True
    elif (circular_distance(factor1[0],factor1[-1])>tolerance) or (circular_distance(factor1[0],factor1[-3])>tolerance):
        return False
    return None

lure_continue = ContinuousFactor("lure_continue", \
            distribution=CustomDistribution(lambda c: is_continue_lure(c, tolerance), [ContinuousFactorWindow([stimuli_continue], 4, 1, 1)]))

design = [stimuli, target, lure, stimuli_continue, target_continue, lure_continue]#target, lure]
crossing = [stimuli, target]#, target]
constraints = [MinimumTrials(10)]

block        = CrossBlock(design, crossing, constraints)
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)
