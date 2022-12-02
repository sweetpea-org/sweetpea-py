import operator as op
import pytest

from itertools import permutations

from sweetpea import CrossBlock
from sweetpea._internal.block import Block
from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea._internal.constraint import Consistency, Cross, Derivation, AtMostKInARow, Reify
from sweetpea._internal.backend import LowLevelRequest, BackendRequest
from sweetpea._internal.logic import And, Or, Iff, to_cnf_tseitin


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

block = CrossBlock([congruency, color, motion, task],
                   [color, motion, task],
                   [Reify(congruency)])


def test_fully_cross_with_three_factors():
    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(65,  And([3,  5,  7 ])), Iff(66,  And([3,  5,  8 ])), Iff(67,  And([3,  6,  7 ])), Iff(68,  And([3,  6,  8 ])), Iff(69,  And([4,  5,  7 ])), Iff(70,  And([4,  5,  8 ])), Iff(71,  And([4,  6,  7 ])), Iff(72,  And([4,  6,  8 ])),
        Iff(73,  And([11, 13, 15])), Iff(74,  And([11, 13, 16])), Iff(75,  And([11, 14, 15])), Iff(76,  And([11, 14, 16])), Iff(77,  And([12, 13, 15])), Iff(78,  And([12, 13, 16])), Iff(79,  And([12, 14, 15])), Iff(80,  And([12, 14, 16])),
        Iff(81,  And([19, 21, 23])), Iff(82,  And([19, 21, 24])), Iff(83,  And([19, 22, 23])), Iff(84,  And([19, 22, 24])), Iff(85,  And([20, 21, 23])), Iff(86,  And([20, 21, 24])), Iff(87,  And([20, 22, 23])), Iff(88,  And([20, 22, 24])),
        Iff(89,  And([27, 29, 31])), Iff(90,  And([27, 29, 32])), Iff(91,  And([27, 30, 31])), Iff(92,  And([27, 30, 32])), Iff(93,  And([28, 29, 31])), Iff(94,  And([28, 29, 32])), Iff(95,  And([28, 30, 31])), Iff(96,  And([28, 30, 32])),
        Iff(97,  And([35, 37, 39])), Iff(98,  And([35, 37, 40])), Iff(99,  And([35, 38, 39])), Iff(100, And([35, 38, 40])), Iff(101, And([36, 37, 39])), Iff(102, And([36, 37, 40])), Iff(103, And([36, 38, 39])), Iff(104, And([36, 38, 40])),
        Iff(105, And([43, 45, 47])), Iff(106, And([43, 45, 48])), Iff(107, And([43, 46, 47])), Iff(108, And([43, 46, 48])), Iff(109, And([44, 45, 47])), Iff(110, And([44, 45, 48])), Iff(111, And([44, 46, 47])), Iff(112, And([44, 46, 48])),
        Iff(113, And([51, 53, 55])), Iff(114, And([51, 53, 56])), Iff(115, And([51, 54, 55])), Iff(116, And([51, 54, 56])), Iff(117, And([52, 53, 55])), Iff(118, And([52, 53, 56])), Iff(119, And([52, 54, 55])), Iff(120, And([52, 54, 56])),
        Iff(121, And([59, 61, 63])), Iff(122, And([59, 61, 64])), Iff(123, And([59, 62, 63])), Iff(124, And([59, 62, 64])), Iff(125, And([60, 61, 63])), Iff(126, And([60, 61, 64])), Iff(127, And([60, 62, 63])), Iff(128, And([60, 62, 64])),
    ]), 129)

    backend_request = BackendRequest(65)
    Cross.apply(block, backend_request)

    assert backend_request.fresh == 258
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [65, 73, 81, 89, 97,  105, 113, 121]),
        LowLevelRequest("EQ", 1, [66, 74, 82, 90, 98,  106, 114, 122]),
        LowLevelRequest("EQ", 1, [67, 75, 83, 91, 99,  107, 115, 123]),
        LowLevelRequest("EQ", 1, [68, 76, 84, 92, 100, 108, 116, 124]),
        LowLevelRequest("EQ", 1, [69, 77, 85, 93, 101, 109, 117, 125]),
        LowLevelRequest("EQ", 1, [70, 78, 86, 94, 102, 110, 118, 126]),
        LowLevelRequest("EQ", 1, [71, 79, 87, 95, 103, 111, 119, 127]),
        LowLevelRequest("EQ", 1, [72, 80, 88, 96, 104, 112, 120, 128])
    ]


def test_derivation_with_unusual_order():
    d = Derivation(0, [[4, 2], [5, 3]], congruency)
    backend_request = BackendRequest(64)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(1,  Or([And([5,  3 ]), And([6,  4 ])])),
        Iff(9,  Or([And([13, 11]), And([14, 12])])),
        Iff(17, Or([And([21, 19]), And([22, 20])])),
        Iff(25, Or([And([29, 27]), And([30, 28])])),
        Iff(33, Or([And([37, 35]), And([38, 36])])),
        Iff(41, Or([And([45, 43]), And([46, 44])])),
        Iff(49, Or([And([53, 51]), And([54, 52])])),
        Iff(57, Or([And([61, 59]), And([62, 60])])),
    ]), 64)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]
