import operator as op

from sweetpea import *


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design = [color, text, conFactor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [])


def test_get_dep_x_product():
    assert DerivationProcessor.get_dep_x_product(conLevel) == [
        (('color', 'red'), ('text', 'red')),
        (('color', 'red'), ('text', 'blue')),
        (('color', 'blue'), ('text', 'red')),
        (('color', 'blue'), ('text', 'blue'))]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])
    twoConLevel = DerivedLevel("twoCon", WithinTrial(lambda x: x, [integer, numeral, text]))
    assert DerivationProcessor.get_dep_x_product(twoConLevel) == [
        (('integer', '1'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'two'))]


def test_get_derived_factors():
    assert DerivationProcessor.get_derived_factors(design) == [conFactor]


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
    assert DerivationProcessor.generate_derivations(blk) == [
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

    assert DerivationProcessor.generate_derivations(
        FullyCrossBlock(one_two_design, one_two_crossing, [])) == [
        Derivation(6, [[0, 2, 5], [0, 3, 4], [0, 3, 5], [1, 2, 4], [1, 2, 5], [1, 3, 4]]),
        Derivation(7, [[0, 2, 4], [1, 3, 5]])]


def test_shift_window():
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], WithinTrial(lambda x: x, None), 0) == [[0, 0], [1, 1]]
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], Transition(lambda x: x, None), 4) == [[0, 4], [1, 5]]
    assert DerivationProcessor.shift_window([[0, 2, 4], [1, 3, 5]], Window(lambda x: x, None, 3), 6) == [[0, 8, 16], [1, 9, 17]]
    assert DerivationProcessor.shift_window([[1, 1, 1, 1], [2, 2, 2, 2]], Window(lambda x: x, None, 4), 10) == \
        [[1, 11, 21, 31], [2, 12, 22, 32]]