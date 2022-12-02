import operator as op
import pytest

from itertools import permutations

from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea._internal.constraint import AtMostKInARow, Derivation, Reify
from sweetpea._internal.derivation_processor import DerivationProcessor
from sweetpea._internal.block import Block
from sweetpea import CrossBlock


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])

text_repeats_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(lambda texts: texts[0] == texts[-1], [text])),
    DerivedLevel("no",  Transition(lambda texts: texts[0] != texts[-1], [text]))
])

congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", Window(lambda color, text: color == text, [color, text], 1, 3)),
    DerivedLevel("no",  Window(lambda color, text: color != text, [color, text], 1, 3))
])

design = [color, text, con_factor]
crossing = [color, text]
blk = CrossBlock(design, crossing, [Reify(con_factor)])


def two_con(i, n, t):
    return (i == "1" and n == "I" and t == "two") or \
        (i == "1" and n == "II" and t == "one") or \
        (i == "2" and n == "I" and t == "one") or \
        (i == "2" and n == "I" and t == "two") or \
        (i == "2" and n == "II" and t == "one") or \
        (i == "1" and n == "II" and t == "two")

def two_not_con(i, n, t):
    return not two_con(i, n, t)


def test_generate_derivations_should_raise_error_if_fn_doesnt_return_a_boolean():
    def local_eq(color, text):
            color == text # Notice the missing return stmt

    local_con_factor = Factor("congruent?", [
        DerivedLevel("con", WithinTrial(local_eq, [color, text])),
        DerivedLevel("inc", WithinTrial(lambda c, t: not local_eq(c, t), [color, text]))
    ])

    with pytest.raises(ValueError):
        CrossBlock([color, text, local_con_factor],
                   [color, text],
                   [Reify(local_con_factor)])

def test_generate_derivations_should_raise_error_if_some_factor_matches_multiple_levels():
    local_con_factor = Factor("congruent?", [
        DerivedLevel("con", WithinTrial(op.eq, [color, text])),
        DerivedLevel("inc", WithinTrial(op.eq, [color, text]))
    ])

    with pytest.raises(ValueError):
        CrossBlock([color, text, local_con_factor],
                   [color, text],
                   [Reify(local_con_factor)])

def test_generate_derivations_should_produce_warning_if_some_level_is_unreachable(capsys):
    local_con_factor = Factor("congruent?", [
        DerivedLevel("con", WithinTrial(op.eq, [color, text])),
        DerivedLevel("inc", WithinTrial(op.ne, [color, text])),
        DerivedLevel("dum", WithinTrial(lambda c, t: c=='green', [color, text]))
    ])
    block = CrossBlock([color, text, local_con_factor],
                       [color, text],
                       [Reify(local_con_factor)])
    block.show_errors()
    assert capsys.readouterr().out == "WARNING: No matches to the factor 'congruent?' predicate for level\n 'dum'.\n"

def test_generate_derivations_within_trial():
    assert DerivationProcessor.generate_derivations(blk) == [
        Derivation(4, [[0, 2], [1, 3]], con_factor),
        Derivation(5, [[0, 3], [1, 2]], con_factor)]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])

    twoConLevel = DerivedLevel("twoCon", WithinTrial(two_con, [integer, numeral, text]))
    twoNotConLevel = DerivedLevel("twoNotCon", WithinTrial(two_not_con, [integer, numeral, text]))
    two_con_factor = Factor("twoCon?", [twoConLevel, twoNotConLevel])

    one_two_design = [integer, numeral, text, two_con_factor]
    one_two_crossing = [integer, numeral, text]

    assert DerivationProcessor.generate_derivations(
        CrossBlock(one_two_design, one_two_crossing, list(map(Reify, one_two_design)))) == [
        Derivation(6, [[0, 2, 5], [0, 3, 4], [0, 3, 5], [1, 2, 4], [1, 2, 5], [1, 3, 4]], two_con_factor),
        Derivation(7, [[0, 2, 4], [1, 3, 5]], two_con_factor)]


