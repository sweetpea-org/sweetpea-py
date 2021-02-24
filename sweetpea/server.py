from sweetpea.blocks import Block
from sweetpea.core import CNF


def build_cnf(block: Block) -> CNF:
    """Converts a Block into a CNF represented as a Unigen-compatible string.
    """
    backend_request = block.build_backend_request()
    cnf = CNF(backend_request.get_cnfs_as_json())
    return cnf


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
