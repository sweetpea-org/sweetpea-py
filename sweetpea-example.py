from sweetpea import *
import operator

IQ_level = Factor("Intelligence", ["Low", "Moderately Low", "Average", "Above Average", "Genius"])
processing_time = Factor("time_val", ["Slow", "Slow", "Slow", "Fast", "Fast"])

congruentLevel = DerivedLevel("congruent", WithinTrial(operator.))

