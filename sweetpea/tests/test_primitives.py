import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, ElseLevel, WithinTrial, Transition, Window, get_external_level_name, SimpleLevel
from sweetpea.tests.test_utils import get_level_from_name

color = Factor("color", ["red", "blue"])
text = Factor("text", ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_level   = DerivedLevel("yes", Transition(op.eq, [color]))
color_no_repeat_level = DerivedLevel("no", Transition(op.ne, [color]))
color_repeats_factor  = Factor("color repeats?", [color_repeats_level, color_no_repeat_level])

color3 = Factor("color3", ["red", "blue", "green"])

yes_fn = lambda colors: colors[0] == colors[1] == colors[2]
no_fn = lambda colors: not yes_fn(colors)
color3_repeats_factor = Factor("color3 repeats?", [
    DerivedLevel("yes", Window(yes_fn, [color3], 3, 1)),
    DerivedLevel("no",  Window(no_fn, [color3], 3, 1))
])


def test_factor_validation():
    Factor("factor name", ["level 1", "level 2"])
    Factor("name", [1, 2])
    Factor("name", ["a", "b", "a"])
    Factor("name", [
        DerivedLevel("a", WithinTrial(op.eq, [color, text])),
        ElseLevel("a")
    ])

    # Non-string name
    with pytest.raises(ValueError):
        Factor(56, ["level "])

    # Non-list levels
    with pytest.raises(ValueError):
        Factor("name", 42)

    # Empty list
    with pytest.raises(ValueError):
        Factor("name", [])

    # Valid level types, but not uniform.
    with pytest.raises(ValueError):
        Factor("name", ["level1", con_level])

    # Derived levels with non-uniform window types
    with pytest.raises(ValueError):
        Factor("name", [
            con_level,
            DerivedLevel("other", WithinTrial(lambda color: color, [color]))
        ])

    # Derived levels with different window arguments
    with pytest.raises(ValueError):
        Factor("name", [
            con_level,
            DerivedLevel("other", Transition(lambda colors: colors[0] == colors[1], [color]))
        ])


def test_factor_get_level():
    assert color.get_level(get_level_from_name(color, "red").internal_name).external_name == "red"
    assert color_repeats_factor.get_level(get_level_from_name(color_repeats_factor, "yes").internal_name) == color_repeats_level
    assert color.get_level("bogus") == None


def test_factor_is_derived():
    assert color.is_derived() == False
    assert con_factor.is_derived() == True


def test_factor_has_complex_window():
	assert color.has_complex_window() == False
	assert con_factor.has_complex_window() == False
	assert color_repeats_factor.has_complex_window() == True


def test_factor_applies_to_trial():
    assert color.applies_to_trial(1) == True
    assert color.applies_to_trial(2) == True
    assert color.applies_to_trial(3) == True
    assert color.applies_to_trial(4) == True

    with pytest.raises(ValueError):
        color.applies_to_trial(0)

    assert color_repeats_factor.applies_to_trial(1) == False
    assert color_repeats_factor.applies_to_trial(2) == True
    assert color_repeats_factor.applies_to_trial(3) == True
    assert color_repeats_factor.applies_to_trial(4) == True

    f = Factor('f', [DerivedLevel('l', Window(op.eq, [color], 2, 2))])
    assert f.applies_to_trial(1) == False
    assert f.applies_to_trial(2) == True
    assert f.applies_to_trial(3) == False
    assert f.applies_to_trial(4) == True

    assert color3.applies_to_trial(1) == True


def test_derived_level_validation():
    DerivedLevel(42, WithinTrial(op.eq, [color, text]))
    DerivedLevel("name", WithinTrial(lambda x: x, [color]))

    # Invalid Window
    with pytest.raises(ValueError):
        DerivedLevel("name", 42)

def test_derived_level_argument_list_expansion():
    # We should internally duplicate each factor to match the width of the window.
    assert color_repeats_level.window.args == [color, color]
    assert color_no_repeat_level.window.args == [color, color]


def test_derived_level_get_dependent_cross_product():
    assert [((tup[0][0].factor_name, tup[0][1].external_name),
    (tup[1][0].factor_name, tup[1][1].external_name))  for tup in con_level.get_dependent_cross_product()] == [
        (('color', 'red'), ('text', 'red')),
        (('color', 'red'), ('text', 'blue')),
        (('color', 'blue'), ('text', 'red')),
        (('color', 'blue'), ('text', 'blue'))]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])
    two_con_level = DerivedLevel("twoCon", WithinTrial(lambda x: x, [integer, numeral, text]))
    assert [((tup[0][0].factor_name, tup[0][1].external_name),
    (tup[1][0].factor_name, tup[1][1].external_name),
    (tup[2][0].factor_name, tup[2][1].external_name)) for tup in two_con_level.get_dependent_cross_product()] == [
        (('integer', '1'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'two'))]

    mixed_level = DerivedLevel("mixed", WithinTrial(lambda x: x, [
        Factor("color", ["red", "blue", "green"]),
        Factor("boolean", ["true", "false"])
    ]))
    assert [((tup[0][0].factor_name, tup[0][1].external_name),
    (tup[1][0].factor_name, tup[1][1].external_name)) for tup in mixed_level.get_dependent_cross_product()] == [
        (('color', 'red'), ('boolean', 'true')),
        (('color', 'red'), ('boolean', 'false')),
        (('color', 'blue'), ('boolean', 'true')),
        (('color', 'blue'), ('boolean', 'false')),
        (('color', 'green'), ('boolean', 'true')),
        (('color', 'green'), ('boolean', 'false'))
    ]


def test_derived_level_equality():
    assert con_level == con_level

def test_else_level():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])

    conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    conFactor = Factor("congruent?", [conLevel, ElseLevel("inc")])

def __get_response_transition() -> Factor:
    color  = Factor("color",  ["red", "blue", "green"])
    motion = Factor("motion", ["up", "down"])
    task   = Factor("task",   ["color", "motion"])

    # Response Definition
    def response_left(task, color, motion):
        return (task == "color"  and color  == "red") or \
            (task == "motion" and motion == "up")

    def response_right(task, color, motion):
        return not response_left(task, color, motion)

    response = Factor("response", [
        DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
        DerivedLevel("right", WithinTrial(response_right, [task, color, motion]))
    ])

    return Factor("response transition", [
        DerivedLevel("repeat", Transition(lambda responses: responses[0] == responses[1], [response])),
        DerivedLevel("switch", Transition(lambda responses: responses[0] != responses[1], [response]))
    ])


def test_derived_level_get_dependent_cross_product_with_nesting():
    response_transition = __get_response_transition()

    assert [((tup[0][0].factor_name, tup[0][1].external_name),
    (tup[1][0].factor_name, tup[1][1].external_name)) for tup in response_transition.levels[0].get_dependent_cross_product()] == [
        (('response', 'left' ), ('response', 'left' )),
        (('response', 'left' ), ('response', 'right')),
        (('response', 'right'), ('response', 'left' )),
        (('response', 'right'), ('response', 'right'))
    ]

def test_base_window_validation():
    # Nonfactor argument
    with pytest.raises(ValueError):
        WithinTrial(op.eq, [42])

    # Duplicated factors
    with pytest.raises(ValueError):
        DerivedLevel("name", WithinTrial(lambda x, y: x, [color, color]))