@pytest.mark.parametrize('design',
    [[color, text, color_repeats_factor],
     [color, color_repeats_factor, text],
     [color_repeats_factor, color, text]])
def test_generate_derivations_transition(design):
    block = CrossBlock(design, [color, text], list(map(Reify, design)))

    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [[0, 4], [1, 5]], color_repeats_factor),
        Derivation(17, [[0, 5], [1, 4]], color_repeats_factor)
    ]


@pytest.mark.parametrize('design',
    [[color, text, color_repeats_factor, text_repeats_factor],
     [color, color_repeats_factor, text_repeats_factor, text],
     [color_repeats_factor, color, text_repeats_factor, text],
     [color_repeats_factor, text_repeats_factor, color, text]])
def test_generate_derivations_with_multiple_transitions(design):
    block = CrossBlock([color, text, color_repeats_factor, text_repeats_factor],
                       [color, text],
                       [Reify(color_repeats_factor), Reify(text_repeats_factor)])

    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [[0, 4], [1, 5]], color_repeats_factor),
        Derivation(17, [[0, 5], [1, 4]], color_repeats_factor),
        Derivation(22, [[2, 6], [3, 7]], text_repeats_factor),
        Derivation(23, [[2, 7], [3, 6]], text_repeats_factor)
    ]


def test_generate_derivations_with_window():
    block = CrossBlock([color, text, congruent_bookend], [color, text], [Reify(congruent_bookend)])

    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [[0, 2], [1, 3]], congruent_bookend),
        Derivation(17, [[0, 3], [1, 2]], congruent_bookend)
    ]


def test_generate_argument_list_with_within_trial():
    x_product = con_level.get_dependent_cross_product()

    assert DerivationProcessor.generate_argument_list(con_level, x_product[0]) == ['red', 'red']
    assert DerivationProcessor.generate_argument_list(con_level, x_product[1]) == ['red', 'blue']
    assert DerivationProcessor.generate_argument_list(con_level, x_product[2]) == ['blue', 'red']
    assert DerivationProcessor.generate_argument_list(con_level, x_product[3]) == ['blue', 'blue']


def test_generate_argument_list_with_transition():
    color_repeats_level = DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color]))
    x_product = color_repeats_level.get_dependent_cross_product()

    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[0]) == [{-1: 'red', 0: 'red'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[1]) == [{-1: 'red', 0: 'blue'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[2]) == [{-1: 'blue', 0: 'red'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[3]) == [{-1: 'blue', 0: 'blue'}]

    double_repeat_level = DerivedLevel("name", Transition(lambda colors, texts: True, [color, text]))
    x_product = double_repeat_level.get_dependent_cross_product()

    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[0]) == [{-1: 'red', 0: 'red'}, {-1: 'red', 0: 'red'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[1]) == [{-1: 'red', 0: 'red'}, {-1: 'red', 0: 'blue'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[2]) == [{-1: 'red', 0: 'red'}, {-1: 'blue', 0: 'red'}]
    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[3]) == [{-1: 'red', 0: 'red'}, {-1: 'blue', 0: 'blue'}]

    assert DerivationProcessor.generate_argument_list(color_repeats_level, x_product[15]) == [{-1: 'blue', 0: 'blue'}, {-1: 'blue', 0: 'blue'}]


def test_shift_window():
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], WithinTrial(lambda x: x, [color]), 0) == [[0, 0], [1, 1]]
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], Transition(lambda x: x, [color]), 4) == [[0, 4], [1, 5]]
    assert DerivationProcessor.shift_window([[0, 2, 4], [1, 3, 5]], Window(lambda x: x, [color], 2, 3), 6) == [[0, 8, 16], [1, 9, 17]]
    assert DerivationProcessor.shift_window([[1, 1, 1, 1], [2, 2, 2, 2]], Window(lambda x: x, [color], 2, 4), 10) == \
        [[1, 11, 21, 31], [2, 12, 22, 32]]
