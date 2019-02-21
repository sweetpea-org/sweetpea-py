import json
import requests
import tempfile
import time

from datetime import datetime
from typing import List, cast

from sweetpea.sampling_strategies.base_strategy import BaseStrategy
from sweetpea.blocks import Block
from sweetpea.docker import update_docker_image, start_docker_container, check_server_health, stop_docker_container

"""
This represents the non-uniform sampling strategy, in which we 'sample' just by using a SAT
solver repeatedly to produce unique (but not uniform) samples.
"""
class NonUniform(BaseStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int) -> List[dict]:
        backend_request = block.build_backend_request()
        json_data = {
            'action': 'SampleNonUniform',
            'sampleCount': sample_count,
            'support': block.variables_per_sample(),
            'fresh': backend_request.fresh,
            'cnfs': backend_request.get_cnfs_as_json(),
            'requests': backend_request.get_requests_as_json()
        }

        solutions = cast(List[dict], [])

        # Make sure the local image is up-to-date.
        update_docker_image("sweetpea/server")

        # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
        container = start_docker_container("sweetpea/server", 8080)

        print("Sending formula to backend... ", end='', flush=True)
        t_start = datetime.now()

        job = None
        try:
            check_server_health()

            url = 'http://localhost:8080/experiments/jobs'
            job_response = requests.post(url, data = json.dumps(json_data))
            if job_response.status_code != 200:
                tmp_filename = ""
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    json.dump(json.dumps(json_data), f)
                    tmp_filename = f.name

                raise RuntimeError("Received non-200 response from non-uniform experiment generation job submission! Request body saved to temp file '" +
                    tmp_filename + "' status_code=" + str(job_response.status_code) + " response_body=" + str(job_response.text))

            job = job_response.json()
            delay = 0.2
            while job['status'] == 'InProgress':
                print('.', end='', flush=True)
                time.sleep(delay)
                delay = min(delay * 2, 30)
                url = 'http://localhost:8080/experiments/jobs/' + job['id']
                job_response = requests.get(url)
                if job_response.status_code != 200:
                    raise RuntimeError("Received non-200 response from non-uniform job status query! url=" + url + " response=" + str(job_response.status_code) + " body=" + job_response.text)
                else:
                    job = job_response.json()

            solutions = json.loads(job['result'])['solutions']
            t_end = datetime.now()
            print(str((t_end - t_start).seconds) + "s")

        # 3. Stop and then remove the docker container.
        finally:
            stop_docker_container(container)

        # 4. Decode the results
        result = list(map(lambda s: BaseStrategy.decode(block, s['assignment']), solutions))

        return result

