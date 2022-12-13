import operator as op

from sweetpea._internal.level import get_all_levels
from sweetpea._internal.iter import intersperse
from sweetpea._internal.primitive import Factor, DerivedLevel, Transition


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue", "green"])

color_repeats_level   = DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color]))
color_no_repeat_level = DerivedLevel("no", Transition(lambda colors: colors[0] != colors[-1], [color]))
color_repeats_factor  = Factor("color repeats?", [color_repeats_level, color_no_repeat_level])

def test_get_all_external_level_names():
    assert get_all_levels([color, text]) == [(color, color.get_level('red')),
                                             (color, color.get_level('blue')),
                                             (text, text.get_level('red')),
                                             (text, text.get_level('blue')),
                                             (text, text.get_level('green'))]

    assert get_all_levels([color_repeats_factor]) == [(color_repeats_factor, color_repeats_level),
                                                      (color_repeats_factor, color_no_repeat_level)]

def test_intersperse():
    assert list(intersperse('', ['yes', 'no', 'yes'])) == \
        ['yes', '', 'no', '', 'yes']

    assert list(intersperse('', ['yes', 'no', 'yes'], 2)) == \
        ['yes', '', '', 'no', '', '', 'yes']

    assert list(intersperse('', ['yes', 'no', 'yes'], 0)) == \
        ['yes', 'no', 'yes']
