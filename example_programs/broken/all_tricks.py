from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.constraints import NoMoreThanKInARow, AtMostKInARow
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
import operator as op

text    = Factor("text",    ["red", "blue"])
color    = Factor("color",    ["28",    "45"])
motion   = Factor("motion", ["up", "down"])
response = Factor("response", ["👈",  "👉"])

def congruent(color, motion):
    return ((color == "red") and (motion == "up")) or ((color == "blue") and (motion == "down"))

def some_func(color0, text0, color1, text1, color2):
    return None

DerivedLevel("con", WithinTrial(op.eq,          [color, text]))
DerivedLevel("con", Transition(congruent,       [color, motion]))
#DerivedLevel("con", Window(some_func, [[color, text], [color, text], [color]], 2, stride=2))

k=1 #TODO this value should change to the intended value from the writing of the original code
AtMostKInARow(k, conLevel)
Balance(congruentFactor)


# congruent   : 3 (red, red) (g, g) (b,b)
# incongruent : 6
#
# 2 of each congruent --> 6 congruent
# matches the 6 incongruent

# without rep should be a keyword
# balance which figures out the 2-to-1 ratio


weighting = Ratio ([ WithoutRep (2, conLevel),
                     WithoutRep (1, incLevel)])
# text  = Factor "text"  [Level "red", Level "blue", Level "green"]
# color = Factor "color" [Level "red", Level "blue", Level "green"]


# undersampling & oversampling

#block = weightedCrossedBlock design crossing constraints weighting

synthesizeTrials(experiment, output="psyneulink")
