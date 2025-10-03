import pytest

from sweetpea._internal.cross_block import CrossBlock, NestedBlock
from sweetpea._internal.constraint import (
    MinimumTrials,
    ConstantInWindows,
    OrderRunsByPermutation,
    ExactlyK,
    AtMostKInARow,
    Exclude,
    ExactlyKInARow,
    Pin
)
from sweetpea._internal.primitive import Factor, SimpleLevel, DerivedLevel, Transition
from sweetpea._internal.main import synthesize_trials

import shutil
from sweetpea._internal.sampling_strategy.iterate import IterateGen


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

def has_run(vals, target, length):
    """
    Return True if `vals` contains a contiguous run of `target`
    of at least `length` occurrences.
    """
    run = 0
    for v in vals:
        name = v if isinstance(v, str) else getattr(v, "name", v)
        run = run + 1 if name == target else 0
        if run >= length:
            return True
    return False


def get_series(exp, key: str):
    """
    Return the values for factor `key` in a sampled experiment.
    Tries plain dict key first, then falls back to matching Factor.name.
    """
    if key in exp:
        return exp[key]
    for k in exp:
        if getattr(k, "name", None) == key or str(getattr(k, "name", "")) == key:
            return exp[k]
    raise KeyError(key)


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
        num_permutations=2         # K = 2
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
        num_permutations=1
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
        num_permutations=2
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
        num_permutations=1
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


def test_weighted_external_levels_scale_windows(inner_2x2):
    """
    Regression test: weighted external factor in non-permuted NestedBlock.
    Expect total windows = sum(level weights), and trials_per_sample =
    run_len(inner) * total_windows. Also check ConstantInWindows holds.
    """
    # Inner has 4 trials (2x2), preamble = 0  -> run_len = 4 
    # External factor with weights: 3 windows of G1, 1 window of G2 -> total 4 windows.
    group = Factor("group", [SimpleLevel("G1", weight=3), SimpleLevel("G2", weight=1)])

    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[group],           # non-permuted mode (inner not in crossing)
        constraints=[]
    )

    # Geometry checks
    assert any(isinstance(c, ConstantInWindows) and c.factor is group and c.run_len == 4
               for c in nb.constraints)
    # MinimumTrials should be (3+1) windows * 4 trials/run = 16
    assert any(isinstance(c, MinimumTrials) and c.trials == 16 for c in nb.constraints)
    assert nb.trials_per_sample() == 16

    # Build a valid sample: 3 windows of G1, then 1 window of G2.
    # Within each window, reuse the inner 2x2 product once.
    A, B = [f for f in nb.design if getattr(f, "name", None) in ("A", "B")]
    prod = combos_in_product_order([A, B])   # 4 tuples in product order

    group_vals, A_vals, B_vals = [], [], []
    window_plan = ["G1", "G1", "G1", "G2"]  # matches weights 3:1
    for g in window_plan:
        group_vals.extend([g] * 4)          # constant in each 4-trial window
        for a_name, b_name in prod:
            A_vals.append(a_name)
            B_vals.append(b_name)

    sample = {"group": group_vals, "A": A_vals, "B": B_vals}

    # Constancy must pass on the constructed sample.
    cwin = next(c for c in nb.constraints if isinstance(c, ConstantInWindows) and c.factor is group)
    assert cwin.potential_sample_conforms(sample, nb)


@pytest.mark.parametrize("target_level,k", [("a1", 4)])
def test_permuted_mode_can_produce_k_in_a_row(inner_2x2, target_level, k):
    """
    Construct a permuted NestedBlock and force specific permutations
    that produce a run of `k` identical A levels across a window boundary.
    This checks that OrderRunsByPermutation plus ConstantInWindows
    allow such a construction.
    """
    group = Factor("group", levels(["G1", "G2"]))
    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],
        num_permutations=2
    )

    # Product order for inner 2×2 block
    A, B = [f for f in inner_2x2.design if f.name in ("A", "B")]
    product = combos_in_product_order([A, B])

    # Force mapping so that perm_0 ends with two a1s and perm_1 begins with two a1s
    perm_factor = nb.perm_factor
    lvls = list(perm_factor.levels)
    mapping = {
        lvls[0]: (2, 3, 0, 1),  # ends with (a1, b?)
        lvls[1]: (0, 1, 2, 3),  # begins with (a1, b?)
    }
    nb._perm_map.clear()
    nb._perm_map.update(mapping)

    # Build sample: four windows, alternating perm_0/perm_1 × groups
    window_plan = [(lvls[0], "G1"), (lvls[1], "G1"), (lvls[0], "G2"), (lvls[1], "G2")]
    A_vals, B_vals, group_vals, order_vals = [], [], [], []
    for perm_lvl, gname in window_plan:
        p = nb.get_trial_permutation_for_level(perm_lvl)
        group_vals.extend([gname] * 4)
        order_vals.extend([perm_lvl.name] * 4)
        for idx in p:
            a_name, b_name = product[idx]
            A_vals.append(a_name)
            B_vals.append(b_name)

    perm_key = perm_factor.name
    sample = {"A": A_vals, "B": B_vals, "group": group_vals, perm_key: order_vals}

    # Constraints should accept this construction
    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    if hasattr(orbp, "level2perm"):  # keep internal mapping consistent
        orbp.level2perm.clear()
        orbp.level2perm.update(mapping)

    assert orbp.potential_sample_conforms(sample, nb)
    for c in nb.constraints:
        if isinstance(c, ConstantInWindows) and c.factor in (perm_factor, group):
            assert c.potential_sample_conforms(sample, nb)

    # And the A sequence should really have k consecutive a1s
    assert has_run(A_vals, target_level, k), f"A sequence lacked {k} consecutive {target_level!r}"

