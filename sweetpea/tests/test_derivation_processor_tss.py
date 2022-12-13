import operator as op
import pytest

from itertools import permutations

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea._internal.constraint import AtMostKInARow, Derivation, Reify
from sweetpea._internal.derivation_processor import DerivationProcessor
from sweetpea._internal.block import Block
from sweetpea import CrossBlock


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
    DerivedLevel("repeat", Transition(lambda responses: responses[0] == responses[-1], [response])),
    DerivedLevel("switch", Transition(lambda responses: responses[0] != responses[-1], [response]))
])


def test_generate_derivations_with_transition_that_depends_on_derived_levels():
    block = CrossBlock([color, motion, task, response, response_transition],
                       [color, motion, task],
                       [Reify(response), Reify(response_transition)])
    derivations = DerivationProcessor.generate_derivations(block)

    assert Derivation(64, [[6, 14], [7, 15]], response_transition) in derivations
    assert Derivation(65, [[6, 15], [7, 14]], response_transition) in derivations


def test_generate_derivations_when_derived_factor_precedes_dependencies():
    block = CrossBlock([congruency, motion, color, task],
                       [color, motion, task],
                       [Reify(congruency)])
    derivations = DerivationProcessor.generate_derivations(block)

    assert Derivation(0, [[4, 2], [5, 3]], congruency) in derivations
    assert Derivation(1, [[4, 3], [5, 2]], congruency) in derivations
