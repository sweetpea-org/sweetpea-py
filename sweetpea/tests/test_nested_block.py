import pytest

from sweetpea._internal.cross_block import CrossBlock, NestedBlock
from sweetpea._internal.constraint import (
    MinimumTrials,
    ConstantInWindows,
    OrderRunsByPermutation,
    ExactlyK,
    AtMostKInARow,
    Exclude,
)
from sweetpea._internal.primitive import Factor, SimpleLevel, DerivedLevel, Transition


# ---------- helpers

def levels(names):
    return [SimpleLevel(n) for n in names]

def combos_in_product_order(factors):
    """Cartesian product of level *names* in itertools.product order."""
    from itertools import product
    names = [[lvl.name for lvl in f.levels] for f in factors]
    return list(product(*names))

def get_constraint(block, cls, **attrs):
    """Return the first constraint of type `cls` matching provided attribute identities/values."""
    for c in block.constraints:
        if isinstance(c, cls) and all(getattr(c, k) is v for k, v in attrs.items()):
            return c
    return None

def has_exactly_k(block, factor, level, k):
    return any(
        isinstance(c, ExactlyK)
        and getattr(c.level, "factor", None) is factor
        and c.level is level
        and c.k == k
        for c in block.constraints
    )


# ---------- fixtures: tiny inner block

@pytest.fixture
def inner_2x2():
    # Inner block with a single crossing: 2x2 = 4 trials, preamble 0.
    A = Factor("A", levels(["a1", "a2"]))
    B = Factor("B", levels(["b1", "b2"]))
    inner = CrossBlock(design=[A, B], crossing=[A, B], constraints=[])
    assert inner.trials_per_sample() == 4
    assert len(inner.crossings) == 1
    return inner


# ======================================================================
# NON-PERMUTED NESTED MODE
# ======================================================================

def test_nested_mode_constant_windows_and_length(inner_2x2):
    task = Factor("task", levels(["single", "dual"]))  # 2 levels
    nb = NestedBlock(
        design=[task, inner_2x2],
        crossing=[task],             # inner block NOT listed => non-permuted
        constraints=[]
    )

    # Geometry: each window is the entire inner block (run_len = 4)
    assert nb.trials_per_sample() == 2 * 4  # 2 task levels × 4 inner trials
    assert any(isinstance(c, ConstantInWindows) and c.factor is task and c.run_len == 4
               for c in nb.constraints)

    # MinimumTrials forces 8 trials total
    assert any(isinstance(c, MinimumTrials) and c.trials == 8 for c in nb.constraints)

    # Valid sample: for each task level, repeat the 2x2 inner product once
    A, B = [f for f in nb.design if getattr(f, "name", None) in ("A", "B")]
    product_order = combos_in_product_order([A, B])

    task_vals, A_vals, B_vals = [], [], []
    for tname in ["single", "dual"]:
        task_vals.extend([tname] * 4)
        for a_name, b_name in product_order:
            A_vals.append(a_name)
            B_vals.append(b_name)

    sample = {"task": task_vals, "A": A_vals, "B": B_vals}

    # Constancy passes on valid sample
    for c in nb.constraints:
        if isinstance(c, ConstantInWindows) and c.factor is task:
            assert c.potential_sample_conforms(sample, nb)

    # Violate constancy: flip 'task' within first window
    bad_sample = dict(sample)
    bad_sample["task"] = sample["task"][:]
    bad_sample["task"][1] = "dual"
    violated = [c for c in nb.constraints
                if isinstance(c, ConstantInWindows) and c.factor is task
                and not c.potential_sample_conforms(bad_sample, nb)]
    assert violated


def test_inner_constraints_are_inherited(inner_2x2):
    """Put a simple constraint on the inner block and ensure NestedBlock inherits it."""
    A = next(f for f in inner_2x2.orig_design if getattr(f, "name", None) == "A")
    inner_constrained = CrossBlock(
        design=inner_2x2.orig_design,
        crossing=inner_2x2.orig_crossings[0],
        constraints=[AtMostKInARow(1, (A, "a1"))],
    )
    task = Factor("task", levels(["T1", "T2"]))
    nb = NestedBlock(design=[task, inner_constrained], crossing=[task], constraints=[])
    assert any(isinstance(c, AtMostKInARow) for c in nb.constraints)


def test_constant_in_windows_rejects_misaligned_length(inner_2x2):
    """Non-permuted: T must be a multiple of run_len for ConstantInWindows to hold."""
    task = Factor("task", levels(["T1", "T2"]))
    nb = NestedBlock(design=[task, inner_2x2], crossing=[task], constraints=[])
    # run_len for task = inner_total = 4; total should be 8, but we give 6
    sample = {
        "task": ["T1"] * 6,
        "A": ["a1", "a2", "a1", "a2", "a1", "a2"],
        "B": ["b1", "b2", "b1", "b2", "b1", "b2"],
    }
    cwin = get_constraint(nb, ConstantInWindows, factor=task)
    assert cwin and cwin.run_len == 4
    assert cwin.potential_sample_conforms(sample, nb) is False


