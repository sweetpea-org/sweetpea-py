import operator as op
import pytest

from sweetpea import *
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

correct_response = Factor(name="correct_response", initial_levels=["H", "S"])
congruency = Factor(name="congruency", initial_levels=["congruent", "incongruent"])
design     = [correct_response, congruency]
crossing   = [correct_response, congruency]

@pytest.mark.parametrize('strategy', [IterateSATGen, RandomGen])
@pytest.mark.parametrize('trial_count', [4, 5, 6, 7, 8])
def test_stays_balanced(strategy, trial_count):
    crossing_size = 1
    for f in crossing:
        crossing_size *= len(f.levels)
    block  = Repeat(CrossBlock(design=design, crossing=crossing, constraints=[]),
                    constraints=[MinimumTrials(trials=trial_count)])
    experiments = synthesize_trials(block=block, samples=3, sampling_strategy = strategy)

    for exp in experiments:
        conds = list(zip(*exp.values()))
        for cond in conds:
            assert len(conds) == trial_count

        to_go = trial_count
        while to_go > 0:
            tabulation: Dict[List[str], bool] = dict()
            for cond in conds[:crossing_size]:
                assert not (cond in tabulation)
                tabulation[cond] = True
            to_go -= crossing_size
            cond = cond[crossing_size:]

@pytest.mark.parametrize('strategy', [IterateSATGen, RandomGen])
@pytest.mark.parametrize('trial_count', [4, 5, 6])
def test_leftovers_balanced_across_all_possible_solutions(strategy, trial_count):
    block  = Repeat(CrossBlock(design=design, crossing=crossing, constraints=[]),
                    constraints = [MinimumTrials(trials=trial_count)])
    experiments = synthesize_trials(block=block, samples=500, sampling_strategy = strategy)

    leftover = trial_count % 4

    def factorial(n):
        if n < 2:
            return 1
        else:
            return n * factorial(n - 1)

    assert len(experiments) == 24 * (24 // factorial(4 - leftover))

    # Make sure the solutions are actually distinct
    tabulation: Dict[List[str], bool] = dict()
    for e in experiments:
        key = tuple([(k, tuple(e[k])) for k in e])
        assert not key in tabulation
        tabulation[key] = True
