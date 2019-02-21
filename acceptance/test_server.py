import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import AtMostKInARow, ExactlyKInARow, Exclude
from sweetpea.server import build_cnf, is_cnf_still_sat
from sweetpea.logic import And
from sweetpea import fully_cross_block


# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent factor
con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

block = fully_cross_block([color, text, con_factor], [color, text], [])


def test_is_cnf_still_sat_should_respond_correctly():
    # Build the CNF on the server.
    cnf_result = build_cnf(block)
    cnf_id = cnf_result['id']

    assert     is_cnf_still_sat(cnf_id, [And([1, 3])])

    assert not is_cnf_still_sat(cnf_id, [And([7, 8])])
    assert not is_cnf_still_sat(cnf_id, [And([1, 7, 13])])
