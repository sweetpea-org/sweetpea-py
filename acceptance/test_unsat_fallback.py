import pytest

from sweetpea import *
from sweetpea._internal.constraint import CoverAllCombinations, relax_budget
from sweetpea._internal.core import SolveOutcome
from importlib import import_module

# The generate package rebinds this name to the function it re-exports,
# so the module itself has to be fetched by path.
sample_module = import_module('sweetpea._internal.core.generate.sample_non_uniform')
from sweetpea._internal.main import _weaken_until_satisfiable
from sweetpea._internal.sampling_strategy.base import SamplingResult


def _stroop():
    colors = ['red', 'green', 'blue']
    color = Factor('color', colors)
    word = Factor('word', colors)
    congruency = Factor('congruency', [
        DerivedLevel('con', WithinTrial(lambda c, w: c == w, [color, word])),
        DerivedLevel('incon', WithinTrial(lambda c, w: c != w, [color, word])),
    ])
    return color, word, congruency


def _covered(constraints):
    """Stroop with coverage, where AtLeastKInARow(7) has no solution: coverage
    fixes the block at 12 trials holding four word-reds, which cannot form a run
    of seven."""
    color, word, congruency = _stroop()
    made = constraints(color, word)
    block = CrossBlock([congruency, color, word], [congruency, color],
                       [CoverAllCombinations(color, word)] + made)
    return block, made


def _crowded(constraints):
    """Four trials of which three are red. No arrangement keeps the reds apart
    at k=1, since 3 > 1 * (4 - 3 + 1); k=2 admits one."""
    color = Factor('color', [Level('red', 3), 'green'])
    made = constraints(color)
    return CrossBlock([color], [color], made), made


# ~~~~~~~~~~~~ Outcome plumbing ~~~~~~~~~~~~

def test_no_solution_on_first_solve_is_unsatisfiable(monkeypatch, tmp_path):
    monkeypatch.setattr(sample_module, 'cryptominisat_solve', lambda f, d=False: [])
    (solutions, outcome) = sample_module.compute_solutions(tmp_path / 'p.cnf', 3, 2)
    assert solutions == []
    assert outcome is SolveOutcome.UNSATISFIABLE


def test_no_solution_after_one_is_satisfied(monkeypatch, tmp_path):
    answers = [[1, 2, 3], []]
    monkeypatch.setattr(sample_module, 'cryptominisat_solve',
                        lambda f, d=False: answers.pop(0))
    monkeypatch.setattr(sample_module, 'update_file', lambda f, s: None)
    (solutions, outcome) = sample_module.compute_solutions(tmp_path / 'p.cnf', 3, 5)
    assert len(solutions) == 1
    assert outcome is SolveOutcome.SATISFIED


def test_solver_failure_is_unknown(monkeypatch, tmp_path):
    monkeypatch.setattr(sample_module, 'cryptominisat_solve', lambda f, d=False: None)
    (solutions, outcome) = sample_module.compute_solutions(tmp_path / 'p.cnf', 3, 2)
    assert solutions == []
    assert outcome is SolveOutcome.UNKNOWN


# ~~~~~~~~~~~~ Weakening after UNSAT ~~~~~~~~~~~~

def test_at_least_k_in_a_row_weakens_downward():
    block, (cap,) = _covered(
        lambda c, w: [Relax(AtLeastKInARow(7, (w, 'red')), by=6)])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert experiments
    assert cap.relaxation.original_k == 7
    assert cap.relaxation.applied_k == cap.k < 7


def test_at_most_k_in_a_row_weakens_upward():
    block, (cap,) = _crowded(
        lambda c: [Relax(AtMostKInARow(1, (c, 'red')), by=1)])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert experiments
    assert cap.relaxation.original_k == 1
    assert cap.relaxation.applied_k == 2
    assert block.applied_relaxations


@pytest.mark.parametrize('build,make', [
    (_covered, lambda c, w: [AtLeastKInARow(7, (w, 'red'))]),
    (_crowded, lambda c: [AtMostKInARow(1, (c, 'red'))]),
])
def test_unwrapped_constraint_is_not_weakened(build, make):
    block, _ = build(make)
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen) == []


def test_budget_too_small_applies_nothing(capsys):
    # Steps taken during the search are kept, so that a later concession starts
    # from them, but nothing counts as applied without a design to show for it.
    block, (cap,) = _covered(
        lambda c, w: [Relax(AtLeastKInARow(7, (w, 'red')), by=1)])
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen) == []
    assert cap.k == 6
    assert block.applied_relaxations == []
    assert 'was not enough' in capsys.readouterr().out


def test_unknown_outcome_does_not_weaken():
    # A solver failure says nothing about the design, so nothing is altered and
    # no re-solve is attempted.
    block, (cap,) = _crowded(lambda c: [Relax(AtMostKInARow(1, (c, 'red')), by=2)])
    result = SamplingResult([], {}, SolveOutcome.UNKNOWN)

    def run():
        raise AssertionError('must not re-solve on an unknown outcome')

    assert _weaken_until_satisfiable(block, result, run) is result
    assert cap.k == 1
    assert cap.relaxation.applied_k is None


