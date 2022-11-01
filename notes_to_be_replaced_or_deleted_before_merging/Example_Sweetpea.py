from time import time
import sys

sys.path.append("..")

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row, minimum_trials
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments

crossing_c = 3
crossing_t = 3
# crossing_third = 6
num_trials = crossing_c*crossing_t*2

color      = Factor("color",  list(range(crossing_c)))
text       = Factor("text", list(range(crossing_t)))
# third      = Factor("third", list(range(crossing_third)))

def response_repeat(color):
    return color[0] == color[1]

def response_switch(color):
    return not response_repeat(color)

resp_transition = Factor("response_transition", [
    DerivedLevel("repeat", Transition(response_repeat, [color])),
    DerivedLevel("switch", Transition(response_switch, [color]))
])

design       = [color, text, resp_transition]
crossing     = [color, text, resp_transition]
block        = fully_cross_block(design, crossing, [])

times = []
for i in range(1):
    start = time()
    block.complex_factors_or_constraints = True
    experiments  = synthesize_trials_non_uniform(block, 1)
    end = time()
    times += [end - start]

    print_experiments(block, experiments)
print(sum(times) / len(times))
print(times)