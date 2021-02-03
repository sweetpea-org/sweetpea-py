import json
import requests
import tempfile
import time
import os
from typing import List

from sweetpea.blocks import Block
from sweetpea.logic import And, cnf_to_json
from sweetpea.core import build_CNF

"""
Contains helper functions for interacting with the backend.

"""

"""
Sends a job to the backend to build the CNF for a design, returning a dict like so:
{
    'id': '<job id>',
    'cnf_str': '<CNF String>'
}
"""
def build_cnf(block: Block) -> dict:

    backend_request = block.build_backend_request()
    job_result_str = build_CNF(backend_request.get_cnfs_as_json(),
        backend_request.fresh - 1,
        block.variables_per_sample(),
        backend_request.get_requests_as_generation_requests())

    return job_result_str        

# TODO: Make a 'local' version of this for better performance?
# (Invoke solver directly, rather than through docker)
# Make sure there is working local function 
# def is_cnf_still_sat(cnf_id: str, additional_clauses: List[And]) -> bool:
#     request_data = {
#         'action': 'IsSAT',
#         'cnfId': cnf_id,
#         'cnfs': cnf_to_json(additional_clauses)
#     }

#     sat_job_id = submit_job(request_data)
#     return get_job_result(sat_job_id) == "True"
