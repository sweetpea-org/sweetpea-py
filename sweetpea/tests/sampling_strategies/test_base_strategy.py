import operator as op
import pytest

from random import shuffle

from sweetpea.sampling_strategies.base import SamplingStrategy
from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.constraints import Reify


# Common variables for stroop.
color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("color repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

text_repeats_factor = Factor("text repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [text])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [text]))
])

congruent_bookend = Factor("congruent bookend?", [
    DerivedLevel("yes", Window(lambda color, text: color == text, [color, text], 1, 3)),
    DerivedLevel("no",  Window(lambda color, text: color != text, [color, text], 1, 3))
])

design = [color, text, con_factor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [Reify(con_factor)])


def test_decode():
    solution = [-1,   2,  -3,   4,   5,  -6,
                -7,   8,   9, -10, -11,  12,
                13, -14, -15,  16, -17,  18,
                19, -20,  21, -22,  23, -24]
    shuffle(solution)

    assert SamplingStrategy.decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red',  'red'],
        'text':       ['blue', 'red',  'blue', 'red'],
        'congruent?': ['con',  'inc',  'inc',  'con']
    }

    solution = [ -1,   2, -3,   4,   5,  -6,
                  7,  -8, -9,  10, -11,  12,
                 13, -14, 15, -16,  17, -18,
                -19,  20, 21, -22, -23,  24]
    shuffle(solution)

    assert SamplingStrategy.decode(blk, solution) == {
        'color':      ['blue', 'red',  'red', 'blue'],
        'text':       ['blue', 'blue', 'red', 'red'],
        'congruent?': ['con',  'inc',  'con', 'inc']
    }

    solution = [-1,   2,   3,  -4,  -5,   6,
                -7,   8,  -9,  10,  11, -12,
                13, -14,  15, -16,  17, -18,
                19, -20, -21,  22, -23,  24]
    shuffle(solution)

    assert SamplingStrategy.decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red', 'red'],
        'text':       ['red',  'blue', 'red', 'blue'],
        'congruent?': ['inc',  'con',  'con', 'inc']
    }

    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_blk = fully_cross_block([f1, f2], [f1, f2], [])
    solution = [-1,   2,  -3, 4,
                -5,  -6,   7, 8,
                 9, -10  -11, 12]
    shuffle(solution)

    assert SamplingStrategy.decode(f_blk, solution) == {
        'a': ['c', 'd', 'b'],
        'e': ['f', 'f', 'f']
    }


def test_decode_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [Reify(color_repeats_factor)])

    solution = [ 1,  -2,  3,  -4,
                 5,  -6, -7,   8,   #  17, -18
                -9,  10,  11, -12,  # -19,  20
                -13, 14, -15,  16,  #  21, -22
                17, -18, -19, 20, 21, -22] # color_repeats_factor
    shuffle(solution)

    decoded = SamplingStrategy.decode(block, solution)
    assert decoded['color'] ==          ['red', 'red',  'blue', 'blue']
    assert decoded['text']  ==          ['red', 'blue', 'red',  'blue']
    assert decoded['color repeats?'] == ['',    'yes',  'no',   'yes' ]


    solution = [ 1,  -2,  -3,   4,
                -5,   6,   7,  -8,
                -9,   10, -11,  12,
                 13, -14,  15, -16,
                -17,  18,  19, -20, -21, 22]
    shuffle(solution)

    decoded = SamplingStrategy.decode(block, solution)
    assert decoded['color'] ==          ['red',  'blue', 'blue', 'red']
    assert decoded['text']  ==          ['blue', 'red',  'blue', 'red']
    assert decoded['color repeats?'] == ['',     'no',   'yes',  'no' ]


def test_decode_with_general_window():
    block = fully_cross_block([color, text, congruent_bookend],
                              [color, text],
                              [Reify(congruent_bookend)])

    solution = [ 1,  -2,  -3,   4,
                -5,   6,   7,  -8,
                -9,   10, -11,  12,
                 13, -14,  15, -16,
                -17,  18,  19, -20]
    shuffle(solution)

    decoded = SamplingStrategy.decode(block, solution)
    assert decoded['color'] ==              ['red',  'blue', 'blue', 'red']
    assert decoded['text']  ==              ['blue', 'red',  'blue', 'red']
    assert decoded['congruent bookend?'] == ['no',   '',     '',     'yes']


def test_decode_with_transition_and_only_positive_variables():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [Reify(color_repeats_factor)])

    solution = [2, 3, 5, 8, 18, 9, 11, 19, 14, 16, 22]

    decoded = SamplingStrategy.decode(block, solution)
    assert decoded['color'] ==          ['blue', 'red',  'red', 'blue']
    assert decoded['text']  ==          ['red',  'blue', 'red', 'blue']
    assert decoded['color repeats?'] == ['',     'no',   'yes', 'no'  ]
