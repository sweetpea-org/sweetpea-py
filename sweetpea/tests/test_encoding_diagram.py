import pytest
import operator as op

from sweetpea import CrossBlock
from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea._internal.constraint import Reify
from sweetpea._internal.encoding_diagram import __generate_encoding_diagram


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("color repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])

text_repeats_factor = Factor("text repeats?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [text])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [text]))
])

design = [color, text, con_factor]
crossing = [color, text]
blk = CrossBlock(design, crossing, [Reify(con_factor)])


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
    block = CrossBlock([color, text, color_repeats_factor],
                       [color, text],
                       [Reify(color_repeats_factor)])

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
    design = [color, text, con_factor, color_repeats_factor, text_repeats_factor]
    block = CrossBlock(design,
                       [color, text],
                       list(map(Reify, design)))

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
    design = [text_repeats_factor, color, color_repeats_factor, text, con_factor]
    block = CrossBlock(design,
                              [color, text],
                              list(map(Reify, design)))

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

    yes_fn = lambda colors: colors[0] == colors[-1] == colors[-2]
    no_fn = lambda colors: not yes_fn(colors)
    color3_repeats_factor = Factor("color3 repeats?", [
        DerivedLevel("yes", Window(yes_fn, [color3], 3, 1)),
        DerivedLevel("no",  Window(no_fn, [color3], 3, 1))
    ])

    block = CrossBlock([color3_repeats_factor, color3, text], [color3, text], [Reify(color3_repeats_factor)])

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


def test_generate_encoding_diagram_with_window_with_stride():
    congruent_bookend = Factor("congruent bookend?", [
        DerivedLevel("yes", Window(lambda colors, texts: colors[0] == texts[0], [color, text], 1, 3)),
        DerivedLevel("no",  Window(lambda colors, texts: colors[0] != texts[0], [color, text], 1, 3))
    ])

    block = CrossBlock([color, text, congruent_bookend], [color, text], [Reify(congruent_bookend)])

    assert __generate_encoding_diagram(block) == "\
------------------------------------------------------\n\
|   Trial |  color   |   text   | congruent bookend? |\n\
|       # | red blue | red blue |    yes       no    |\n\
------------------------------------------------------\n\
|       1 |  1   2   |  3   4   |    17        18    |\n\
|       2 |  5   6   |  7   8   |                    |\n\
|       3 |  9   10  | 11   12  |                    |\n\
|       4 | 13   14  | 15   16  |    19        20    |\n\
------------------------------------------------------\n"

    congruent_bookend = Factor("congruent bookend?", [
        DerivedLevel("yes", Window(lambda colors, texts: colors[0] == texts[0], [color, text], 2, 2)),
        DerivedLevel("no",  Window(lambda colors, texts: colors[0] != texts[0], [color, text], 2, 2))
    ])

    block = CrossBlock([color, text, congruent_bookend], [color, text], [Reify(congruent_bookend)])

    assert __generate_encoding_diagram(block) == "\
------------------------------------------------------\n\
|   Trial |  color   |   text   | congruent bookend? |\n\
|       # | red blue | red blue |    yes       no    |\n\
------------------------------------------------------\n\
|       1 |  1   2   |  3   4   |                    |\n\
|       2 |  5   6   |  7   8   |    17        18    |\n\
|       3 |  9   10  | 11   12  |                    |\n\
|       4 | 13   14  | 15   16  |    19        20    |\n\
------------------------------------------------------\n"

