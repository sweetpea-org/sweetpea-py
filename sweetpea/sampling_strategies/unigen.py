from math import ceil, log
from tqdm import tqdm
import sys

from typing import List, cast

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.core import sample_uniform, CNF
from sweetpea.constraints import minimum_trials

"""
This strategy relies fully on Unigen to produce the desired number of samples.
"""
class UniGen(SamplingStrategy):

    @staticmethod
    def class_name():
        return 'UniGen'

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False, use_cmsgen=False) -> SamplingResult:

        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_uniform(
            sample_count,
            CNF(backend_request.get_cnfs_as_json()),
            backend_request.fresh - 1,
            block.variables_per_sample(),
            backend_request.get_requests_as_generation_requests(),
            use_docker=False,
            use_cmsgen=use_cmsgen)

        # This section deals with the problem caused by a corner case created
        # by at_least_k_in_a_row_constraint. I.e. in some cases this cotnraint
        # requires the support of a minimum_trials contraint to find valid
        # solutions. This will find the optimal minimum trials constraint to
        # the user using binary search with trial and error.
        if not solutions:
            from sweetpea.constraints import AtLeastKInARow
            if min_search:
                return SamplingResult([], {})
            else:
                atleast_constraints = cast(List[AtLeastKInARow], filter(lambda c: isinstance(c, AtLeastKInARow),
                                                                        block.constraints))
                max_constraints = list(map(lambda x: x.max_trials_required, atleast_constraints))

                if max_constraints:
                    print("No solution found... We require a minimum trials contraint to find a solution.")
                    max_constraint = max(max_constraints)
                    min_constraint = block.trials_per_sample()+1
                    original_min_trials = block.min_trials
                    last_valid_min_contraint = max_constraint
                    last_valid = SamplingResult([], {})
                    progress = tqdm(total=ceil(log(max_constraint-min_constraint))+1, file=sys.stdout)
                    while True:
                        current_constraint = int((max_constraint-min_constraint+1)/2)+min_constraint
                        block.min_trials = original_min_trials
                        c = minimum_trials(current_constraint)
                        c.validate(block)
                        c.apply(block, None)
                        block.constraints.append(c)
                        res = UnigenSamplingStrategy.sample(block, sample_count, True)
                        progress.update(1)
                        if res.samples:
                            if current_constraint <= min_constraint:
                                print("Optimal minimum trials contraint is at ", current_constraint, ".")
                                return res
                            else:
                                last_valid_min_contraint = current_constraint
                                last_valid = res
                                max_constraint = current_constraint-1
                        else:
                            if max_constraint <= current_constraint:
                                print("Optimal minimum trials contraint is at ", last_valid_min_contraint, ".")
                                return last_valid
                            else:
                                min_constraint = current_constraint + 1
                    progress.close()
                    return result
                else:
                    return SamplingResult([], {})

        result = list(map(lambda s: SamplingStrategy.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})

UnigenSamplingStrategy = UniGen