# ======================================================================
# PERMUTED NESTED MODE (inner listed in crossing; all Factors from design in crossing)
# ======================================================================

def test_permuted_mode_enforces_permutation_and_balancing(inner_2x2):
    group = Factor("group", levels(["G1", "G2"]))
    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],   # include all Factors from design per rule
        constraints=[],
        num_permutations=2,            # K = 2
        permutation_factor_name="order"
    )

    # Access the hidden permutation factor
    perm_factor = nb.perm_factor
    perm_key_obj = perm_factor.name  # key is the HiddenName object

    # Constant in windows for the permutation factor
    assert any(isinstance(c, ConstantInWindows) and c.factor is perm_factor and c.run_len == 4
               for c in nb.constraints)

    # ORBP present and wired to the given inner block
    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.perm_factor is perm_factor
    assert orbp.inner_block is inner_2x2
    assert orbp.run_len == 4
    assert orbp.cross_size == 4

    # total_windows = K * |group| = 2 * 2 = 4; run_len = 4 => 16 trials
    assert nb.trials_per_sample() == 16

    # ExactlyK for each perm level: per_perm_windows * run_len
    per_perm_windows = (2 * 2) // 2  # total_windows // K = 2
    for lvl in perm_factor.levels:
        assert has_exactly_k(nb, perm_factor, lvl, per_perm_windows * 4)

    # --------- Build a VALID sample matching the chosen permutations per window
    A, B = [f for f in inner_2x2.design if getattr(f, "name", None) in ("A", "B")]
    prod = combos_in_product_order([A, B])

    level2perm = {lvl.name: nb.get_trial_permutation_for_level(lvl) for lvl in perm_factor.levels}
    window_plan = [("perm_0", "G1"), ("perm_1", "G2"), ("perm_0", "G1"), ("perm_1", "G2")]

    A_vals, B_vals, group_vals, order_vals = [], [], [], []
    for perm_name, gname in window_plan:
        p = level2perm[perm_name]
        group_vals.extend([gname] * 4)        # constant in window
        order_vals.extend([perm_name] * 4)    # constant in window
        for idx in p:
            a_name, b_name = prod[idx]
            A_vals.append(a_name)
            B_vals.append(b_name)

    valid_sample = {"A": A_vals, "B": B_vals, "group": group_vals, perm_key_obj: order_vals}
    assert orbp.potential_sample_conforms(valid_sample, nb)

    # Violate permutation in window #2 by swapping the last two trials.
    bad_sample = {k: (v[:] if isinstance(v, list) else v) for k, v in valid_sample.items()}
    bad_sample["A"][6], bad_sample["A"][7] = bad_sample["A"][7], bad_sample["A"][6]
    bad_sample["B"][6], bad_sample["B"][7] = bad_sample["B"][7], bad_sample["B"][6]
    assert not orbp.potential_sample_conforms(bad_sample, nb)

    # Violate constancy: change permutation level mid-window #3.
    bad2 = {k: (v[:] if isinstance(v, list) else v) for k, v in valid_sample.items()}
    bad2[perm_key_obj][8] = "perm_1"
    constancy = next(c for c in nb.constraints if isinstance(c, ConstantInWindows) and c.factor is perm_factor)
    assert not constancy.potential_sample_conforms(bad2, nb)


def test_permuted_mode_k1_small(inner_2x2):
    """Permuted mode with K=1 (minimal total trials)."""
    cohort = Factor("cohort", levels(["C"]))  # single-level external
    nb = NestedBlock(
        design=[cohort, inner_2x2],
        crossing=[inner_2x2, cohort],
        constraints=[],
        num_permutations=1,
        permutation_factor_name="order",
    )
    assert nb.trials_per_sample() == 4

    perm_factor = nb.perm_factor
    assert any(isinstance(c, ConstantInWindows) and c.factor is perm_factor and c.run_len == 4
               for c in nb.constraints)

    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.perm_factor is perm_factor
    assert orbp.cross_size == 4
    assert orbp.run_len == 4
    assert any(isinstance(c, ExactlyK) and getattr(c.level, "factor", None) is perm_factor and c.k == 4
               for c in nb.constraints)


def test_permuted_mode_with_joint_external_cross(inner_2x2):
    """
    Permuted mode with an external factor that IS jointly crossed:
    - inner block listed in crossing (perm mode)
    - every Factor in design also in crossing (rule)
    - when jointly crossed, no extra ExactlyK per external level is needed
    """
    group = Factor("group", levels(["G1", "G2"]))
    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],   # jointly crossed
        constraints=[],
        num_permutations=2,
        permutation_factor_name="order",
    )

    perm_factor = nb.perm_factor
    assert any(isinstance(c, ConstantInWindows) and c.factor is perm_factor and c.run_len == 4
               for c in nb.constraints)

    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.perm_factor is perm_factor
    assert orbp.cross_size == 4 and orbp.run_len == 4

    # Trials: K=2 × |group|=2 windows × run_len=4
    assert nb.trials_per_sample() == 16

    per_perm_windows = (2 * 2) // 2  # 2 windows each
    for lvl in perm_factor.levels:
        assert has_exactly_k(nb, perm_factor, lvl, per_perm_windows * 4)

    # Because `group` is jointly crossed, there should be no ExactlyK per group level.
    assert not any(isinstance(c, ExactlyK) and getattr(c.level, "factor", None) is group
                   for c in nb.constraints)


