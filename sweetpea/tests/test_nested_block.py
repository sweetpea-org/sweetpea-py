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

    # ---- Geometry ----
    assert nb.trials_per_sample() == 2 * 4  # 2 task levels × inner block

    # NestedMode should expose a runtime stitch spec
    spec = nb.external_stitch_spec()
    assert spec is not None
    assert spec["run_len"] == 4
    assert task in spec["external_design"]

    # No CNF-level ConstantInWindows anymore
    from sweetpea._internal.constraint import ConstantInWindows
    assert not any(
        isinstance(c, ConstantInWindows) and c.factor is task
        for c in nb.constraints
    )

    # ---- Generate stitched sample via public API ----
    experiments = synthesize_trials(nb, samples=1)
    sample = experiments[0]

    # ---- Verify constancy per window AFTER stitching ----
    run_len = spec["run_len"]
    for w in range(0, len(sample["task"]), run_len):
        window = sample["task"][w:w + run_len]
        assert len(set(window)) == 1




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


def test_nested_mode_minimum_trials_rounds_up(inner_2x2):
    task = Factor("task", levels(["T1", "T2"]))
    nb = NestedBlock(design=[task, inner_2x2], crossing=[task], constraints=[])

    nb.constraints.append(MinimumTrials(6))  # lower than required 8

    experiments = synthesize_trials(nb, samples=1)
    sample = experiments[0]

    # Still produces valid geometry
    assert len(sample["task"]) == 8




# ======================================================================
# PERMUTED NESTED MODE (inner listed in crossing; all Factors from design in crossing)
# ======================================================================

def test_permuted_mode_enforces_permutation_and_windows(inner_2x2):
    group = Factor("group", levels(["G1", "G2"]))

    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],   # permuted mode
        constraints=[],
        num_permutations=2
    )

    # ---- Hidden permutation factor ----
    perm_factor = nb.perm_factor
    perm_key_obj = perm_factor.name  # HiddenName

    # ---- Geometry ----
    # total_windows = K * |group| = 2 * 2 = 4
    # run_len = inner block size = 4
    assert nb.trials_per_sample() == 16

    # ---- ConstantInWindows for permutation factor ----
    from sweetpea._internal.constraint import ConstantInWindows, OrderRunsByPermutation

    constancy = next(
        c for c in nb.constraints
        if isinstance(c, ConstantInWindows) and c.factor is perm_factor
    )
    assert constancy.run_len == 4

    # ---- OrderRunsByPermutation present ----
    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.perm_factor is perm_factor
    assert orbp.inner_block is inner_2x2
    assert orbp.cross_size == 4
    assert orbp.run_len == 4

    # ---- Build a valid sample consistent with permutations ----
    A, B = [f for f in inner_2x2.design if f.name in ("A", "B")]
    prod = combos_in_product_order([A, B])

    level2perm = {
        lvl.name: nb.get_trial_permutation_for_level(lvl)
        for lvl in perm_factor.levels
    }

    # 4 windows
    window_plan = [
        ("perm_0", "G1"),
        ("perm_1", "G2"),
        ("perm_0", "G1"),
        ("perm_1", "G2"),
    ]

    A_vals, B_vals, group_vals, order_vals = [], [], [], []
    for perm_name, gname in window_plan:
        perm = level2perm[perm_name]

        group_vals.extend([gname] * 4)
        order_vals.extend([perm_name] * 4)

        for idx in perm:
            a, b = prod[idx]
            A_vals.append(a)
            B_vals.append(b)

    valid_sample = {
        "A": A_vals,
        "B": B_vals,
        "group": group_vals,
        perm_key_obj: order_vals,
    }

    assert orbp.potential_sample_conforms(valid_sample, nb)

    # ---- Violate permutation inside a window ----
    bad = {k: v[:] for k, v in valid_sample.items()}
    bad["A"][6], bad["A"][7] = bad["A"][7], bad["A"][6]
    bad["B"][6], bad["B"][7] = bad["B"][7], bad["B"][6]

    assert not orbp.potential_sample_conforms(bad, nb)

    # ---- Violate constancy of permutation factor ----
    bad2 = {k: v[:] for k, v in valid_sample.items()}
    bad2[perm_key_obj][8] = "perm_1"

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


