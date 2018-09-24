# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#          yay, testing! run: `pytest tests.py`
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import operator as op

from sweetpea import *


# Common variables for stroop.
color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design = [color, text, conFactor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [])


def test_get_all_level_names():
    text  = Factor("text",  ["red", "blue", "green"])
    assert get_all_level_names([color, text]) == [('color', 'red'),
                                                  ('color', 'blue'),
                                                  ('text', 'red'),
                                                  ('text', 'blue'),
                                                  ('text', 'green')]

def test_toCNFRec():
    assert toCNFRec(1) == 1

    assert toCNFRec(Not(1)) == Not(1)
    assert toCNFRec(Not(Not(1))) == 1
    assert toCNFRec(Not(Not(And([1, 2])))) == And([1, 2])
    assert toCNFRec(Not(And([1, 2]))) == Or([Not(1), Not(2)])
    assert toCNFRec(Not(Or([1, 2]))) == And([Not(1), Not(2)])

    assert toCNFRec(Iff(1, 2)) == And([Or([1, Not(2)]), Or([2, Not(1)])])

    assert toCNFRec(Iff(4, Or([And([0, 2]), And([1, 3])]))) == \
        And(input_list=[
            Or(input_list=[4, Not(input=0), Not(input=2)]),
            Or(input_list=[4, Not(input=1), Not(input=3)]),
            Or(input_list=[0, 1, Not(input=4)]),
            Or(input_list=[0, 3, Not(input=4)]),
            Or(input_list=[2, 1, Not(input=4)]),
            Or(input_list=[2, 3, Not(input=4)])
        ])


def test_toCNF():
    # Simple cases
    assert toCNF(1) == And([1])
    assert toCNF(And([1, 2])) == And([1, 2])
    assert toCNF(Not(5)) == And([Not(5)])
    assert toCNF(And([5])) == And([5])
    assert toCNF(And([2, 3, 5])) == And([2, 3, 5])
    assert toCNF(Or([2])) == And([2])
    assert toCNF(Or([1, 2, 3])) == And([Or([1, 2, 3])])
    assert toCNF(Or([1, And([2]), 3])) == And([Or([1, 2, 3])])

    assert toCNF(And([Or([1, Not(2), Not(3)]), Or([Not(4), 5, 6])])) == \
        And([Or([1, Not(2), Not(3)]), Or([Not(4), 5, 6])])
    assert toCNF(Or([And([1, 2]), 3])) == And([Or([1, 3]), Or([2, 3])])

    # Collapsing
    assert toCNF(And([1, And([2])])) == And([1, 2])
    assert toCNF(And([And([1]), And([2])])) == And([1, 2])
    assert toCNF(And([And([1, 2, 3]), And([4])])) == And([1, 2, 3, 4])
    assert toCNF(And([Or([1, 2]), And([3, 4])])) == And([Or([1, 2]), 3, 4])
    assert toCNF(Or([1, Or([3, 4]), And([5, 6])])) == And([Or([1, 3, 4, 5]), Or([1, 3, 4, 6])])
    assert toCNF(Or([1, Or([3, 4]), And([5])])) == And([Or([1, 3, 4, 5])])

    # DeMorgan's laws
    assert toCNF(Not(And([1, 3]))) == And([Or([Not(1), Not(3)])])
    assert toCNF(Not(Or([1, 3]))) == And([Not(1), Not(3)])

    # Not yet in CNF
    assert toCNF(Not(Not(Not(And([1, 3]))) == And([Or([Not(1), Not(3)])])))
    assert toCNF(Or([1, And([2, 3]), 4])) == And([Or([1, 2, 4]), Or([1, 3, 4])])

    assert toCNF(Or([And([1, 2]), And([3, 4])])) == And([
        Or([1, 3]), Or([1, 4]), Or([2, 3]), Or([2, 4])])
    assert toCNF(And([Not(2), Or([1, 5])])) == And([Not(2), Or([1, 5])])

    assert toCNF(Or([And([3, 4]), And([Not(2), Or([1, 5])])])) == \
        And([
            Or([3, Not(2)]),
            Or([3, 1, 5]),
            Or([4, Not(2)]),
            Or([4, 1, 5])
        ])

    assert toCNF(Or([Or([And([1, 2]), And([3, 4])]),
                     And([Not(2), Or([1, 5])])])) == \
        And([
            Or([1, 3, Not(2)]),
            Or([1, 3, 5]),
            Or([1, 4, Not(2)]),
            Or([1, 4, 5]),
            Or([2, 3, 1, 5]),
            Or([2, 4, 1, 5])
        ])


