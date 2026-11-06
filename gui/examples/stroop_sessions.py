"""
Stroop in two sessions, with Repeat and Merge.

- stroop_trials: every color x word pair once (4 trials).
- stroop_twice: those trials run twice (8 trials).
- sessions_of_stroop: morning and afternoon each hold for stroop_twice
  (16 trials); incongruent trials never come more than 2 in a row, even
  across the session boundary.
- hand_assignment: the response hand is balanced separately over the same
  trials, and the Merge puts the sessions in order.
"""

from sweetpea import (
    synthesize_trials, print_experiments, CrossBlock, Repeat,
    Nest, Merge, Factor, DerivedLevel,
    WithinTrial, MinimumTrials, AtMostKInARow, Sequential,
    CMSGen,
)

color = Factor("color", ["red", "blue"])
word = Factor("word", ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent", WithinTrial(lambda color, word: color == word, [color, word])),
    DerivedLevel("incongruent", WithinTrial(lambda color, word: color != word, [color, word])),
])
session = Factor("session", ["morning", "afternoon"])
response_hand = Factor("response_hand", ["left", "right"])

session_block = CrossBlock(
    design=[session],
    crossing=[session],
    constraints=[],
)

stroop_trials = CrossBlock(
    design=[color, word, congruency],
    crossing=[color, word],
    constraints=[],
)

stroop_twice = Repeat(
    block=stroop_trials,
    constraints=[
        MinimumTrials(8),
    ],
)

sessions_of_stroop = Nest(
    outer_block=session_block,
    inner_block=stroop_twice,
    constraints=[
        AtMostKInARow(2, (congruency, "incongruent")),
    ],
)

hand_assignment = CrossBlock(
    design=[response_hand],
    crossing=[response_hand],
    constraints=[],
)

experiment = Merge(
    blocks=[sessions_of_stroop, hand_assignment],
    constraints=[
        Sequential(session),
    ],
)

experiments = synthesize_trials(experiment, 2, CMSGen)
print_experiments(experiment, experiments)
