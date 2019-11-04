import operator as op
import pytest

from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row
from sweetpea.sampling_strategies.guided import GuidedSamplingStrategy
from sweetpea import fully_cross_block, synthesize_trials
from sweetpea.tests.test_utils import get_level_from_name

# Basic setup
color_list = ["red", "blue"]
color = factor("color", color_list)
text  = factor("text",  color_list)

# Congruent factor
con_level  = derived_level("con", within_trial(op.eq, [color, text]))
inc_level  = derived_level("inc", within_trial(op.ne, [color, text]))
con_factor = factor("congruent?", [con_level, inc_level])

design      = [color, text, con_factor]
crossing    = [color, text]
constraints = []

block = fully_cross_block(design, crossing, constraints)


def test_guided_sampling_works():
    trials = synthesize_trials(block, 5, sampling_strategy=GuidedSamplingStrategy)

    assert len(trials) == 5
