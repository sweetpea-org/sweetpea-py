

color    = Factor("color",    ["red", "blue"])
color    = Factor("color",    [28,    45])
response = Factor("response", ["👈",  "👉"])

DerivedLevel("con", WithinTrial(op.eq,          [color, text]))
DerivedLevel("con", Transition(congruent,       [color, motion]))
DerivedLevel("con", Window(some_func, stride=2, [[color, text], [color, text], [color]]))

def congruent(color, motion):
    return ((color == "red") && (motion == "up")) || ((color == "blue") && (motion == "down"))

def some_fun(color0, text0, color1, text1, color2):
    return None


NoMoreThanKInARow(k, conLevel)
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

block     = weightedCrossedBlock design crossing constraints weighting

synthesizeTrials(experiment, output="psyneulink")
