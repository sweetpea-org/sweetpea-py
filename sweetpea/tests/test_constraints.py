import operator as op
import pytest

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.constraints import Consistency, FullyCross, Derivation, NoMoreThanKInARow, Forbid
from sweetpea.backend import LowLevelRequest, BackendRequest
from sweetpea.logic import And, Or, Iff, to_cnf_tseitin


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

design = [color, text, con_factor]
crossing = [color, text]
block = fully_cross_block(design, crossing, [])


def test_consistency():
    backend_request = BackendRequest(0)

    # From standard example
    # [ LowLevelRequest("EQ", 1, [1, 2]), LowLevelRequest("EQ", 1, [3, 4]), ...]
    backend_request.ll_requests.clear()

    Consistency.apply(block, backend_request)
    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1]), range(1, 24, 2)))

    # Different case
    backend_request.ll_requests.clear()
    f = Factor("a", ["b", "c", "d", "e"])
    f_block = fully_cross_block([f], [f], [])

    Consistency.apply(f_block, backend_request)
    assert backend_request.ll_requests == \
        list(map(lambda x: LowLevelRequest("EQ", 1, [x, x+1, x+2, x+3]), range(1, 16, 4)))

    # Varied level lengths
    backend_request.ll_requests.clear()
    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_block = fully_cross_block([f1, f2], [f1, f2], [])

    Consistency.apply(f_block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [1, 2, 3]), LowLevelRequest("EQ", 1, [4]),
        LowLevelRequest("EQ", 1, [5, 6, 7]), LowLevelRequest("EQ", 1, [8]),
        LowLevelRequest("EQ", 1, [9, 10, 11]), LowLevelRequest("EQ", 1, [12])]


def test_fully_cross():
    (expected_cnf, _) = to_cnf_tseitin(And([
        Iff(25, And([1,  3 ])), Iff(26, And([1,  4 ])), Iff(27, And([2,  3 ])), Iff(28, And([2,  4 ])),
        Iff(29, And([7,  9 ])), Iff(30, And([7,  10])), Iff(31, And([8,  9 ])), Iff(32, And([8,  10])),
        Iff(33, And([13, 15])), Iff(34, And([13, 16])), Iff(35, And([14, 15])), Iff(36, And([14, 16])),
        Iff(37, And([19, 21])), Iff(38, And([19, 22])), Iff(39, And([20, 21])), Iff(40, And([20, 22]))
    ]), 41)

    backend_request = BackendRequest(25)
    FullyCross.apply(block, backend_request)

    assert backend_request.fresh == 74
    assert backend_request.cnfs == [expected_cnf]
    assert backend_request.ll_requests == [
        LowLevelRequest("EQ", 1, [25, 29, 33, 37]),
        LowLevelRequest("EQ", 1, [26, 30, 34, 38]),
        LowLevelRequest("EQ", 1, [27, 31, 35, 39]),
        LowLevelRequest("EQ", 1, [28, 32, 36, 40])
    ]


def test_derivation():
    # Congruent derivation
    d = Derivation(4, [[0, 2], [1, 3]])
    backend_request = BackendRequest(24)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(5,  Or([And([1,  3 ]), And([2,  4 ])])),
        Iff(11, Or([And([7,  9 ]), And([8,  10])])),
        Iff(17, Or([And([13, 15]), And([14, 16])])),
        Iff(23, Or([And([19, 21]), And([20, 22])]))
    ]), 24)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]

    # Incongruent derivation
    d = Derivation(5, [[0, 3], [1, 2]])
    backend_request = BackendRequest(24)
    d.apply(block, backend_request)

    (expected_cnf, expected_fresh) = to_cnf_tseitin(And([
        Iff(6,  Or([And([1,  4 ]), And([2,  3 ])])),
        Iff(12, Or([And([7,  10]), And([8,  9 ])])),
        Iff(18, Or([And([13, 16]), And([14, 15])])),
        Iff(24, Or([And([19, 22]), And([20, 21])]))
    ]), 24)

    assert backend_request.fresh == expected_fresh
    assert backend_request.cnfs == [expected_cnf]


def test_nomorethankinarow():
    c = NoMoreThanKInARow(1, ("color", "red"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [1,  7 ]),
        LowLevelRequest("LT", 2, [7,  13]),
        LowLevelRequest("LT", 2, [13, 19])
    ]

    c = NoMoreThanKInARow(2, ("color", "red"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 3, [1, 7,  13]),
        LowLevelRequest("LT", 3, [7, 13, 19])
    ]

    c = NoMoreThanKInARow(1, ("color", "blue"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 2, [2,  8 ]),
        LowLevelRequest("LT", 2, [8,  14]),
        LowLevelRequest("LT", 2, [14, 20])
    ]

    c = NoMoreThanKInARow(2, ("color", "blue"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 3, [2, 8,  14]),
        LowLevelRequest("LT", 3, [8, 14, 20])
    ]

    c = NoMoreThanKInARow(3, ("congruent?", "con"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 4, [5, 11, 17, 23])
    ]

    c = NoMoreThanKInARow(0, ("congruent?", "con"))
    backend_request = BackendRequest(0)
    c.apply(block, backend_request)
    assert backend_request.ll_requests == [
        LowLevelRequest("LT", 1, [5]),
        LowLevelRequest("LT", 1, [11]),
        LowLevelRequest("LT", 1, [17]),
        LowLevelRequest("LT", 1, [23])
    ]


def test_forbid():
    f = Forbid(("color", "red"))
    backend_request = BackendRequest(0)
    f.apply(block, backend_request)
    assert backend_request.cnfs == [And([-1, -7, -13, -19])]

    f = Forbid(("congruent?", "con"))
    backend_request = BackendRequest(0)
    f.apply(block, backend_request)
    assert backend_request.cnfs == [And([-5, -11, -17, -23])]