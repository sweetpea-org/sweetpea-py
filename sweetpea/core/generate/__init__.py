"""This module provides functionality for generating CNF formulas.

Something something test text.
"""


from .is_satisfiable import cnf_is_satisfiable
from .sample_non_uniform import sample_non_uniform, sample_non_uniform_from_specification
from .sample_uniform import sample_uniform
from .utility import AssertionType, GenerationRequest, SampleType, ProblemSpecification, Solution, combine_cnf_with_requests
