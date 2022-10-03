# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea import (
    Factor, DerivedLevel, WithinTrial,
    MultiCrossBlock, synthesize_trials, print_experiments,
    CMSGen
)

"""
Multiple Crossing Task (Multi-component vector matching)
******************************
factors (levels):
- left (0000, 0001 ......, 1111)
- right (0000, 0001 ......, 1111)
- congruent stimilus (congruent, incongruent): Factor dependent on first and second letter of left and right.
- congruent context (congruent, incongruent): Factor dependent on third and fourth letter of left and right.
- four_case (stimulus, context)

design:
- counterbalancing left x four_case x right

"""

# DEFINE FOUR FACTORS

left    = Factor("left", ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"])
right    = Factor("right", ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"])

# ALL POSSIBLE COMBINATIONS


# DEFINE CONGRUENCY FACTOR

def congruent_stimulus(left, right):
    return left[0] == right[0] and left[1] == right[1]

def incongruent_stimulus(left, right):
    return not congruent_stimulus(left, right)

cong_stimulus = DerivedLevel("cong_stimulus", WithinTrial(congruent_stimulus, [left, right]))
incong_stimulus = DerivedLevel("incong_stimulus", WithinTrial(incongruent_stimulus, [left, right]))

stimulus = Factor("stimulus", [
    cong_stimulus,
    incong_stimulus
])

# DEFINE CONGRUENCY FACTOR

def congruent_context(left, right):
    return left[2] == right[2] and left[3] == right[3]

def incongruent_context(left, right):
    return not congruent_context(left, right)


cong_context = DerivedLevel("cong_context", WithinTrial(congruent_context, [left, right]))
incong_context = DerivedLevel("incong_context", WithinTrial(incongruent_context, [left, right]))

context = Factor("context", [
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

four_case = Factor("four_case", [
    DerivedLevel("con_con", WithinTrial(con_con, [left, right])),
    DerivedLevel("con_inc", WithinTrial(con_inc, [left, right])),
    DerivedLevel("inc_inc", WithinTrial(inc_inc, [left, right])),
    DerivedLevel("inc_con", WithinTrial(inc_con, [left, right]))
])

# DEFINE SEQUENCE CONSTRAINTS

constraints = []

# DEFINE EXPERIMENT

design       = [left, right, four_case]
crossing     = [[left, four_case], [right,four_case]]
block        = MultiCrossBlock(design, crossing, constraints)

# SOLVE

experiments  = synthesize_trials(block, 1, CMSGen)

print_experiments(block, experiments)
