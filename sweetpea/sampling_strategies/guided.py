import os
import numpy as np

from functools import reduce
from itertools import product
from time import time
from typing import List, cast

from sweetpea.blocks import Block
from sweetpea.docker import update_docker_image, start_docker_container, stop_docker_container
from sweetpea.logic import And
from sweetpea.sampling_strategies.base_strategy import BaseStrategy
from sweetpea.server import build_cnf, is_cnf_still_sat


"""
This strategy gradually constructs samples in memory, with the aid of a SAT solver to
guide the choices it makes.
"""
class Guided(BaseStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int) -> List[dict]:

        update_docker_image("sweetpea/server")
        container = start_docker_container("sweetpea/server", 8080)

        samples = cast(List[dict], [])
        try:
            # Build the full CNF for this block
            cnf_result = build_cnf(block)
            cnf_id = cnf_result['id']

            for _ in range(sample_count):
                samples.append(Guided.__generate_sample(block, cnf_id))

        finally:
            stop_docker_container(container)

        return samples


    @staticmethod
    def __generate_sample(block: Block, cnf_id: str) -> dict:
        # Start a 'committed' list of CNFs
        committed = cast(List[And], [])

        for trial_number in range(block.trials_per_sample()):

            #  Get the variable list for this trial.
            variables = block.variable_list_for_trial(trial_number + 1)
            variables = list(filter(lambda i: i != [], variables))
            potential_trials = list(map(list, product(*variables)))

            # Use env var to switch between filtering and not
            if Guided.__prefilter_enabled():
                pass
                # TODO:
                # Flatten the list
                # Check SAT for each one
                # Record each var that is auto-unsat
                # Filter out any potential trials with those vars set
                # Record the number filterd out for metrics

            allowed_trials = []
            for potential_trial in potential_trials:
                start_time = time()
                allowed = is_cnf_still_sat(cnf_id, committed + [And(potential_trial)])
                duration_seconds = time() - start_time

                # TODO: Record stats

                if allowed:
                    allowed_trials.append(potential_trial)

            # Randomly sample a single trial from the uniform distribution of the allowed trials,
            # and commit that trial to the committed sequence.
            trial_idx = np.random.randint(0, len(allowed_trials))
            committed.append(And(allowed_trials[trial_idx]))

        # Flatten the committed trials into a list of integers and decode it.
        solution = Guided.__committed_to_solution(committed)
        return BaseStrategy.decode(block, solution)

    @staticmethod
    def __committed_to_solution(committed: List[And]) -> List[int]:
        return reduce(lambda sol, clause: sol + clause.input_list, committed, [])

    @staticmethod
    def __prefilter_enabled():
        return os.environ.get('SWEETPEA_GUIDED_PREFILTER_TRIALS') is not None
