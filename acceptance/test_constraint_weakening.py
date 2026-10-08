import pytest

from sweetpea import *
from sweetpea._internal.block import BlockGeometry
from sweetpea._internal.constraint import CoverAllCombinations


def _stroop(n):
    """Build a Stroop-style design with n colors/words and a derived congruency
    factor, crossing [congruency, color] (word left free)."""
    colors = ['red', 'green', 'blue', 'yellow', 'purple'][:n]
    color = Factor('color', colors)
    word = Factor('word', colors)
    congruency = Factor('congruency', [
        DerivedLevel('con', WithinTrial(lambda c, w: c == w, [color, word])),
        DerivedLevel('incon', WithinTrial(lambda c, w: c != w, [color, word])),
    ])
    return colors, color, word, congruency


def _build(n, make_caps):
    """A covered Stroop block, plus the caps as constructed, so that a test can
    read back what a relaxation did to them."""
    colors, color, word, congruency = _stroop(n)
    caps = make_caps(color, word)
    block = CrossBlock([congruency, color, word], [congruency, color],
                       [CoverAllCombinations(color, word)] + caps)
    return colors, block, caps


def _covers_all(experiment, colors):
    all_pairs = set((c, w) for c in colors for w in colors)
    return set(zip(experiment['color'], experiment['word'])) == all_pairs


# In 3-color Stroop the red-red cell forces one word-red per instance and two
# free combos (green-red, blue-red) contain word-red, so a cap's demand at K
# instances is K + 2. Coverage settles at K=2, hence a demand of 4.
_DEMAND = 4


# ~~~~~~~~~~~~ Relax argument checking ~~~~~~~~~~~~

def test_relax_rejects_unsupported_constraint():
    _, color, word, _ = _stroop(3)
    with pytest.raises(ValueError) as info:
        Relax(Pin(0, (word, 'red')), by=1)
    assert 'ExactlyK' in str(info.value)


@pytest.mark.parametrize('by', [0, -1, True, 1.5, 'one'])
def test_relax_rejects_bad_budget(by):
    _, color, word, _ = _stroop(3)
    with pytest.raises(ValueError):
        Relax(ExactlyK(3, (word, 'red')), by=by)


def test_relax_leaves_its_argument_alone():
    _, color, word, _ = _stroop(3)
    original = ExactlyK(3, (word, 'red'))
    relaxed = Relax(original, by=1)
    assert relaxed is not original
    assert original.relaxation is None
    assert relaxed.relaxation.by == 1
    assert original.k == relaxed.k == 3


def test_relax_keeps_the_designs_factor():
    # A deep copy would clone the level's factor and leave the constraint
    # pointing outside the design.
    _, color, word, _ = _stroop(3)
    relaxed = Relax(ExactlyK(3, (word, 'red')), by=1)
    assert relaxed.level.factor is word


# ~~~~~~~~~~~~ Repair, both failure sites ~~~~~~~~~~~~

@pytest.mark.parametrize('written,by', [
    (1, 3),   # below the K=1 floor: unreconcilable at any K without widening
    (3, 1),   # clears the floor, but every K the scan reaches overshoots it
])
def test_relax_widens_cap_to_the_demand(written, by):
    _, block, caps = _build(3, lambda c, w: [Relax(ExactlyK(written, (w, 'red')), by=by)])
    relaxation = caps[0].relaxation
    assert relaxation.original_k == written
    assert relaxation.applied_k == _DEMAND
    assert caps[0].k == _DEMAND
    assert block._trials_per_sample() == 12


@pytest.mark.parametrize('written,by', [(1, 1), (1, 2)])
def test_relax_over_budget_errors(written, by):
    with pytest.raises(ValueError) as info:
        _build(3, lambda c, w: [Relax(ExactlyK(written, (w, 'red')), by=by)])
    message = str(info.value)
    assert str(_DEMAND) in message
    assert 'Relax' in message


def test_cap_within_reach_is_left_alone():
    _, block, caps = _build(3, lambda c, w: [Relax(ExactlyK(4, (w, 'red')), by=1)])
    assert caps[0].relaxation.applied_k is None
    assert caps[0].k == 4
    assert block.applied_relaxations == []


