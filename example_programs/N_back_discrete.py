from sweetpea import (
    Factor, DerivedLevel, WithinTrial, Transition, AtMostKInARow, MinimumTrials,
    CrossBlock, MultiCrossBlock, synthesize_trials, print_experiments, tabulate_experiments,
    CMSGen, IterateGen, RandomGen, ContinuousConstraint, ContinuousFactor, ContinuousWindow,
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
    if len(stimuli) == 2:
        return stimuli[0]==stimuli[-1]
    elif len(stimuli) == 3:
        return (stimuli[0]!=stimuli[-2]) and (stimuli[0]==stimuli[-1])
    elif stimuli[0]==stimuli[-2]:
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

# text  = Factor("text",  ["red", "blue"])

# def sample_continuous():
#     return random.uniform(0.5, 1.5)  # Response times between 0.5 and 1.5 seconds

# response_time = ContinuousFactor("response_time", distribution=CustomDistribution(sample_continuous))

# # DW: Currently stride has not been implemented yet
# # Derived ContinuousFactor that computes the difference between 
# # current trial and the previous trial for another factor using ContinuousWindow

# print('Difference between current trial of previous trial for response time')
# def difference(factor1):
#     return  factor1[0]-factor1[-1]

# window_diff = ContinuousFactor("window_diff", \
#             distribution=CustomDistribution(difference, [ContinuousWindow([response_time], 2, 1)]))

# design = [color, text, response_time, window_diff]
# crossing = [color, text]
# constraints = [MinimumTrials(10)]

# block        = CrossBlock(design, crossing, constraints)
# experiments  = synthesize_trials(block, 1, CMSGen)
# print_experiments(block, experiments)

# # Derived ContinuousFactor that computes the addition of the previous trials 
# # of two factors defined by ContinuousWindow
# # current trial and the previous trial for another factor

# print('Sum of previous trial of response_time and trial value of window_diff two trials before')

# def compute_sum(factor1, factor2):
#     return factor1[-1] + factor2[-2]

# factor_add = ContinuousFactor("factor_add", \
#             distribution=CustomDistribution(compute_sum, [ContinuousWindow([response_time], 2, 1), ContinuousWindow([window_diff], 3, 1)]))

# design = [color, text, response_time, window_diff, factor_add]
# crossing = [color, text]
# constraints = [MinimumTrials(10)]

# block        = CrossBlock(design, crossing, constraints)
# experiments  = synthesize_trials(block, 1, CMSGen)
# print_experiments(block, experiments)


# print('If a ContinuousWindow is constructed with more than one factor, \
# User need to modify distribution function accordingly')

# def custom_add(factors, factor2):
#     response_time= factors[0]
#     window_diff= factors[1]
#     return response_time[-1]+window_diff[-1]+factor2[-2]


# window_multiple_factor = ContinuousFactor("window_multiple_factor", \
#             distribution=CustomDistribution(custom_add, \
#             [ContinuousWindow([response_time, window_diff], 2, 1), \
#             ContinuousWindow([factor_add], 3, 1)]))

# design = [color, text, response_time, window_diff, factor_add, window_multiple_factor]
# crossing = [color, text]
# constraints = [MinimumTrials(10)]

# block        = CrossBlock(design, crossing, constraints)
# experiments  = synthesize_trials(block, 1, CMSGen)
# print_experiments(block, experiments)

# # Derived ContinuousFactor that computes the cumulative sum of the other factor
# print("Derived ContinuousFactor that computes the cumulative sum of the other factor")
# response_time_sum = ContinuousFactor("response_time_sum", \
# distribution=CustomDistribution(lambda x:x, [response_time], cumulative=True))

# design = [color, text, response_time, response_time_sum]
# crossing = [color, text]
# constraints = [MinimumTrials(10)]#, cc]

# block        = CrossBlock(design, crossing, constraints)
# experiments  = synthesize_trials(block, 2, CMSGen)
# print_experiments(block, experiments)
