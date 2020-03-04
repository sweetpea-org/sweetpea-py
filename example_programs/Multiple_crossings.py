import sys
sys.path.append("..")
from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import exactly_k, exactly_k_in_a_row, exclude
from sweetpea import fully_cross_block, multiple_cross_block, synthesize_trials_non_uniform, print_experiments


"""
Multiple Crossing Task (Multi-component vector matching)
******************************
factors (levels):
- left (0000, 0001 ......, 1111)
- right (0000, 0001 ......, 1111)
- congruent stimilus (congruent, incongruent): factor dependent on first and second letter of left and right.
- congruent context (congruent, incongruent): factor dependent on third and fourth letter of left and right.
- four_case (stimulus, context)

design:
- counterbalancing left x four_case x right

"""

# DEFINE FOUR FACTORS

left    = factor("left", ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"])
right    = factor("right", ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"])

# ALL POSSIBLE COMBINATIONS


# DEFINE CONGRUENCY FACTOR

def congruent_stimulus(left, right):
    return left[0] == right[0] and left[1] == right[1]

def incongruent_stimulus(left, right):
    return not congruent_stimulus(left, right)

cong_stimulus = derived_level("cong_stimulus", within_trial(congruent_stimulus, [left, right]))
incong_stimulus = derived_level("incong_stimulus", within_trial(incongruent_stimulus, [left, right]))

stimulus = factor("stimulus", [
    cong_stimulus,
    incong_stimulus
])

# DEFINE CONGRUENCY FACTOR

def congruent_context(left, right):
    return left[2] == right[2] and left[3] == right[3]

def incongruent_context(left, right):
    return not congruent_context(left, right)


cong_context = derived_level("cong_context", within_trial(congruent_context, [left, right]))
incong_context = derived_level("incong_context", within_trial(incongruent_context, [left, right]))

context = factor("context", [
    cong_context,
    incong_context
])

def con_con(left, right):
    return congruent_stimulus(left, right) and congruent_context(left, right)

def con_inc(left, right):
    return congruent_stimulus(left, right) and not congruent_context(left, right)

def inc_inc(left, right):
    return not congruent_stimulus(left, right) and not congruent_context(left, right)

def inc_con(left, right):
    return not congruent_stimulus(left, right) and congruent_context(left, right)

four_case = factor("four_case", [
    derived_level("con_con", within_trial(con_con, [left, right])),
    derived_level("con_inc", within_trial(con_inc, [left, right])),
    derived_level("inc_inc", within_trial(inc_inc, [left, right])),
    derived_level("inc_con", within_trial(inc_con, [left, right]))    
])

# DEFINE SEQUENCE CONSTRAINTS

# constraints = [exactly_k(4, four_case)]
constraints = []

# DEFINE EXPERIMENT

design       = [left, right, four_case]
crossing     = [[left, four_case], [right,four_case]]
block        = multiple_cross_block(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials_non_uniform(block, 1)

print_experiments(block, experiments)
