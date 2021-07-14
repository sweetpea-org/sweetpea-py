import json
import math
from sweetpea.constraints import minimum_trials
from sweetpea.core.generate.utility import ProblemSpecification, Solution
import requests
import tempfile
from tqdm import tqdm
import sys

from datetime import datetime
from typing import List, cast
from ascii_graph import Pyasciigraph

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.core import sample_uniform, CNF

"""
This strategy relies fully on Unigen to produce the desired number of samples.
"""
class UnigenSamplingStrategy(SamplingStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False) -> SamplingResult:

        backend_request = block.build_backend_request()
        if block.errors:
            for e in block.errors:
                print(e)
                if "WARNING" not in e:
                    return SamplingResult([], {})

        solutions = sample_uniform(
            sample_count,
            CNF(backend_request.get_cnfs_as_json()),
            backend_request.fresh - 1,
            block.variables_per_sample(),
            backend_request.get_requests_as_generation_requests(),
            False)

        if not solutions:
            from sweetpea.constraints import AtLeastKInARow
            if min_search:
                return SamplingResult([], {})
            else:
                max_constraints = list(map(lambda x: cast(AtLeastKInARow, x).max_trials_required, filter(lambda c: isinstance(c, AtLeastKInARow), block.constraints)))

                if max_constraints:
                    print("No solution found... We require a minimum trials contraint to find a solution.")
                    max_constraint = max(max_constraints)
                    min_constraint = block.trials_per_sample()+1
                    original_min_trials = block.min_trials
                    last_valid_min_contraint = max_constraint
                    last_valid = SamplingResult([], {})
                    progress = tqdm(total=math.ceil(math.log(max_constraint-min_constraint))+1, file=sys.stdout)
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

        # kappa = 0.638
        # pivot_unigen = math.ceil(4.03 * (1 + 1 / kappa) * (1 + 1 / kappa))
        # solution_count = math.factorial(block.trials_per_sample())
        # log_count = math.log(solution_count, 2)
        # start_iteration = int(round(log_count + math.log(1.8, 2) - math.log(pivot_unigen, 2))) - 2

        # json_data = {
        #     'sampleCount': sample_count,
        #     'support': block.variables_per_sample(),
        #     'fresh': backend_request.fresh - 1,
        #     'cnfs': backend_request.get_cnfs_as_json(),
        #     'requests': backend_request.get_requests_as_json(),
        #     'unigenOptions': [
        #         "--verbosity=0",
        #         "--samples=" + str(sample_count),
        #         "--kappa=" + str(kappa),
        #         "--pivotUniGen=" + str(pivot_unigen),
        #         "--startIteration=" + str(start_iteration),
        #         "--maxLoopTime=3000",
        #         "--maxTotalTime=72000",
        #         "--tApproxMC=1",
        #         "--pivotAC=60",
        #         "--gaussuntil=400"
        #     ]
        # }

        # solutions = cast(List[dict], [])

        # # Make sure the local image is up-to-date.
        # update_docker_image("sweetpea/server")

        # # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
        # container = start_docker_container("sweetpea/server", 8080)

        # # 2. POST to /experiments/generate using the backend request json as the body.
        # # TOOD: Do this in separate thread, and output some kind of progress indicator.
        # print("Sending formula to backend... ", end='', flush=True)
        # t_start = datetime.now()
        # try:
        #     check_server_health()

        #     experiments_request = requests.post('http://localhost:8080/experiments/generate', data = json.dumps(json_data))
        #     if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
        #         tmp_filename = ""
        #         with tempfile.NamedTemporaryFile(delete=False, mode="w+") as f:
        #             json.dump(json_data, f)
        #             tmp_filename = f.name

        #         raise RuntimeError("Received non-200 response from experiment generation! LowLevelRequest body saved to temp file '" +
        #             tmp_filename + "' status_code=" + str(experiments_request.status_code) + " response_body=" + str(experiments_request.text))

        #     solutions = experiments_request.json()['solutions']
        #     t_end = datetime.now()
        #     print(str((t_end - t_start).seconds) + "s")

        # # 3. Stop and then remove the docker container.
        # finally:
        #     stop_docker_container(container)

        # # 4. Decode the results
        # result = list(map(lambda s: SamplingStrategy.decode(block, s['assignment']), solutions))

        # # Dump histogram of frequency distribution, just to make sure it's somewhat even.
        # print()
        # print("Found " + str(len(solutions)) + " distinct solutions.")
        # print()
        # hist_data = [("Solution #" + str(idx + 1), sol['frequency']) for idx, sol in enumerate(solutions)]
        # hist_data.sort(key=lambda tup: tup[1], reverse=True)

        # graph = Pyasciigraph()
        # for line in  graph.graph('Most Frequently Sampled Solutions', hist_data[:15]):
        #     print(line)

        # return SamplingResult(result, {})
