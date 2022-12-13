import operator as op
import pytest

from sweetpea import *
from sweetpea._internal.sampling_strategy.guided import GuidedGen

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

block = CrossBlock(design, crossing, constraints)


def test_guided_sampling_works():
    trials = synthesize_trials(block, 5, sampling_strategy=GuidedGen)

    assert len(trials) == 5
