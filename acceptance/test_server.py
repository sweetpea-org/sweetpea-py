import operator as op
import pytest

from sweetpea.docker import start_docker_container, stop_docker_container
from sweetpea.primitives import factor, derived_level, within_trial, transition
from sweetpea.constraints import at_most_k_in_a_row, exactly_k_in_a_row, exclude
from sweetpea.server import build_cnf, is_cnf_still_sat
from sweetpea.logic import And
from sweetpea import fully_cross_block


# Basic setup
color_list = ["red", "blue"]
color = factor("color", color_list)
text  = factor("text",  color_list)

# Congruent factor
con_level  = derived_level("con", within_trial(op.eq, [color, text]))
inc_level  = derived_level("inc", within_trial(op.ne, [color, text]))
con_factor = factor("congruent?", [con_level, inc_level])

block = fully_cross_block([color, text, con_factor], [color, text], [])


def test_is_cnf_still_sat_should_respond_correctly():
    container = start_docker_container("sweetpea/server", 8080)

    try:
        cnf_result = build_cnf(block)
    
        # Build the CNF on the server.
        cnf_result = build_cnf(block)
        cnf_id = cnf_result['id']

        assert     is_cnf_still_sat(cnf_id, [And([1, 3])])

        assert not is_cnf_still_sat(cnf_id, [And([7, 8])])
        assert not is_cnf_still_sat(cnf_id, [And([1, 7, 13])])
    finally:
        stop_docker_container(container)