def test_cnfToStr():
    assert cnfToJson([And([Or([1])])]) == [[1]]
    assert cnfToJson([And([Or([Not(5)])])]) == [[-5]]
    assert cnfToJson([And([Or([1, 2, Not(4)])])]) == [[1, 2, -4]]

    assert cnfToJson([And([Or([1, 4]), Or([5, -4, 2]), Or([-1, -5])])]) == [
        [1, 4],
        [5, -4, 2],
        [-1, -5]]

    assert cnfToJson([And([
        Or([1, 3, Not(2)]),
        Or([1, 3, 5]),
        Or([1, 4, Not(2)]),
        Or([1, 4, 5]),
        Or([2, 3, 1, 5]),
        Or([2, 4, 1, 5])])]) == [
            [1, 3, -2],
            [1, 3, 5],
            [1, 4, -2],
            [1, 4, 5],
            [2, 3, 1, 5],
            [2, 4, 1, 5]]


# done
def test_fullycrosssize():
    text  = Factor("text",  ["red"])
    size  = Factor("size",  ["big", "small", "tiny"])
    assert fully_cross_size([color, color]) == 4
    assert fully_cross_size([color, color, color]) == 8
    assert fully_cross_size([size, text]) == 3
    assert fully_cross_size([size, color]) == 6
    assert fully_cross_size([text]) == 1


def test_design_size():
    assert design_size([color, text]) == 4
    assert design_size([color, text, conFactor]) == 6

# needs more tests
def test_get_depxProduct():
    assert get_dep_xProduct(conLevel) == [(('color', 'red'), ('text', 'red')),
                                          (('color', 'red'), ('text', 'blue')),
                                          (('color', 'blue'), ('text', 'red')),
                                          (('color', 'blue'), ('text', 'blue'))]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])
    twoConLevel = DerivedLevel("twoCon", WithinTrial(lambda x: x, [integer, numeral, text]))
    assert get_dep_xProduct(twoConLevel) == [(('integer', '1'), ('numeral', 'I'), ('text', 'one')),
                                             (('integer', '1'), ('numeral', 'I'), ('text', 'two')),
                                             (('integer', '1'), ('numeral', 'II'), ('text', 'one')),
                                             (('integer', '1'), ('numeral', 'II'), ('text', 'two')),
                                             (('integer', '2'), ('numeral', 'I'), ('text', 'one')),
                                             (('integer', '2'), ('numeral', 'I'), ('text', 'two')),
                                             (('integer', '2'), ('numeral', 'II'), ('text', 'one')),
                                             (('integer', '2'), ('numeral', 'II'), ('text', 'two'))]


def test_encoding_variable_size():
    assert encoding_variable_size(blk.design, blk.xing) == 24


def test_get_derived_factors():
    assert get_derived_factors(design) == [conFactor]


def two_con(i, n, t):
    return (i == "1" and n == "I" and t == "two") or \
        (i == "1" and n == "II" and t == "one") or \
        (i == "2" and n == "I" and t == "one") or \
        (i == "2" and n == "I" and t == "two") or \
        (i == "2" and n == "II" and t == "one") or \
        (i == "1" and n == "II" and t == "two")

def two_not_con(i, n, t):
    return not two_con(i, n, t)

def test_process_derivations():
    assert process_derivations(design, crossing) == [
        Derivation(4, [[0, 2], [1, 3]]),
        Derivation(5, [[0, 3], [1, 2]])]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])

    twoConLevel = DerivedLevel("twoCon", WithinTrial(two_con, [integer, numeral, text]))
    twoNotConLevel = DerivedLevel("twoNotCon", WithinTrial(two_not_con, [integer, numeral, text]))
    twoConFactor = Factor("twoCon?", [twoConLevel, twoNotConLevel])

    one_two_design = [integer, numeral, text, twoConFactor]
    one_two_crossing = [integer, numeral, text]

    assert process_derivations(one_two_design, one_two_crossing) == [
        Derivation(6, [[0, 2, 5], [0, 3, 4], [0, 3, 5], [1, 2, 4], [1, 2, 5], [1, 3, 4]]),
        Derivation(7, [[0, 2, 4], [1, 3, 5]])]


