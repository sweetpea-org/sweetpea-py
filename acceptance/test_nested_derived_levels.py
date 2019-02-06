import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import Exclude
from sweetpea.encoding_diagram import print_encoding_diagram
from sweetpea import fully_cross_block, synthesize_trials_non_uniform, print_experiments


color      = Factor("color",  ["red", "blue", "green", "brown"])
word       = Factor("motion", ["red", "blue", "green", "brown"])

repeated_color_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(lambda colors: colors[0] == colors[1], [color])),
    DerivedLevel("no",  Transition(lambda colors: colors[0] != colors[1], [color]))
])

repeated_word_factor = Factor("repeated word?", [
    DerivedLevel("yes", Transition(lambda words: words[0] == words[1], [word])),
    DerivedLevel("no",  Transition(lambda words: words[0] != words[1], [word]))
])

def color_and_word_repeat_fn(color_repeated, word_repeated):
    return color_repeated == "yes" and word_repeated == "yes"

def color_and_word_did_not_repeat_fn(color_repeated, word_repeated):
    return not color_and_word_repeat_fn(color_repeated, word_repeated)

color_and_word_repeated_factor = Factor("both repeat?", [
    DerivedLevel("yes", WithinTrial(color_and_word_repeat_fn,         [repeated_color_factor, repeated_word_factor])),
    DerivedLevel("no",  WithinTrial(color_and_word_did_not_repeat_fn, [repeated_color_factor, repeated_word_factor]))
])

design       = [color, word, repeated_color_factor, repeated_word_factor, color_and_word_repeated_factor]
crossing     = [color, word]
constraints  = [Exclude(("both repeat?", "yes"))]
block        = fully_cross_block(design, crossing, constraints)


@pytest.mark.skip
def test_correct_solution_count_with_nested_derived_factors():
    # TODO:
    # Nested derived levels (Derived levels that derive from other derived levels) aren't supported yet.
    # I thought it would be pretty basic to fix, but it turns out it's harder than anticipated, so I think
    # I'm going to set it aside for now.
    #
    # The difficulty comes from the realization that the width and stride of a window are relative to the
    # trial sequence to which  the controlling factors apply. For example:
    #
    # - Let 'A' be a derived factor with width=1 and stride=2.
    # - Let 'B' be a derived factor with widht=1 and stride=1 that depends on 'A'.
    #
    # Because 'A' only applies to every other trial, so does 'B'! Even though 'B's stride is 1!
    #
    # I'm not sure yet how to sort this out. We could force the user to specify the correct width
    # and stride, but that's not a great experience.
    #
    # This came up while looking at the 'Exclude' constraint, and trying to determine the circumstances
    # in which the exclude constraint would reduce the sequence length. At first I thought it would
    # reduce the sequence length whenever it is applied to a derived factor with a window width of 1.
    # However, this test block provides a counterexample in which a derived factor (albeit nested) with
    # a width of 1 is excluded, and it does _not_ (I think) reduce the sequence length.
    #
    # I'm not sure yet if Jon/Sebastian will need to nest derived factors, but if they do, it may impact
    # the way that we're handling the Exclude constraint.
    experiments = synthesize_trials_non_uniform(block, 50)

    assert len(experiments) > 0
