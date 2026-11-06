"""
Nested sessions: days, then sessions within each day, then A x B trials.

Each day is held constant for two sessions, and each session for one run of
every A x B combination: 16 trials. The constraint on the sessions Nest keeps
a1 from appearing more than twice in a row anywhere in the sequence.
"""

from sweetpea import (
    synthesize_trials, print_experiments, CrossBlock, Nest,
    Factor, AtMostKInARow, CMSGen,
)

A = Factor("A", ["a1", "a2"])
B = Factor("B", ["b1", "b2"])
session = Factor("session", ["s1", "s2"])
day = Factor("day", ["d1", "d2"])

day_block = CrossBlock(
    design=[day],
    crossing=[day],
    constraints=[],
)

session_block = CrossBlock(
    design=[session],
    crossing=[session],
    constraints=[],
)

ab_trials = CrossBlock(
    design=[A, B],
    crossing=[A, B],
    constraints=[],
)

sessions = Nest(
    outer_block=session_block,
    inner_block=ab_trials,
    constraints=[
        AtMostKInARow(2, (A, "a1")),
    ],
)

days = Nest(
    outer_block=day_block,
    inner_block=sessions,
    constraints=[],
)

experiments = synthesize_trials(days, 1, CMSGen)
print_experiments(days, experiments)
