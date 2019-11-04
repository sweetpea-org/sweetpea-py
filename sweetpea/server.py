import json
import requests
import tempfile
import time
import os
from typing import List

from sweetpea.blocks import Block
from sweetpea.logic import And, cnf_to_json


"""
Contains helper functions for interacting with the server.

All functions expect that the server has already been started.
"""

port = '8080'
if "SWEETPEA_DOCKER_PORT" in os.environ:
    port = os.environ["SWEETPEA_DOCKER_PORT"]
BASE_URL = 'http://localhost:' + port + '/'
SUBMIT_JOB_URL = BASE_URL + 'experiments/jobs'
JOB_STATUS_URL_TEMPLATE = SUBMIT_JOB_URL + '/{}'


"""
Submit an async job to the server for processing. Returns the job id. (String)
"""
def submit_job(request_data: dict) -> str:
    data_str = json.dumps(request_data)
    job_response = requests.post(SUBMIT_JOB_URL, data = data_str)
    if job_response.status_code != 200:
        tmp_filename = ""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(str.encode(data_str))
            tmp_filename = f.name

        raise RuntimeError("Received non-200 response from job submission! Request body saved to temp file '" +
            tmp_filename + "' status_code=" + str(job_response.status_code) + " response_body=" + str(job_response.text))

    return job_response.json()['id']


"""
Gets the current state of a job on the server.
"""
def get_job_status(job_id: str) -> dict:
    job_url = JOB_STATUS_URL_TEMPLATE.format(job_id)
    job_response = requests.get(job_url)
    if job_response.status_code != 200:
        raise RuntimeError("Received non-200 response from job status query! url=" + job_url + " response=" +
            str(job_response.status_code) + " body=" + job_response.text)
    else:
        return job_response.json()


"""
Waits for an async job to finish and returns its result. (String)
"""
def get_job_result(job_id: str) -> str:
    job = get_job_status(job_id)

    delay = 0.1
    while job['status'] == 'InProgress':
        time.sleep(delay)
        delay = min(delay * 2, 30)
        job = get_job_status(job_id)

    return job['result']


"""
Sends a job to the server to build the CNF for a design, returning a dict like so:
{
    'id': '<job id>',
    'cnf_str': '<CNF String>'
}
"""
def build_cnf(block: Block) -> dict:
    backend_request = block.build_backend_request()
    json_data = {
        'action': 'BuildCNF',
        'cnfs': backend_request.get_cnfs_as_json(),
        'requests': backend_request.get_requests_as_json(),
        'support': block.variables_per_sample(),
        'fresh': backend_request.fresh - 1,
    }

    job_id = submit_job(json_data)
    job_result_str = get_job_result(job_id)

    return {
        'id': job_id,
        'cnf_str': job_result_str
    }

# TODO: Make a 'local' version of this for better performance?
# (Invoke solver directly, rather than through docker)
def is_cnf_still_sat(cnf_id: str, additional_clauses: List[And]) -> bool:
    request_data = {
        'action': 'IsSAT',
        'cnfId': cnf_id,
        'cnfs': cnf_to_json(additional_clauses)
    }

    sat_job_id = submit_job(request_data)
    return get_job_result(sat_job_id) == "True"
