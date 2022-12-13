import glob
import operator as op
import os
import pytest
import re

from sweetpea import CrossBlock, MinimumTrials, synthesize_trials, UniformGen
from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea._internal.constraint import Exclude, ExactlyKInARow, AtMostKInARow, Reify
from sweetpea._internal.sampling_strategy.random import RandomGen, UCSolutionEnumerator

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

red_color = color["red"]
blue_color = color["blue"]
red_text = text["red"]
blue_text = text["blue"]

con_factor_within_trial = Factor("congruent?", [
    DerivedLevel("con", WithinTrial(op.eq, [color, text])),
    DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
])

con_factor_window = Factor("congruent?", [
    DerivedLevel("con", Window(op.eq, [color, text], 1, 1)),
    DerivedLevel("inc", Window(op.ne, [color, text], 1, 1))
])

color_repeats_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[-1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[-1], [color]))
])


def test_validate_accepts_basic_factors():
    block = CrossBlock([color, text],
                       [color, text],
                       [])
    RandomGen._RandomGen__validate(block)


def test_validate_accepts_derived_factors_with_simple_windows():
    block = CrossBlock([color, text, con_factor_within_trial],
                       [color, text],
                       [])
    RandomGen._RandomGen__validate(block)

    block = CrossBlock([color, text, con_factor_window],
                       [color, text],
                       [])
    RandomGen._RandomGen__validate(block)


def test_validate_accepts_implied_derived_factors_with_complex_windows():
    block = CrossBlock([color, text, color_repeats_factor],
                       [color, text],
                       [])
    # no error

def test_example_counts():
    # Get all the python examples from the uc-counting-tests directory
    path_to_test_files = os.path.dirname(os.path.abspath(__file__)) + "/uc-counting-tests/*.py"
    files = glob.glob(path_to_test_files)

    failures = []

    for filename in files:
        contents = None
        with open(filename, 'r') as f:
            contents = f.read()
            exec(contents, globals(), locals())

        if 'block' not in vars():
            failures.append("File did not produce a variable named 'block', aborting. file={}".format(filename))
            continue

        matches = re.search('# ASSERT COUNT = (\d+)', contents)
        if matches:
            expected_count = int(matches.groups(0)[0])
            enumerator = UCSolutionEnumerator(vars()['block'])
            if enumerator.solution_count() != expected_count:
                failures.append("Count Mismatch. Actual count: {}, Expected count: {}, File={}"
                    .format(enumerator.solution_count(), expected_count, filename))
        else:
            failures.append("File did not contain an assertion for count, aborting. file={}".format(filename))

    if failures:
        pytest.fail('{} failures occurred in counting tests: {}'.format(len(failures), failures))


def test_constraint_violation():
    are_constraints_violated = RandomGen._RandomGen__are_constraints_violated

    block = CrossBlock([color, text, con_factor_within_trial],
                       [color, text],
                       [ExactlyKInARow(2, (color, red_color))])

    class FakeEnumer:
        def __init__(self):
            self.has_crossed_complex_derived_factors = False
    enumer = FakeEnumer()

    assert are_constraints_violated(block, {color: [color[l] for l in ['red', 'red', 'blue', 'blue']]}, enumer, 4, 0, 0) == False
    assert are_constraints_violated(block, {color: [color[l] for l in ['red', 'blue', 'red', 'blue']]}, enumer, 4, 0, 0) == True

    block = CrossBlock([color, text, con_factor_within_trial],
                       [color, text],
                       [AtMostKInARow(2, (color, red_color))])

    assert are_constraints_violated(block, {color: [color[l] for l in ['red', 'blue', 'blue', 'blue']]}, enumer, 4, 0, 0) == False
    assert are_constraints_violated(block, {color: [color[l] for l in ['red', 'red', 'blue', 'blue']]}, enumer, 4, 0, 0) == False
    assert are_constraints_violated(block, {color: [color[l] for l in ['red', 'red', 'red', 'blue']]}, enumer, 4, 0, 0) == True
    assert are_constraints_violated(block, {color: [color[l] for l in ['blue', 'red', 'red', 'red']]}, enumer, 4, 0, 0) == True

def test_minimum_trials():
    for min_trials in [1, 2, 3, 4, 5, 6, 7, 17, 55]:
        block = CrossBlock([color, text],
                           [color, text],
                           [MinimumTrials(min_trials)])
        runs = synthesize_trials(block=block, samples=1,sampling_strategy=RandomGen)
        assert len(runs[0]["color"]) == max(4, min_trials)
