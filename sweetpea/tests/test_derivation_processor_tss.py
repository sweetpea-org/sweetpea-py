import operator as op
import pytest

from itertools import permutations

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.constraints import NoMoreThanKInARow, Derivation
from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.blocks import Block
from sweetpea import fully_cross_block


color  = Factor("color",  ["red", "blue"])
motion = Factor("motion", ["up", "down"])
task   = Factor("task",   ["color", "motion"])

def color_motion_congruent(color, motion):
    return ((color == "red") and (motion == "up")) or \
           ((color == "blue") and (motion == "down"))

def color_motion_incongruent(color, motion):
    return not color_motion_congruent(color, motion)

congruency = Factor("congruency", [
    DerivedLevel("con", WithinTrial(color_motion_congruent,   [color, motion])),
    DerivedLevel("inc", WithinTrial(color_motion_incongruent, [color, motion]))
])

def response_left(task, color, motion):
    return (task == "color"  and color  == "red") or \
        (task == "motion" and motion == "up")

def response_right(task, color, motion):
    return not response_left(task, color, motion)

response = Factor("response", [
    DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
    DerivedLevel("right", WithinTrial(response_right, [task, color, motion]))
])

response_transition = Factor("response transition", [
    DerivedLevel("repeat", Transition(lambda responses: responses[0] == responses[1], [response])),
    DerivedLevel("switch", Transition(lambda responses: responses[0] != responses[1], [response]))
])


def test_generate_derivations_with_transition_that_depends_on_derived_levels():
    block = fully_cross_block([color, motion, task, response, response_transition],
                              [color, motion, task],
                              [])
    derivations = DerivationProcessor.generate_derivations(block)

    assert Derivation(64, [[6, 14], [7, 15]]) in derivations
    assert Derivation(65, [[6, 15], [7, 14]]) in derivations


def test_generate_derivations_when_derived_factor_precedes_dependencies():
    block = fully_cross_block([congruency, motion, color, task],
                              [color, motion, task],
                              [])
    derivations = DerivationProcessor.generate_derivations(block)

    assert Derivation(0, [[4, 2], [5, 3]]) in derivations
    assert Derivation(1, [[4, 3], [5, 2]]) in derivations
