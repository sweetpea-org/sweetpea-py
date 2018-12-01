import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window

color = Factor("color", ["red", "blue"])
text = Factor("text", ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_level   = DerivedLevel("yes", Transition(op.eq, [color, color]))
color_no_repeat_level = DerivedLevel("no", Transition(op.ne, [color, color]))
color_repeats_factor  = Factor("color repeats?", [color_repeats_level, color_no_repeat_level])


def test_factor_validation():
    Factor("factor name", ["level 1", "level 2"])

    # Non-string name
    with pytest.raises(ValueError):
        Factor(56, ["level "])

    # Non-list levels
    with pytest.raises(ValueError):
        Factor("name", 42)

    # Empty list
    with pytest.raises(ValueError):
        Factor("name", [])

    # Invalid level type
    with pytest.raises(ValueError):
        Factor("name", [1, 2])

    # Valid level types, but not uniform.
    with pytest.raises(ValueError):
        Factor("name", ["level1", con_level])

    # Derived levels with non-uniform window types
    with pytest.raises(ValueError):
        Factor("name", [
            con_level,
            DerivedLevel("other", Transition(op.eq, [color, color]))
        ])


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

    f = Factor('f', [DerivedLevel('l', Window(op.eq, [color, color], 2))])
    assert f.applies_to_trial(1) == False
    assert f.applies_to_trial(2) == True
    assert f.applies_to_trial(3) == False
    assert f.applies_to_trial(4) == True


def test_derived_level_validation():
    # Non-str name
    with pytest.raises(ValueError):
        DerivedLevel(42, WithinTrial(op.eq, [color, text]))

    # Invalid Window
    with pytest.raises(ValueError):
        DerivedLevel("name", 42)


def test_derived_level_get_dependent_cross_product():
    assert con_level.get_dependent_cross_product() == [
        (('color', 'red'), ('text', 'red')),
        (('color', 'red'), ('text', 'blue')),
        (('color', 'blue'), ('text', 'red')),
        (('color', 'blue'), ('text', 'blue'))]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])
    two_con_level = DerivedLevel("twoCon", WithinTrial(lambda x: x, [integer, numeral, text]))
    assert two_con_level.get_dependent_cross_product() == [
        (('integer', '1'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '1'), ('numeral', 'II'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'I'), ('text', 'two')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'one')),
        (('integer', '2'), ('numeral', 'II'), ('text', 'two'))]


def test_derived_level_equality():
    assert con_level == con_level

    # Sometimes string levels may be compared directly to DerivedLevels
    assert con_level != "blue"


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
        DerivedLevel("repeat", Transition(op.eq, [response, response])),
        DerivedLevel("switch", Transition(op.ne, [response, response]))
    ])


def test_derived_level_get_dependent_cross_product_with_nesting():
    response_transition = __get_response_transition()

    assert response_transition.levels[0].get_dependent_cross_product() == [
        (('response', 'left' ), ('response', 'left' )),
        (('response', 'left' ), ('response', 'right')),
        (('response', 'right'), ('response', 'left' )),
        (('response', 'right'), ('response', 'right'))
    ]


