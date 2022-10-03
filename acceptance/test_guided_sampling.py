import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row
from sweetpea.sampling_strategies.guided import GuidedSamplingStrategy
from sweetpea import fully_cross_block, synthesize_trials

# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent Factor
con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

design      = [color, text, con_factor]
crossing    = [color, text]
constraints = []

block = fully_cross_block(design, crossing, constraints)


def test_guided_sampling_works():
    trials = synthesize_trials(block, 5, sampling_strategy=GuidedSamplingStrategy)

    assert len(trials) == 5
