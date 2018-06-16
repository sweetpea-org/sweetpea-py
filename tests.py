# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#          yay, testing! run: `pytest tests.py`
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from FrontEnd import *
import operator as op


def test_get_all_level_names():
    color = Factor("color", ["red", "blue"])
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
    assert cnfToStr(And([1])) == "1 0\n"
    assert cnfToStr(And([Not(5)])) == "-5 0\n"
    assert cnfToStr(Or([1, 2, Not(4)])) == "1 2 -4"

    assert cnfToStr(And([Or([1, 4]), Or([5, -4, 2]), Or([-1, -5])])) == "\n".join([
        "1 4 0",
        "5 -4 2 0",
        "-1 -5 0\n"])

    assert cnfToStr(And([
        Or([1, 3, Not(2)]),
        Or([1, 3, 5]),
        Or([1, 4, Not(2)]),
        Or([1, 4, 5]),
        Or([2, 3, 1, 5]),
        Or([2, 4, 1, 5])])) == "\n".join([
        "1 3 -2 0",
        "1 3 5 0",
        "1 4 -2 0",
        "1 4 5 0",
        "2 3 1 5 0",
        "2 4 1 5 0\n"])


# done
def test_fullycrosssize():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red"])
    size  = Factor("size",  ["big", "small", "tiny"])
    assert fully_cross_size([color, color]) == 4
    assert fully_cross_size([color, color, color]) == 8
    assert fully_cross_size([size, text]) == 3
    assert fully_cross_size([size, color]) == 6
    assert fully_cross_size([text]) == 1

# needs more tests
def test_get_depxProduct():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
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

def test_etc():
    assert None == None