import os
# from sweetpea._internal.core.generate.tools.executables import CRYPTOMINISAT_EXE
# has_cms = os.path.exists(CRYPTOMINISAT_EXE) or shutil.which("cryptominisat5")

# @pytest.mark.skipif(not has_cms, reason="cryptominisat5 is required for SAT-based sampling")
@pytest.mark.parametrize("target_level,k", [("a1", 4)])
def test_non_permuted_nested_can_yield_runs_across_windows(target_level, k):
    """
    Regression for reviewer’s 'four in a row' example:

    Inner block enforces ExactlyKInARow(2, A='a1') within a window.
    A non-permuted NestedBlock repeats that block, so a long run can
    appear if one window ends with 'a1 a1' and the next begins with 'a1 a1'.
    """
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [ExactlyKInARow(2, (A, "a1"))])

    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [session], constraints=[])

    res = IterateGen.sample(nb, sample_count=1000)
    exps = res.samples
    assert exps  # should generate some experiments

    # At least one experiment should contain k 'a1's in a row across a boundary
    assert any(has_run(get_series(exp, "A"), target_level, k) for exp in exps)

def test_randomgen_nestedblock_smoke_non_permuted():
    """RandomGen should respect geometry and constancy in a simple non-permuted NestedBlock."""
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])
    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [session], [])

    run_len = inner.trials_per_sample()   # 4
    total_len = 2 * run_len               # two session levels

    from sweetpea._internal.sampling_strategy.random import RandomGen
    result = RandomGen.sample(nb, sample_count=5)
    assert len(result.samples) == 5

    for exp in result.samples:
        sess_vals = get_series(exp, "session")
        assert len(sess_vals) == total_len
        # Each window of size run_len must have a constant session label
        for start in range(0, total_len, run_len):
            window = sess_vals[start:start + run_len]
            assert all(val == window[0] for val in window)

def test_sampling_strategies_return_expected_number_of_experiments():
    """Different generators should produce the expected number of experiments."""
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])
    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [inner, session], num_permutations=2)


    # Enumerative strategies should return all distinct experiments (36 total)
    import importlib.util

    if importlib.util.find_spec("gurobipy") is not None:
        from sweetpea._internal.sampling_strategy.iterate_ilp import IterateILPGen
        exps = synthesize_trials(nb, 1000, sampling_strategy=IterateILPGen)
        assert len(exps) == 36
    if has_cms:
        from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
        exps = synthesize_trials(nb, 1000, sampling_strategy=IterateSATGen)
        assert len(exps) == 36

        exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
        assert len(exps) == 36

    if has_cms:
        from sweetpea._internal.sampling_strategy.cmsgen import CMSGen
        from sweetpea._internal.sampling_strategy.unigen import UniGen
        from sweetpea._internal.sampling_strategy.uniform import UniformGen
        for Gen in (CMSGen, UniformGen, UniGen):
            exps = synthesize_trials(nb, 1000, sampling_strategy=Gen)
            assert len(exps) == 1000



# @pytest.mark.skipif(not has_cms, reason="cryptominisat5 is required for SAT-based sampling")
def test_nestedblock_refreshes_permutations_each_time():
    """Permuted NestedBlock should refresh its permutation map between samples."""
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])
    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [inner, session], num_permutations=2)

    # First sample
    IterateGen.sample(nb, 1)
    perm_map_1 = dict(nb._perm_map)

    # Second sample should reshuffle the permutation mapping
    IterateGen.sample(nb, 1)
    perm_map_2 = dict(nb._perm_map)

    assert len(perm_map_1) == 2
    assert all(isinstance(v, tuple) for v in perm_map_1.values())
    assert perm_map_1 != perm_map_2, f"Expected refresh, got identical maps: {perm_map_1}"