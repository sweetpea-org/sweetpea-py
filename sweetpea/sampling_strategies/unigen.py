import json
import math
import requests
import tempfile

from datetime import datetime
from typing import List, cast
from ascii_graph import Pyasciigraph

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.docker import update_docker_image, start_docker_container, check_server_health, stop_docker_container

"""
This strategy relies fully on Unigen to produce the desired number of samples.
"""
class UnigenSamplingStrategy(SamplingStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:

        print("Warning: Unigen is currently not working.")
        # TODO: Do this in separate thread, and output some kind of progress indicator.
        backend_request = block.build_backend_request()

        # Taken from the unigen2.py script: https://bitbucket.org/kuldeepmeel/unigen/src/4677b2ec4553b2a44a31910db0037820abdc1394/UniGen2.py?at=master&fileviewer=file-view-default
        kappa = 0.638
        pivot_unigen = math.ceil(4.03 * (1 + 1 / kappa) * (1 + 1 / kappa))
        solution_count = math.factorial(block.trials_per_sample())
        log_count = math.log(solution_count, 2)
        start_iteration = int(round(log_count + math.log(1.8, 2) - math.log(pivot_unigen, 2))) - 2

        json_data = {
            'sampleCount': sample_count,
            'support': block.variables_per_sample(),
            'fresh': backend_request.fresh - 1,
            'cnfs': backend_request.get_cnfs_as_json(),
            'requests': backend_request.get_requests_as_json(),
            'unigenOptions': [
                "--verbosity=0",
                "--samples=" + str(sample_count),
                "--kappa=" + str(kappa),
                "--pivotUniGen=" + str(pivot_unigen),
                "--startIteration=" + str(start_iteration),
                "--maxLoopTime=3000",
                "--maxTotalTime=72000",
                "--tApproxMC=1",
                "--pivotAC=60",
                "--gaussuntil=400"
            ]
        }

        solutions = cast(List[dict], [])

        # Make sure the local image is up-to-date.
        update_docker_image("sweetpea/server")

        # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
        container = start_docker_container("sweetpea/server", 8080)

        # 2. POST to /experiments/generate using the backend request json as the body.
        # TOOD: Do this in separate thread, and output some kind of progress indicator.
        print("Sending formula to backend... ", end='', flush=True)
        t_start = datetime.now()
        try:
            check_server_health()

            experiments_request = requests.post('http://localhost:8080/experiments/generate', data = json.dumps(json_data))
            if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
                tmp_filename = ""
                with tempfile.NamedTemporaryFile(delete=False, mode="w+") as f:
                    json.dump(json_data, f)
                    tmp_filename = f.name

                raise RuntimeError("Received non-200 response from experiment generation! LowLevelRequest body saved to temp file '" +
                    tmp_filename + "' status_code=" + str(experiments_request.status_code) + " response_body=" + str(experiments_request.text))

            solutions = experiments_request.json()['solutions']
            t_end = datetime.now()
            print(str((t_end - t_start).seconds) + "s")

        # 3. Stop and then remove the docker container.
        finally:
            stop_docker_container(container)

        # 4. Decode the results
        result = list(map(lambda s: SamplingStrategy.decode(block, s['assignment']), solutions))

        # Dump histogram of frequency distribution, just to make sure it's somewhat even.
        print()
        print("Found " + str(len(solutions)) + " distinct solutions.")
        print()
        hist_data = [("Solution #" + str(idx + 1), sol['frequency']) for idx, sol in enumerate(solutions)]
        hist_data.sort(key=lambda tup: tup[1], reverse=True)

        graph = Pyasciigraph()
        for line in  graph.graph('Most Frequently Sampled Solutions', hist_data[:15]):
            print(line)

        return SamplingResult(result, {})