def test_permuted_mode_with_inner_preamble(inner_2x2):
    """
    Inner block uses a Transition (preamble > 0) and excludes one level,
    so crossing_size=2 and preamble=1 -> inner total = 3.
    """
    X = Factor("X", levels(["x1", "x2"]))
    repX = Factor("repX", [
        DerivedLevel("yes", Transition(lambda xs: xs[0] == xs[-1], [X])),
        DerivedLevel("no",  Transition(lambda xs: xs[0] != xs[-1], [X])),
    ])
    inner_with_preamble = CrossBlock(
        design=[X, repX],
        crossing=[X, repX],
        constraints=[Exclude((repX, "yes"))],   # make it non-implied
    )

    # One crossing; Transition induces preamble=1; exclude reduces crossing_size to 2
    assert len(inner_with_preamble.crossings) == 1
    assert inner_with_preamble.crossing_size(inner_with_preamble.crossings[0]) == 2
    assert inner_with_preamble.preamble_size(inner_with_preamble.crossings[0]) == 1
    assert inner_with_preamble.trials_per_sample() == 3

    # Wrap in permuted mode with a trivial external factor in the crossing
    cohort = Factor("cohort", levels(["C"]))  # satisfies “factor in design must be in crossing”
    nb = NestedBlock(
        design=[cohort, inner_with_preamble],
        crossing=[inner_with_preamble, cohort],
        constraints=[],
        num_permutations=1,
        permutation_factor_name="order",
    )

    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.cross_size == 2
    assert orbp.preamble == 1
    assert orbp.run_len == 3
    assert nb.trials_per_sample() == 3  # one window × run_len


# ======================================================================
# NESTED–NESTED (NON-PERMUTED)
# ======================================================================

def test_nested_nested_block_small(inner_2x2):
    """day -> (session -> inner_2x2), both non-permuted."""
    session = Factor("session", levels(["s1", "s2"]))
    inner_nb = NestedBlock(design=[session, inner_2x2], crossing=[session], constraints=[])
    assert inner_nb.trials_per_sample() == 8
    assert any(isinstance(c, ConstantInWindows) and c.factor is session and c.run_len == 4
               for c in inner_nb.constraints)

    day = Factor("day", levels(["d1", "d2"]))
    outer_nb = NestedBlock(design=[day, inner_nb], crossing=[day], constraints=[])
    assert outer_nb.trials_per_sample() == 16
    assert any(isinstance(c, ConstantInWindows) and c.factor is day and c.run_len == 8
               for c in outer_nb.constraints)


def test_nested_nested_smoke(inner_2x2):
    """Tiny nested-nested: outer(nested(inner_2x2))—both non-permuted and minimal."""
    session = Factor("session", levels(["s1", "s2"]))
    mid = NestedBlock(design=[session, inner_2x2], crossing=[session], constraints=[])
    assert mid.trials_per_sample() == 8

    day = Factor("day", levels(["d1"]))
    outer = NestedBlock(design=[day, mid], crossing=[day], constraints=[])
    assert outer.trials_per_sample() == 8


# ======================================================================
# VALIDATION / ERRORS
# ======================================================================

def test_permuted_mode_rejects_bad_num_permutations(inner_2x2):
    g = Factor("g", levels(["x", "y"]))
    with pytest.raises(ValueError):
        NestedBlock(design=[g, inner_2x2], crossing=[inner_2x2, g], num_permutations=0)
    with pytest.raises(ValueError):
        # 2x2 inner crossing => 4 combos => 4! = 24 permutations; 25 invalid
        NestedBlock(design=[g, inner_2x2], crossing=[inner_2x2, g], num_permutations=25)


def test_nested_block_requires_single_inner_block_in_design(inner_2x2):
    """Multiple inner blocks in design should raise (blocks needn't be in crossing)."""
    other_inner = CrossBlock(design=inner_2x2.orig_design,
                             crossing=inner_2x2.orig_crossings[0],
                             constraints=[])
    with pytest.raises(ValueError):
        NestedBlock(design=[inner_2x2, other_inner], crossing=[inner_2x2])


def test_nested_block_requires_all_factors_in_crossing(inner_2x2):
    """Any Factor in design must be included in crossing (both modes)."""
    task = Factor("task", levels(["T1", "T2"]))
    with pytest.raises(ValueError):
        NestedBlock(design=[task, inner_2x2], crossing=[], constraints=[])

    group = Factor("group", levels(["G1", "G2"]))
    with pytest.raises(ValueError):
        NestedBlock(design=[group, inner_2x2], crossing=[inner_2x2], constraints=[], num_permutations=2)


def test_design_factor_must_be_in_crossing_raises(inner_2x2):
    """Duplicate explicit check for the new rule in non-permuted mode."""
    task = Factor("task", levels(["T1", "T2"]))
    with pytest.raises(ValueError):
        NestedBlock(design=[task, inner_2x2], crossing=[inner_2x2], constraints=[])
