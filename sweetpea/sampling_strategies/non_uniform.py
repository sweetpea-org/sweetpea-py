import json
import requests
import tempfile
import time

from datetime import datetime
from typing import List, cast

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.docker import update_docker_image, start_docker_container, check_server_health, stop_docker_container
from sweetpea.server import submit_job, get_job_result

"""
This represents the non-uniform sampling strategy, in which we 'sample' just by using a SAT
solver repeatedly to produce unique (but not uniform) samples.
"""
class NonUniformSamplingStrategy(SamplingStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        backend_request = block.build_backend_request()
        if block.errors:
            for e in block.errors:
                print(e)
                if "WARNING" not in e:
                    return SamplingResult([], {})
        json_data = {
            'action': 'SampleNonUniform',
            'sampleCount': sample_count,
            'support': block.variables_per_sample(),
            'fresh': backend_request.fresh - 1,
            'cnfs': backend_request.get_cnfs_as_json(),
            'requests': backend_request.get_requests_as_json()
        }

        solutions = cast(List[dict], [])

        update_docker_image("sweetpea/server")
        container = start_docker_container("sweetpea/server", 8080)

        print("Sending formula to backend... ", end='', flush=True)
        t_start = datetime.now()

        try:
            job_id = submit_job(json_data)
            job_result_str = get_job_result(job_id)

            solutions = json.loads(job_result_str)['solutions']
            t_end = datetime.now()
            print(str((t_end - t_start).seconds) + "s")

        finally:
            stop_docker_container(container)

        result = list(map(lambda s: SamplingStrategy.decode(block, s['assignment']), solutions))
        return SamplingResult(result, {})