def test_shift_window():
    assert shift_window([[0, 0], [1, 1]], WithinTrial(lambda x: x, None), 0) == [[0, 0], [1, 1]]
    assert shift_window([[0, 0], [1, 1]], Transition(lambda x: x, None), 4) == [[0, 4], [1, 5]]
    assert shift_window([[0, 2, 4], [1, 3, 5]], Window(lambda x: x, None, 3), 6) == [[0, 8, 16], [1, 9, 17]]
    assert shift_window([[1, 1, 1, 1], [2, 2, 2, 2]], Window(lambda x: x, None, 4), 10) == \
        [[1, 11, 21, 31], [2, 12, 22, 32]]


def test_desugar_derivation():
    # Congruent derivation
    assert desugar_derivation(Derivation(4, [[0, 2], [1, 3]]), blk) == toCNF(And([
        Iff(5,  Or([And([1,  3 ]), And([2,  4 ])])),
        Iff(11, Or([And([7,  9 ]), And([8,  10])])),
        Iff(17, Or([And([13, 15]), And([14, 16])])),
        Iff(23, Or([And([19, 21]), And([20, 22])]))
    ]))

    # Incongruent derivation
    assert desugar_derivation(Derivation(5, [[0, 3], [1, 2]]), blk) == toCNF(And([
        Iff(6,  Or([And([1,  4 ]), And([2,  3 ])])),
        Iff(12, Or([And([7,  10]), And([8,  9 ])])),
        Iff(18, Or([And([13, 16]), And([14, 15])])),
        Iff(24, Or([And([19, 22]), And([20, 21])]))
    ]))


def test_desugar_consistency():
    # From standard example
    # [ Request("EQ", 1, [1, 2]), Request("EQ", 1, [3, 4]), ...]
    assert desugar_consistency(blk) == \
        list(map(lambda x: Request("EQ", 1, [x, x+1]), range(1, 24, 2)))

    # Different case
    f = Factor("a", ["b", "c", "d", "e"])
    f_blk = fully_cross_block([f], [f], [])
    assert desugar_consistency(f_blk) == \
        list(map(lambda x: Request("EQ", 1, [x, x+1, x+2, x+3]), range(1, 16, 4)))

    # Varied level lengths
    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_blk = fully_cross_block([f1, f2], [f1, f2], [])
    assert desugar_consistency(f_blk) == [
        Request("EQ", 1, [1, 2, 3]), Request("EQ", 1, [4]),
        Request("EQ", 1, [5, 6, 7]), Request("EQ", 1, [8]),
        Request("EQ", 1, [9, 10, 11]), Request("EQ", 1, [12])]


def test_desugar_full_crossing():
    assert desugar_full_crossing(25, blk) == (41, toCNF(And([
        Iff(25, And([1,  3 ])), Iff(26, And([1,  4 ])), Iff(27, And([2,  3 ])), Iff(28, And([2,  4 ])),
        Iff(29, And([7,  9 ])), Iff(30, And([7,  10])), Iff(31, And([8,  9 ])), Iff(32, And([8,  10])),
        Iff(33, And([13, 15])), Iff(34, And([13, 16])), Iff(35, And([14, 15])), Iff(36, And([14, 16])),
        Iff(37, And([19, 21])), Iff(38, And([19, 22])), Iff(39, And([20, 21])), Iff(40, And([20, 22]))
    ])), [
        Request("EQ", 1, [25, 29, 33, 37]),
        Request("EQ", 1, [26, 30, 34, 38]),
        Request("EQ", 1, [27, 31, 35, 39]),
        Request("EQ", 1, [28, 32, 36, 40])
    ])


