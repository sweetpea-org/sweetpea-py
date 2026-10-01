
import operator as op
import pytest

from sweetpea import *
from sweetpea._internal.constraint import LatinSquare

@pytest.mark.parametrize('strategy', [RandomGen, IterateSATGen])
# Counts cover every rotation of the pattern, since where the cycle starts is
# the solver's choice: two levels outside the main factor, so twice the
# sequences a fixed start would allow.
@pytest.mark.parametrize('config', [(1, 32),
                                    (8, 1152),
                                    (5, 384)])
def test_latin_square_uncrossed(strategy, config):
    (min_trials, expected_count) = config
    
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2"])
    
    outer = CrossBlock([A, B, C], [A, C], [LatinSquare([A, B]), MinimumTrials(min_trials)])
    
    exps = synthesize_trials(outer, 2000, sampling_strategy=IterateGen)
    assert len(exps) == expected_count

def test_latin_square_merge():
    A = Factor("A", ["a1", "a2"])
    B = Factor("B", ["b1", "b2"])
    C = Factor("C", ["c1", "c2"])

    orig = CrossBlock([A, C], [A, C], [])
    more = MultiCrossBlock([B], [], [])

    outer = Merge([orig, more], [LatinSquare([A, B]), MinimumTrials(8)],
                  mode = RepeatMode.WEIGHT)

    exps = synthesize_trials(outer, 2000, sampling_strategy=IterateGen)
    assert len(exps) == 1152


# ~~~~~~~~~~~~ Where the pattern starts is the solver's choice ~~~~~~~~~~~~

def _pinned(color_levels):
    """Participant 0's first trial must be big-red. Only one of the two
    rotations puts that pair together, and which one it is depends on the order
    the colors are declared."""
    font = Factor("Font", ["small", "big"])
    color = Factor("Color", color_levels)
    b = CrossBlock(design=[font, color], crossing=[font, color], constraints=[])
    return Merge(blocks=[b], constraints=[LatinSquare([font, color], name="Participant"),
                                          Pin(0, (font, "big")), Pin(0, (color, "red"))])


@pytest.mark.parametrize('color_levels', [["red", "green"], ["green", "red"]])
def test_declaration_order_does_not_decide_satisfiability(color_levels):
    block = _pinned(color_levels)
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen)


# ~~~~~~~~~~~~ Leaving participants out of the pattern ~~~~~~~~~~~~

def _crowded(wrap, min_trials, run=3):
    """Every participant held to the pattern gets exactly one `big`, so no run
    of `big` can span a whole participant. AtLeastKInARow wants a longer one."""
    font = Factor("Font", ["small", "big"])
    color = Factor("Color", ["red", "green"])
    b = CrossBlock(design=[font, color], crossing=[], constraints=[MinimumTrials(min_trials)])
    square = LatinSquare([font, color], name="Participant")
    return Merge(blocks=[b], constraints=[wrap(square),
                                          AtLeastKInARow(run, (font, "big"))])


def _square_of(block):
    return next(c for c in block.constraints if isinstance(c, LatinSquare))


def test_square_held_in_full_has_no_solution():
    block = _crowded(lambda s: s, 4)
    assert synthesize_trials(block, 1, sampling_strategy=IterateGen) == []


def test_releasing_a_participant_finds_a_solution():
    block = _crowded(lambda s: Relax(s, by=1), 4)
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    assert experiments
    assert any('Latin square' in m for m in block.applied_relaxations)


def test_solver_chooses_which_participant_to_release():
    # Three participants: only the middle one, released, lets the first end on
    # big and the last start on big, joining a single run. Releasing by position
    # would have needed two.
    block = _crowded(lambda s: Relax(s, by=1), 6)
    experiments = synthesize_trials(block, 20, sampling_strategy=IterateGen)
    assert experiments
    for e in experiments:
        assert _square_of(block).released_participants(e, block) == [1]


def test_release_budget_can_run_out():
    # A run of 5 across three participants needs two of them released.
    assert synthesize_trials(_crowded(lambda s: Relax(s, by=1), 6, run=5), 1,
                             sampling_strategy=IterateGen) == []
    assert synthesize_trials(_crowded(lambda s: Relax(s, by=2), 6, run=5), 1,
                             sampling_strategy=IterateGen)


def test_released_participant_is_named_with_the_results(capsys):
    block = _crowded(lambda s: Relax(s, by=1), 6)
    experiments = synthesize_trials(block, 1, sampling_strategy=IterateGen)
    capsys.readouterr()
    print_experiments(block, experiments)
    assert 'Released from the Latin square: participant 1' in capsys.readouterr().out


def test_relax_accepts_a_latin_square():
    font = Factor("Font", ["small", "big"])
    color = Factor("Color", ["red", "green"])
    assert Relax(LatinSquare([font, color]), by=2).relaxation.by == 2


def test_only_one_constraint_may_be_relaxed():
    font = Factor("Font", ["small", "big"])
    color = Factor("Color", ["red", "green"])
    b = CrossBlock(design=[font, color], crossing=[font, color], constraints=[])
    with pytest.raises(ValueError, match='one constraint'):
        Merge(blocks=[b], constraints=[Relax(LatinSquare([font, color]), by=1),
                                       Relax(ExactlyK(2, (font, "big")), by=1)])


def test_participants_are_numbered_through_the_experiment(capsys):
    # Four participants here, since the number of them is the product of the
    # non-main factors' level counts rather than the diagonal length.
    font = Factor("Font", ["small", "big"])
    color = Factor("Color", ["red", "green"])
    size = Factor("Size", ["s1", "s2"])
    b = CrossBlock(design=[font, color, size], crossing=[font, color, size], constraints=[])
    lsb = Merge(blocks=[b], constraints=[LatinSquare([font, color, size], name="Participant")])
    print_experiments(lsb, synthesize_trials(lsb, 1, sampling_strategy=IterateGen))
    out = capsys.readouterr().out
    for n in range(4):
        assert 'Participant {}:'.format(n) in out