def test_at_least_k_of_one_has_no_room_to_weaken():
    color = Factor('color', ['red', 'green'])
    assert relax_budget(Relax(AtLeastKInARow(1, (color, 'red')), by=3)) == 0


# ~~~~~~~~~~~~ One relaxable constraint per experiment ~~~~~~~~~~~~

def test_two_relaxed_constraints_are_rejected():
    color, word, congruency = _stroop()
    with pytest.raises(ValueError) as info:
        CrossBlock([congruency, color, word], [congruency, color],
                   [Relax(AtMostKInARow(2, (word, 'red')), by=1),
                    Relax(AtLeastKInARow(2, (color, 'red')), by=1)])
    assert 'one constraint' in str(info.value)


def test_relax_accepts_the_in_a_row_pair():
    color, word, _ = _stroop()
    for constraint in (AtMostKInARow(2, (word, 'red')),
                       AtLeastKInARow(2, (word, 'red')),
                       ExactlyK(2, (word, 'red'))):
        assert Relax(constraint, by=1).relaxation.by == 1


def test_relax_still_rejects_other_constraints():
    color, _, _ = _stroop()
    with pytest.raises(ValueError) as info:
        Relax(MinimumTrials(10), by=1)
    assert 'AtMostKInARow' in str(info.value)


# ~~~~~~~~~~~~ Reporting ~~~~~~~~~~~~

def test_weakening_is_reported_with_the_results(capsys):
    block, _ = _crowded(lambda c: [Relax(AtMostKInARow(1, (c, 'red')), by=1)])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    capsys.readouterr()
    print_experiments(block, experiments)
    assert 'relaxed from 1 to 2' in capsys.readouterr().out


# ~~~~~~~~~~~~ Giving up optional coverage factors ~~~~~~~~~~~~

def _weighted(constraints, optional):
    """`color` is 3:1 weighted and crossed, so red is three quarters of every
    pass. Full coverage of word x cue is 12 combinations, so 3 passes of 4 = 12
    trials holding 9 reds, which AtMostKInARow(2) cannot arrange since
    9 > 2 * (12 - 9 + 1). Giving cue up leaves 4 combinations, one pass, 3 reds,
    which it can."""
    color = Factor('color', [Level('red', 3), 'green'])
    word = Factor('word', ['w1', 'w2', 'w3', 'w4'])
    cue = Factor('cue', ['c1', 'c2', 'c3'])
    made = constraints(color)
    block = CrossBlock([color, word, cue], [color],
                       [CoverAllCombinations(word, optional=optional(word, cue))]
                       + made)
    return color, word, cue, block, made


def test_optional_factor_is_given_up_and_the_block_shrinks():
    color, word, cue, block, _ = _weighted(
        lambda c: [AtMostKInARow(2, (c, 'red'))], lambda w, q: [q])
    assert block._trials_per_sample() == 12
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert experiments
    assert block._trials_per_sample() == 4
    assert set(experiments[0]['word']) == {'w1', 'w2', 'w3', 'w4'}


def test_giving_up_is_reported_with_the_results(capsys):
    _, _, _, block, _ = _weighted(
        lambda c: [AtMostKInARow(2, (c, 'red'))], lambda w, q: [q])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert any('gave up cue' in m for m in block.applied_relaxations)
    capsys.readouterr()
    print_experiments(block, experiments)
    assert 'gave up cue' in capsys.readouterr().out


def test_last_optional_factor_is_given_up_first():
    colr = Factor('colr', ['red', 'green'])
    size = Factor('size', ['big', 'small'])
    cue = Factor('cue', ['c1', 'c2'])
    coverage = CoverAllCombinations(colr, optional=[size, cue])
    assert coverage.drop_one() is cue
    assert coverage.drop_one() is size
    assert not coverage.can_drop()


def test_relax_and_giving_up_apply_in_order():
    # AtMostKInARow(1) needs k >= 3 at twelve trials, so one Relax step is not
    # enough on its own; giving cue up as well brings the block within reach.
    cap = []

    def make(color):
        cap.append(Relax(AtMostKInARow(1, (color, 'red')), by=1))
        return cap

    _, _, _, block, _ = _weighted(make, lambda w, q: [q])
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert experiments
    assert cap[0].relaxation.applied_k == 2
    assert block._trials_per_sample() == 4
    reported = ' '.join(block.applied_relaxations)
    assert 'AtMostKInARow' in reported
    assert 'gave up cue' in reported


def test_nothing_left_to_give_up_returns_no_sequences():
    # AtLeastKInARow(5) cannot be met at either size, and there is only one
    # factor to give up.
    colors = ['red', 'green', 'blue']
    color = Factor('color', colors)
    word = Factor('word', colors)
    congruency = Factor('congruency', [
        DerivedLevel('con', WithinTrial(lambda c, w: c == w, [color, word])),
        DerivedLevel('incon', WithinTrial(lambda c, w: c != w, [color, word])),
    ])
    block = CrossBlock([congruency, color, word], [congruency, color],
                       [CoverAllCombinations(color, optional=[word]),
                        AtLeastKInARow(5, (word, 'red'))])
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen) == []