def test_desugar_nomorethankinarow():
    assert desugar_nomorethankinarow(1, ("color", "red"), blk) == [
        Request("LT", 1, [1,  7 ]),
        Request("LT", 1, [7,  13]),
        Request("LT", 1, [13, 19])
    ]

    assert desugar_nomorethankinarow(2, ("color", "red"), blk) == [
        Request("LT", 2, [1, 7,  13]),
        Request("LT", 2, [7, 13, 19])
    ]

    assert desugar_nomorethankinarow(1, ("color", "blue"), blk) == [
        Request("LT", 1, [2,  8 ]),
        Request("LT", 1, [8,  14]),
        Request("LT", 1, [14, 20])
    ]

    assert desugar_nomorethankinarow(2, ("color", "blue"), blk) == [
        Request("LT", 2, [2, 8,  14]),
        Request("LT", 2, [8, 14, 20])
    ]

    assert desugar_nomorethankinarow(3, ("congruent?", "con"), blk) == [
        Request("LT", 3, [5, 11, 17, 23])
    ]


def test_jsonify():
    fresh = 34
    cnfs = [And([Or([1, 2, 3])]),
            And([Or([-4, 5, -6])])]
    requests = [
        Request("EQ", 1, [5, 10, 15, 20]),
        Request("LT", 3, [1, 2, 3, 4])]

    assert jsonify(fresh, cnfs, requests) == (
            '{"fresh": 34, '
            '"cnfs": [[1, 2, 3], [-4, 5, -6]], '
            '"requests": ['
            '{"equalityType": "EQ", "k": 1, "booleanValues": [5, 10, 15, 20]}, '
            '{"equalityType": "LT", "k": 3, "booleanValues": [1, 2, 3, 4]}]}')


def test_decode():
    solution = [-1,   2,  -3,   4,   5,  -6,
                -7,   8,   9, -10, -11,  12,
                13, -14, -15,  16, -17,  18,
                19, -20,  21, -22,  23, -24]
    assert decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red',  'red'],
        'text':       ['blue', 'red',  'blue', 'red'],
        'congruent?': ['con',  'inc',  'inc',  'con']
    }

    solution = [ -1,   2, -3,   4,   5,  -6,
                  7,  -8, -9,  10, -11,  12,
                 13, -14, 15, -16,  17, -18,
                -19,  20, 21, -22, -23,  24]
    assert decode(blk, solution) == {
        'color':      ['blue', 'red',  'red', 'blue'],
        'text':       ['blue', 'blue', 'red', 'red'],
        'congruent?': ['con',  'inc',  'con', 'inc']
    }

    solution = [-1,   2,   3,  -4,  -5,   6,
                -7,   8,  -9,  10,  11, -12,
                13, -14,  15, -16,  17, -18,
                19, -20, -21,  22, -23,  24]
    assert decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red', 'red'],
        'text':       ['red',  'blue', 'red', 'blue'],
        'congruent?': ['inc',  'con',  'con', 'inc']
    }

    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_blk = fully_cross_block([f1, f2], [f1, f2], [])
    solution = [-1,  2, -3, 4,
                -1, -2,  3, 4,
                 1, -2  -3, 4]
    assert decode(f_blk, solution) == {
        'a': ['c', 'd', 'b'],
        'e': ['f', 'f', 'f']
    }


def test_desugar_with_constraint():
    constraints = [NoMoreThanKInARow(1, ("congruent?", "con"))]
    blk = fully_cross_block(design, crossing, constraints)

    # This was blowing up with an error.
    desugar(blk)


def test_desugar_with_factor_constraint():
    constraints = [NoMoreThanKInARow(1, conFactor)]
    blk = fully_cross_block(design, crossing, constraints)

    desugar(blk)


def test_desugar_with_derived_transition_levels():
    color_transition = Factor("color_transition", [
        DerivedLevel("repeat", Transition(lambda c1, c2: c1 == c2, [color, color])),
        DerivedLevel("switch", Transition(lambda c1, c2: c1 != c2, [color, color]))
    ])

    design.append(color_transition)
    constraints = [NoMoreThanKInARow(2, color_transition)]
    blk = fully_cross_block(design, crossing, constraints)

    desugar(blk)


def test_desugar_full_crossing_with_simpler_stroop():
    blk = fully_cross_block([color, text], [color, text], [])

    desugar_full_crossing(0, blk)
