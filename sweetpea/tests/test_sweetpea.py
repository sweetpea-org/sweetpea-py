import operator as op
import pytest

from sweetpea import fully_cross_block, __decode, __generate_encoding_diagram
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.constraints import NoMoreThanKInARow
from sweetpea.logic import to_cnf_tseitin


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

design = [color, text, con_factor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [])


def test_decode():
    solution = [-1,   2,  -3,   4,   5,  -6,
                -7,   8,   9, -10, -11,  12,
                13, -14, -15,  16, -17,  18,
                19, -20,  21, -22,  23, -24]
    assert __decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red',  'red'],
        'text':       ['blue', 'red',  'blue', 'red'],
        'congruent?': ['con',  'inc',  'inc',  'con']
    }

    solution = [ -1,   2, -3,   4,   5,  -6,
                  7,  -8, -9,  10, -11,  12,
                 13, -14, 15, -16,  17, -18,
                -19,  20, 21, -22, -23,  24]
    assert __decode(blk, solution) == {
        'color':      ['blue', 'red',  'red', 'blue'],
        'text':       ['blue', 'blue', 'red', 'red'],
        'congruent?': ['con',  'inc',  'con', 'inc']
    }

    solution = [-1,   2,   3,  -4,  -5,   6,
                -7,   8,  -9,  10,  11, -12,
                13, -14,  15, -16,  17, -18,
                19, -20, -21,  22, -23,  24]
    assert __decode(blk, solution) == {
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
    assert __decode(f_blk, solution) == {
        'a': ['c', 'd', 'b'],
        'e': ['f', 'f', 'f']
    }


def test_decode_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [])

    solution = [ 1,  -2,  3,  -4,
                 5,  -6, -7,   8,   #  17, -18
                -9,  10,  11, -12,  # -19,  20
                -13, 14, -15,  16,  #  21, -22
                17, -18, -19, 20, 21, -22] # color_repeats_factor
    decoded = __decode(block, solution)
    assert decoded['color'] ==          ['red', 'red',  'blue', 'blue']
    assert decoded['text']  ==          ['red', 'blue', 'red',  'blue']
    assert decoded['color repeats?'] == ['',    'yes',  'no',   'yes' ]


    solution = [ 1,  -2,  -3,   4,
                -5,   6,   7,  -8,
                -9,   10, -11,  12,
                 13, -14,  15, -16,
                -17,  18,  19, -20, -21, 22]
    decoded = __decode(block, solution)
    assert decoded['color'] ==          ['red',  'blue', 'blue', 'red']
    assert decoded['text']  ==          ['blue', 'red',  'blue', 'red']
    assert decoded['color repeats?'] == ['',     'no',   'yes',  'no' ]


def test_generate_encoding_diagram():
    assert __generate_encoding_diagram(blk) == "\
----------------------------------------------\n\
|   Trial |  color   |   text   | congruent? |\n\
|       # | red blue | red blue |  con  inc  |\n\
----------------------------------------------\n\
|       1 |  1   2   |  3   4   |   5    6   |\n\
|       2 |  7   8   |  9   10  |  11    12  |\n\
|       3 | 13   14  | 15   16  |  17    18  |\n\
|       4 | 19   20  | 21   22  |  23    24  |\n\
----------------------------------------------\n"


def test_generate_encoding_diagram_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [])

    assert __generate_encoding_diagram(block) == "\
--------------------------------------------------\n\
|   Trial |  color   |   text   | color repeats? |\n\
|       # | red blue | red blue |   yes     no   |\n\
--------------------------------------------------\n\
|       1 |  1   2   |  3   4   |                |\n\
|       2 |  5   6   |  7   8   |   17      18   |\n\
|       3 |  9   10  | 11   12  |   19      20   |\n\
|       4 | 13   14  | 15   16  |   21      22   |\n\
--------------------------------------------------\n"


def test_generate_encoding_diagram_with_constraint_and_multiple_transitions():
    block = fully_cross_block([color, text, con_factor, color_repeats_factor, text_repeats_factor],
                              [color, text],
                              [])

    assert __generate_encoding_diagram(block) == "\
-------------------------------------------------------------------------------\n\
|   Trial |  color   |   text   | congruent? | color repeats? | text repeats? |\n\
|       # | red blue | red blue |  con  inc  |   yes     no   |   yes    no   |\n\
-------------------------------------------------------------------------------\n\
|       1 |  1   2   |  3   4   |   5    6   |                |               |\n\
|       2 |  7   8   |  9   10  |  11    12  |   25      26   |   31     32   |\n\
|       3 | 13   14  | 15   16  |  17    18  |   27      28   |   33     34   |\n\
|       4 | 19   20  | 21   22  |  23    24  |   29      30   |   35     36   |\n\
-------------------------------------------------------------------------------\n"


def test_generate_encoding_diagram_with_constraint_and_multiple_transitions_in_different_order():
    block = fully_cross_block([text_repeats_factor, color, color_repeats_factor, text, con_factor],
                              [color, text],
                              [])

    assert __generate_encoding_diagram(block) == "\
-------------------------------------------------------------------------------\n\
|   Trial | text repeats? |  color   | color repeats? |   text   | congruent? |\n\
|       # |   yes    no   | red blue |   yes     no   | red blue |  con  inc  |\n\
-------------------------------------------------------------------------------\n\
|       1 |               |  1   2   |                |  3   4   |   5    6   |\n\
|       2 |   25     26   |  7   8   |   31      32   |  9   10  |  11    12  |\n\
|       3 |   27     28   | 13   14  |   33      34   | 15   16  |  17    18  |\n\
|       4 |   29     30   | 19   20  |   35      36   | 21   22  |  23    24  |\n\
-------------------------------------------------------------------------------\n"


def test_generate_encoding_diagram_with_windows():
    color3 = Factor("color3", ["red", "blue", "green"])

    yes_fn = lambda colors: colors[0] == colors[1] == colors[2]
    no_fn = lambda colors: not yes_fn(colors)
    color3_repeats_factor = Factor("color3 repeats?", [
        DerivedLevel("yes", Window(yes_fn, [color3], 3, 1)),
        DerivedLevel("no",  Window(no_fn, [color3], 3, 1))
    ])

    block = fully_cross_block([color3_repeats_factor, color3, text], [color3, text], [])

    assert __generate_encoding_diagram(block) == "\
---------------------------------------------------------\n\
|   Trial | color3 repeats? |     color3     |   text   |\n\
|       # |   yes      no   | red blue green | red blue |\n\
---------------------------------------------------------\n\
|       1 |                 |  1   2     3   |  4   5   |\n\
|       2 |                 |  6   7     8   |  9   10  |\n\
|       3 |    31      32   | 11   12   13   | 14   15  |\n\
|       4 |    33      34   | 16   17   18   | 19   20  |\n\
|       5 |    35      36   | 21   22   23   | 24   25  |\n\
|       6 |    37      38   | 26   27   28   | 29   30  |\n\
---------------------------------------------------------\n"
