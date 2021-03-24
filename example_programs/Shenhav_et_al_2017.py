# Make SweetPea visible regardless of whether it's been installed.
import sys
sys.path.append("..")

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import no_more_than_k_in_a_row
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments
import numpy as np
import psyneulink as pnl

# GENERATING EXPERIMENT SEQUENCE FOR AN EXPERIMENT BLOCK IN SHENHAV ET AL. 2017

"""
Shenhav et al., 2017
******************************
factors (levels):
- dominant color (red, blue)
- dominant motion (up, down)
- coherence of colors (0.3 0.53, 0.76, 1.0)
- coherence of motion (0.3 0.53, 0.76, 1.0)
- response color (-1, 1)
- response motion (-1, 1)
- congruency (congruent, incongruent): factor dependent on dominant color and dominant motion.

design:
- counterbalancing dominant color x dominant motion x color coherence x motion coherence

"""

print("GENERATING EXPERIMENT SEQUENCE WITH SWEETPEA...")

# DEFINE STIMULUS FACTORS

colorCoherence      = factor("color coherence",  ["0.3", "0.53", "0.76", "1.0"])
motionCoherence     = factor("motion coherence", ["0.3", "0.53", "0.76", "1.0"])
color      = factor("color direction", ["red", "blue"])
motion      = factor("motion direction", ["up", "down"])

# DEFINE RESPONSE FACTORS

def leftResponse(stimulusDimension):
    return (stimulusDimension == "red" or stimulusDimension == "up")

def rightResponse(stimulusDimension):
    return (stimulusDimension == "blue" or stimulusDimension == "down")

leftColorResponseLevel = derived_level("-1", within_trial(leftResponse,   [color]))
rightColorResponseLevel = derived_level("1", within_trial(rightResponse,   [color]))

leftMotionResponseLevel = derived_level("-1", within_trial(leftResponse,   [motion]))
rightMotionResponseLevel = derived_level("1", within_trial(rightResponse,   [motion]))

colorResponse = factor("correct color response", [
    leftColorResponseLevel,
    rightColorResponseLevel
])

motionResponse = factor("correct motion response", [
    leftMotionResponseLevel,
    rightMotionResponseLevel
])


# DEFINE CONGRUENCY FACTOR

def congruent(colorResponse, motionResponse):
    return colorResponse == motionResponse

def incongruent(colorResponse, motionResponse):
    return not congruent(colorResponse, motionResponse)


conLevel = derived_level("con", within_trial(congruent,   [colorResponse, motionResponse]))
incLevel = derived_level("inc", within_trial(incongruent,   [colorResponse, motionResponse]))

congruency = factor("congruency", [
    conLevel,
    incLevel
])

# DEFINE SEQUENCE CONSTRAINTS

k = 7
constraints = []

# DEFINE EXPERIMENT

design       = [colorCoherence, motionCoherence, color, motion, colorResponse, motionResponse, congruency]
crossing     = [colorCoherence, motionCoherence, color, motion]
block        = fully_cross_block(design, crossing, constraints)

# SOLVE FOR EXPERIMENT SEQUENCE

experiments  = synthesize_trials_non_uniform(block, 1)

print_experiments(block, experiments)

# GENERATE MODEL INPUTS FROM EXPERIMENT SEQUENCE

colorInputSequence = np.multiply(np.asarray(experiments[0]["color coherence"]).astype(float), np.asarray(experiments[0]["correct color response"]).astype(float))
motionInputSequence = np.multiply(np.asarray(experiments[0]["motion coherence"]).astype(float), np.asarray(experiments[0]["correct motion response"]).astype(float))


# BUILD PSYNEULINK MODEL

print("SIMULATING EXPERIMENT WITH PSYNEULINK MODEL...")

optimal_color_control = 0.69
optimal_motion_control = 0.18

color_input = pnl.ProcessingMechanism(name='Color',
                                  function=pnl.Linear(slope=optimal_color_control))
motion_input = pnl.ProcessingMechanism(name='Motion',
                                  function=pnl.Linear(slope=optimal_motion_control))
# decision = pnl.DDM(name='Decision',
#                function= pnl.DriftDiffusionAnalytical(
#                        starting_point=0,
#                        noise=0.5,
#                        t0=0.2,
#                        threshold=0.45),
#                output_states=[pnl.DDM_OUTPUT.PROBABILITY_UPPER_THRESHOLD, pnl.DDM_OUTPUT.RESPONSE_TIME], this seems to have been removed.
#               )
decision = pnl.DDM(
    function=pnl.DriftDiffusionAnalytical(
        starting_point=0,
        noise=0.5,
        t0=0.2,
        threshold=0.45
    ),
    name='Decision'
)

c = pnl.Composition(name='ColorMotion Task')
c.add_linear_processing_pathway([color_input, decision])
c.add_linear_processing_pathway([motion_input, decision])

# c.show_graph(show_node_structure=ALL)

stimuli = {color_input: colorInputSequence,
              motion_input: motionInputSequence}

c.run(inputs=stimuli)
print (c.results)
