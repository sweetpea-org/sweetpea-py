import operator as op
import pytest

from sweetpea import Factor, DerivedLevel, WithinTrial, CrossBlock
from sweetpea._internal.server import build_cnf, is_cnf_still_sat
from sweetpea._internal.logic import And
from sweetpea._internal.constraint import Reify
from acceptance import path_to_cnf_files, reset_expected_solutions


# Basic setup
color_list = ["red", "blue"]
color = Factor("color", color_list)
text  = Factor("text",  color_list)

# Congruent Factor
con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

block = CrossBlock([color, text, con_factor], [color, text], [Reify(con_factor)])


def test_is_cnf_still_sat_should_respond_correctly():

    # Build the CNF on the server.
    cnf_result = build_cnf(block)

    if reset_expected_solutions:
        with open(path_to_cnf_files+'/test_is_cnf_still_sat_should_respond_correctly.cnf', 'w') as f:
            f.write(cnf_result.as_unigen_string())
    with open(path_to_cnf_files+'/test_is_cnf_still_sat_should_respond_correctly.cnf', 'r') as f:
        old_cnf = f.read()

    assert old_cnf == cnf_result.as_unigen_string()

    assert     is_cnf_still_sat(block, [And([1, 3])])

    assert not is_cnf_still_sat(block, [And([7, 8])])
    assert not is_cnf_still_sat(block, [And([1, 7, 13])])
