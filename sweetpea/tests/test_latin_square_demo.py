"""Latin Square counterbalancing demo — multiple grid sizes.

Demonstrates LatinSquare constraint with synthesize_trials(participants=...)
for 2x2, 3x3, and 2x3 (rectangular) outer grids.  Includes cases where
only a subset of possible participants is requested.
"""

from sweetpea import *


def show_trials(exp, outer_names, inner_names):
    """Pretty-print a single experiment's trials."""
    all_names = outer_names + inner_names
    header = "  ".join(f"{n:<7}" for n in ["Trial"] + all_names)
    print(header)
    print("-" * len(header))
    n = len(exp[all_names[0]])
    for i in range(n):
        row = f"{i+1:<7}"
        row += "  ".join(f"{exp[name][i]:<7}" for name in all_names)
        print(row)


def show_participant_combos(results, outer_names):
    """Print the outer combos each participant received."""
    for pid in sorted(results.keys()):
        exp = results[pid][0]
        combos = set()
        for i in range(len(exp[outer_names[0]])):
            combos.add(tuple(exp[name][i] for name in outer_names))
        print(f"  Participant {pid}: {len(exp[outer_names[0]])} trials, "
              f"outer combos = {sorted(combos)}")


# ======================================================================
# DEMO 1 — 2x2 Latin Square (Font x Color), all participants
# 2 diagonals, 2 participants, 8 trials each
# ======================================================================
print("=" * 65)
print("DEMO 1: 2x2 Latin Square  (Font x Color)")
print("         All participants requested")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "B"])
color = Factor("Color", ["R", "G"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

print(f"Diagonals: {ls.diagonals}")
print(f"Num participants needed: {ls.num_participants}")
print()

results = synthesize_trials(nb, 1, participants=[0, 1])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])
print()


# ======================================================================
# DEMO 2 — 2x2 Latin Square, only participant 0 requested
# Demonstrates computation savings: participant 1 is never solved
# ======================================================================
print("=" * 65)
print("DEMO 2: 2x2 Latin Square  (Font x Color)")
print("         Only participant 0 requested  (saves computation)")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "B"])
color = Factor("Color", ["R", "G"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

results = synthesize_trials(nb, 1, participants=[0])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])
print()


# ======================================================================
# DEMO 3 — 3x3 Latin Square (Font x Color), all 3 participants
# 3 diagonals, 3 participants, 3 outer combos x 4 inner = 12 trials each
# ======================================================================
print("=" * 65)
print("DEMO 3: 3x3 Latin Square  (Font x Color)")
print("         All 3 participants requested")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "M", "B"])
color = Factor("Color", ["R", "G", "Bu"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

print(f"Diagonals: {ls.diagonals}")
print(f"Num participants needed: {ls.num_participants}")
print()

results = synthesize_trials(nb, 1, participants=[0, 1, 2])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])
print()


# ======================================================================
# DEMO 4 — 3x3 Latin Square, only 1 of 3 participants requested
# Demonstrates solving only what you need
# ======================================================================
print("=" * 65)
print("DEMO 4: 3x3 Latin Square  (Font x Color)")
print("         Only participant 2 of 3 requested")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "M", "B"])
color = Factor("Color", ["R", "G", "Bu"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

results = synthesize_trials(nb, 1, participants=[2])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])
print()


# ======================================================================
# DEMO 5 — 2x3 Rectangular grid (Font x Color)
# D = max(2,3) = 3 diagonals, but only 2 of 3 participants requested
# ======================================================================
print("=" * 65)
print("DEMO 5: 2x3 Rectangular Latin Square  (Font x Color)")
print("         2 of 3 participants requested")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "B"])
color = Factor("Color", ["R", "G", "Bu"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

print(f"Diagonals: {ls.diagonals}")
print(f"Num participants needed: {ls.num_participants}")
print()

results = synthesize_trials(nb, 1, participants=[0, 2])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])
print()


# ======================================================================
# DEMO 6 — Cyclical wrapping: participant 5 on a 2x2 grid
# participant 5 % 2 = 1, same diagonal as participant 1
# ======================================================================
print("=" * 65)
print("DEMO 6: Cyclical wrapping  (2x2 grid, participant ID = 5)")
print("         5 % 2 = 1 -> same diagonal as participant 1")
print("=" * 65)
print()

font  = Factor("Font",  ["S", "B"])
color = Factor("Color", ["R", "G"])
task  = Factor("Task",  ["Rd", "Wr"])
speed = Factor("Speed", ["F", "Sl"])

ls = LatinSquare(outer_factors=[font, color])
inner = CrossBlock([task, speed], [task, speed], [])

nb = NestedBlock(
    design=[font, color, inner],
    crossing=[font, color],
    constraints=[ls]
)

results = synthesize_trials(nb, 1, participants=[5])

print_experiments(nb, results)
show_participant_combos(results, ["Font", "Color"])

expected_combos = {("S", "G"), ("B", "R")}  # diagonal 1
actual_combos = set()
exp = results[5][0]
for i in range(len(exp["Font"])):
    actual_combos.add((exp["Font"][i], exp["Color"][i]))
assert actual_combos == expected_combos, (
    f"Expected diagonal 1 combos {expected_combos}, got {actual_combos}"
)
print("  Wrapping verified: participant 5 got diagonal 1 combos.\n")


# ======================================================================
# Summary
# ======================================================================
print("=" * 65)
print("SUMMARY")
print("=" * 65)
print()
print("Demo  Grid   Participants requested   Trials/participant")
print("-" * 60)
print("1     2x2    [0, 1]  (all 2)           8   (2 blocks x 4)")
print("2     2x2    [0]     (1 of 2)           8")
print("3     3x3    [0,1,2] (all 3)           12   (3 blocks x 4)")
print("4     3x3    [2]     (1 of 3)           12")
print("5     2x3    [0, 2]  (2 of 3)            8   (2 blocks x 4)")
print("6     2x2    [5]     (wraps to diag 1)   8")
print()
print("Key insight: only requested participants are solved.")
print("Skipping participants saves computation.")