def test_permuted_mode_with_joint_external_cross(inner_2x2):
    """
    Permuted mode with a jointly crossed external factor:
    - inner block listed in crossing (perm mode)
    - every Factor in design also in crossing
    - no ExactlyK constraints are required
    """
    group = Factor("group", levels(["G1", "G2"]))

    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],
        constraints=[],
        num_permutations=2
    )

    perm_factor = nb.perm_factor

    # Permutation factor constant per window
    from sweetpea._internal.constraint import ConstantInWindows, OrderRunsByPermutation

    assert any(
        isinstance(c, ConstantInWindows)
        and c.factor is perm_factor
        and c.run_len == 4
        for c in nb.constraints
    )

    # OrderRunsByPermutation present
    orbp = next(c for c in nb.constraints if isinstance(c, OrderRunsByPermutation))
    assert orbp.perm_factor is perm_factor
    assert orbp.cross_size == 4
    assert orbp.run_len == 4

    # Geometry: K=2 × |group|=2 windows × run_len=4
    assert nb.trials_per_sample() == 16

    # No ExactlyK constraints at all (balancing is runtime-managed)
    from sweetpea._internal.constraint import ExactlyK
    assert not any(isinstance(c, ExactlyK) for c in nb.constraints)



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
    assert orbp.preamble == 0         
    assert orbp.run_len == 2            
    assert nb.trials_per_sample() == 3  # one window × run_len


# ======================================================================
# NESTED–NESTED (NON-PERMUTED)
# ======================================================================

# Currently not supported yet
# def test_nested_nested_block_small(inner_2x2):
#     """day -> (session -> inner_2x2), both non-permuted."""
#     session = Factor("session", levels(["s1", "s2"]))
#     inner_nb = NestedBlock(design=[session, inner_2x2], crossing=[session], constraints=[])
#     assert inner_nb.trials_per_sample() == 8
#     assert any(isinstance(c, ConstantInWindows) and c.factor is session and c.run_len == 4
#                for c in inner_nb.constraints)

#     day = Factor("day", levels(["d1", "d2"]))
#     outer_nb = NestedBlock(design=[day, inner_nb], crossing=[day], constraints=[])
#     assert outer_nb.trials_per_sample() == 16
#     assert any(isinstance(c, ConstantInWindows) and c.factor is day and c.run_len == 8
#                for c in outer_nb.constraints)


# def test_nested_nested_smoke(inner_2x2):
#     """Tiny nested-nested: outer(nested(inner_2x2))—both non-permuted and minimal."""
#     session = Factor("session", levels(["s1", "s2"]))
#     mid = NestedBlock(design=[session, inner_2x2], crossing=[session], constraints=[])
#     assert mid.trials_per_sample() == 8

#     day = Factor("day", levels(["d1"]))
#     outer = NestedBlock(design=[day, mid], crossing=[day], constraints=[])
#     assert outer.trials_per_sample() == 8


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


def test_nested_block_crossing_rules(inner_2x2):
    """
    Updated rules:
    - Non-permuted mode: crossing cannot be empty (must define window repetition)
    - Permuted mode: crossing must include the inner block
    - External factors do NOT need to be in crossing
    """

    # ---------- Non-permuted mode ----------
    task = Factor("task", levels(["T1", "T2"]))

    # Empty crossing is valid (no window structure)
    # with pytest.raises(ValueError):
    NestedBlock(design=[task, inner_2x2], crossing=[], constraints=[])

    # External factor may appear alone
    NestedBlock(design=[task, inner_2x2], crossing=[task], constraints=[])

    # ---------- Permuted mode ----------
    group = Factor("group", levels(["G1", "G2"]))

    # Permuted mode requires inner block in crossing
    with pytest.raises(ValueError):
        NestedBlock(
            design=[group, inner_2x2],
            crossing=[group],        # inner block missing
            constraints=[],
            num_permutations=2
        )

    # Inner block alone is sufficient
    NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2],
        constraints=[],
        num_permutations=2
    )

    # Inner block + external factor also valid
    NestedBlock(
        design=[group, inner_2x2],
        crossing=[inner_2x2, group],
        constraints=[],
        num_permutations=2
    )


def test_weighted_external_levels_scale_windows(inner_2x2):
    """
    Weighted external factor in non-permuted NestedBlock.
    External scaling is applied at runtime via stitching,
    not fully enforced in CNF.
    """

    # Inner has 4 trials (2x2)
    group = Factor("group", [
        SimpleLevel("G1", weight=3),
        SimpleLevel("G2", weight=1)
    ])

    nb = NestedBlock(
        design=[group, inner_2x2],
        crossing=[],          # non-permuted, no external crossing
        constraints=[]
    )

    # Total windows = 3 + 1 = 4, run_len = 4
    assert nb.trials_per_sample() == 16

    # ---- Build a valid stitched sample manually ----
    A, B = [f for f in nb.design if getattr(f, "name", None) in ("A", "B")]
    prod = combos_in_product_order([A, B])  # 4 inner trials

    window_plan = ["G1", "G1", "G1", "G2"]

    group_vals, A_vals, B_vals = [], [], []
    for g in window_plan:
        group_vals.extend([g] * 4)
        for a_name, b_name in prod:
            A_vals.append(a_name)
            B_vals.append(b_name)

    sample = {
        "group": group_vals,
        "A": A_vals,
        "B": B_vals
    }

    # External correctness must hold AFTER stitching
    stitched = nb.add_implied_levels(sample)

    # Group must be constant per window
    for w in range(4):
        start = w * 4
        assert len(set(stitched["group"][start:start+4])) == 1

    # Inner structure must repeat correctly
    for w in range(4):
        start = w * 4
        assert list(zip(
            stitched["A"][start:start+4],
            stitched["B"][start:start+4]
        )) == prod



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

    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    assert exps  # should generate some experiments
    # At least one experiment should contain k 'a1's in a row across a boundary
    assert any(has_run(get_series(exp, "A"), target_level, k) for exp in exps)

