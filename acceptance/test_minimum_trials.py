import operator as op
import pytest

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea import fully_cross_block, NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy, synthesize_trials, minimum_trials
from sweetpea.tests.test_utils import get_level_from_name
from acceptance import shuffled_design_sample, path_to_cnf_files, reset_expected_solutions

correct_response = Factor(name="correct_response", initial_levels=["H", "S"])
congruency = Factor(name="congruency", initial_levels=["congruent", "incongruent"])
design     = [correct_response, congruency]
crossing   = [correct_response, congruency]

@pytest.mark.parametrize('strategy', [NonUniformSamplingStrategy, UniformCombinatoricSamplingStrategy])
def test_stays_balanced(strategy):
    block  = fully_cross_block(design=design, crossing=crossing, constraints=[minimum_trials(trials=7)])
    experiments = synthesize_trials(block=block, samples=3, sampling_strategy = strategy)

    for exp in experiments:
        tabulation: Dict[str, List[str]] = dict()
        conds = zip(*exp.values())
        for cond in conds:
            if cond in tabulation:
                tabulation[cond] = tabulation[cond] + 1
            else:
                tabulation[cond] = 1
        for cond in tabulation:
            assert tabulation[cond] == 1 or tabulation[cond] == 2
