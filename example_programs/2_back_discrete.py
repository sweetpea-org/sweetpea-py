from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ContinuousConstraint, ContinuousFactor,
    UniformDistribution, GaussianDistribution, Window,
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)
import random

stimuli = Factor("color", ["red", "blue", "green"])

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

design = [stimuli, target, lure]
crossing = [stimuli, target]
constraints = [MinimumTrials(10)]

block        = CrossBlock(design, crossing, constraints)
experiments  = synthesize_trials(block, 1, CMSGen)
print_experiments(block, experiments)