def test_unwrapped_cap_still_errors():
    with pytest.raises(ValueError):
        _build(3, lambda c, w: [ExactlyK(1, (w, 'red'))])


def test_unwrapped_cap_that_fits_is_unaffected():
    _, block, _ = _build(3, lambda c, w: [ExactlyK(4, (w, 'red'))])
    assert block._trials_per_sample() == 12
    assert block.applied_relaxations == []


# ~~~~~~~~~~~~ Sustain scaling ~~~~~~~~~~~~

def test_budget_scales_with_sustained_k():
    # A budget counts the same occurrences k does, so sustaining the block has
    # to multiply both or a stated tolerance silently changes size.
    _, color, word, _ = _stroop(3)
    relaxed = Relax(ExactlyK(2, (word, 'red')), by=1)
    relaxed.init_within_block(BlockGeometry(4, 0, {}))
    relaxed.sustain_within_block(3)
    assert relaxed.k == 6
    assert relaxed.relaxation.by == 3


# ~~~~~~~~~~~~ Reporting ~~~~~~~~~~~~

def test_relaxation_is_reported_at_construction(capsys):
    _, block, _ = _build(3, lambda c, w: [Relax(ExactlyK(3, (w, 'red')), by=1)])
    out = capsys.readouterr().out
    assert "relaxed from 3 to {}".format(_DEMAND) in out
    assert 'word red' in out
    assert block.applied_relaxations


def test_relaxation_is_restated_with_the_results(capsys):
    colors, block, _ = _build(3, lambda c, w: [Relax(ExactlyK(3, (w, 'red')), by=1)])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    capsys.readouterr()
    print_experiments(block, experiments)
    assert "relaxed from 3 to {}".format(_DEMAND) in capsys.readouterr().out


# ~~~~~~~~~~~~ End to end ~~~~~~~~~~~~

def test_relaxed_design_synthesizes():
    colors, block, caps = _build(3, lambda c, w: [Relax(ExactlyK(3, (w, 'red')), by=1)])
    experiments = synthesize_trials(block, 2, sampling_strategy=IterateGen)
    assert experiments
    for e in experiments:
        assert _covers_all(e, colors)
        assert e['word'].count('red') == caps[0].relaxation.applied_k


# ~~~~~~~~~~~~ Composition ~~~~~~~~~~~~

def _simple(constraints):
    color = Factor('color', ['red', 'green', 'blue'])
    word = Factor('word', ['red', 'green', 'blue'])
    return color, word, CrossBlock([color, word], [color],
                                   [CoverAllCombinations(color, word)]
                                   + constraints(color, word))


def test_relax_on_a_whole_factor_reaches_every_level():
    # A cap named on a factor desugars into one per level, and the copies carry
    # the authorization; the constraint the caller holds stays as written.
    cap = []

    def make(color, word):
        cap.append(Relax(ExactlyK(2, word), by=1))
        return cap

    color, word, block = _simple(make)
    assert len(block.applied_relaxations) == 3
    for level in ('red', 'green', 'blue'):
        assert any("word {}".format(level) in m for m in block.applied_relaxations)
    assert cap[0].k == 2
    assert cap[0].relaxation.applied_k is None


def test_relax_alongside_several_coverage_constraints():
    cap = []

    def make(color, word):
        cap.append(Relax(ExactlyK(2, (word, 'red')), by=2))
        return cap

    color, word, block = _simple(make)
    assert cap[0].relaxation.applied_k == 3
    assert block._trials_per_sample() == 9


def test_rebuilding_measures_the_budget_from_the_written_value():
    # The repair mutates the constraint, so a second build has to keep
    # measuring from what the user wrote rather than drifting upward.
    color = Factor('color', ['red', 'green', 'blue'])
    word = Factor('word', ['red', 'green', 'blue'])
    cap = Relax(ExactlyK(2, (word, 'red')), by=1)
    for _ in range(2):
        CrossBlock([color, word], [color],
                   [CoverAllCombinations(color, word), cap])
        assert cap.relaxation.original_k == 2
        assert cap.relaxation.applied_k == 3
        assert cap.k == 3
