
import operator as op

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]

k = 1
constraints = [NoMoreThanKInARow(k, ("congruent?", "con"))]

crossing     = [color, text]
block        = fullyCrossBlock(design, crossing, constraints)
experiment   = [block]
(nVars, cnf) = synthesizeTrials(experiment)