def test_randomgen_nestedblock_smoke_non_permuted():
    """
    RandomGen smoke test for non-permuted NestedBlock.

    This test only checks:
    - sampling succeeds
    - correct total number of trials
    - values come from valid domains

    It does NOT assert miniblock constancy, which is enforced only
    by CNF-based generators.
    """
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

        # Shape check
        assert len(sess_vals) == total_len

        # Domain check (values must be valid levels)
        assert set(sess_vals).issubset({"s1", "s2"})


def test_sampling_strategies_return_expected_number_of_experiments():
    """
    Enumerative generators should produce multiple valid experiments.
    Randomized generators should return the requested number of samples.
    """
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])
    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [inner, session], num_permutations=2)

    import importlib.util

    def unique_experiments(exps):
        return {
            tuple(tuple(v) for v in exp.values())
            for exp in exps
        }

    enumerated_sets = []

    if importlib.util.find_spec("gurobipy") is not None:
        from sweetpea._internal.sampling_strategy.iterate_ilp import IterateILPGen
        exps = synthesize_trials(nb, 1000, sampling_strategy=IterateILPGen)
        enumerated_sets.append(unique_experiments(exps))

    from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateSATGen)
    enumerated_sets.append(unique_experiments(exps))

    from sweetpea._internal.sampling_strategy.iterate import IterateGen
    exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    enumerated_sets.append(unique_experiments(exps))

    # Each enumerative generator must produce >1 unique experiment
    for s in enumerated_sets:
        assert len(s) > 1

    # Randomized strategies: must return requested number
    from sweetpea._internal.sampling_strategy.cmsgen import CMSGen
    from sweetpea._internal.sampling_strategy.unigen import UniGen
    from sweetpea._internal.sampling_strategy.uniform import UniformGen

    # DW: I was not sure how we come up with this number. This would be my next investigation
    # for Gen in (CMSGen, UniformGen, UniGen):
    exps = synthesize_trials(nb, 1000, sampling_strategy=CMSGen)
    assert len(exps) == 1000

    exps = synthesize_trials(nb, 1000, sampling_strategy=UniGen)
    assert len(exps) == 1000
    
    exps = synthesize_trials(nb, 1000, sampling_strategy=UniformGen)
    assert len(exps) == 1000


# This is not supported anymore, since we move the CNF of external factors to runtime. Not sure it is the best move though.
# def test_sampling_strategies_return_expected_number_of_experiments():
#     """Different generators should produce the expected number of experiments."""
#     A = Factor("A", ["a1", "a2"])
#     B = Factor("B", ["b1", "b2"])
#     inner = CrossBlock([A, B], [A, B], [])
#     session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
#     nb = NestedBlock([session, inner], [inner, session], num_permutations=2)

#     # Enumerative strategies should return all distinct experiments (36 total)
#     import importlib.util

#     if importlib.util.find_spec("gurobipy") is not None:
#         from sweetpea._internal.sampling_strategy.iterate_ilp import IterateILPGen
#         exps = synthesize_trials(nb, 1000, sampling_strategy=IterateILPGen)
#         assert len(exps) == 36

#     from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
#     exps = synthesize_trials(nb, 1000, sampling_strategy=IterateSATGen)
#     assert len(exps) == 36

#     exps = synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
#     assert len(exps) == 36

#     from sweetpea._internal.sampling_strategy.cmsgen import CMSGen
#     from sweetpea._internal.sampling_strategy.unigen import UniGen
#     from sweetpea._internal.sampling_strategy.uniform import UniformGen
#     for Gen in (CMSGen, UniformGen, UniGen):
#         exps = synthesize_trials(nb, 1000, sampling_strategy=Gen)
#         assert len(exps) == 1000

def test_nestedblock_refreshes_permutations_each_time():
    """Permuted NestedBlock should refresh its permutation map between samples."""
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    inner = CrossBlock([A, B], [A, B], [])
    session = Factor("session", [SimpleLevel("s1"), SimpleLevel("s2")])
    nb = NestedBlock([session, inner], [inner, session], num_permutations=2)

    # First sample
    synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    perm_map_1 = dict(nb._perm_map)

    # Second sample should reshuffle the permutation mapping
    synthesize_trials(nb, 1000, sampling_strategy=IterateGen)
    perm_map_2 = dict(nb._perm_map)

    assert len(perm_map_1) == 2
    assert all(isinstance(v, tuple) for v in perm_map_1.values())
    assert perm_map_1 != perm_map_2, f"Expected refresh, got identical maps: {perm_map_1}"