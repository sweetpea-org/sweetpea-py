"""This module provides functionality for interacting with CNF formulas.

SweetPea offers three mechanisms for CNF interaction:

#. Sampling solutions from a CNF formula uniformly via :func:`sample_uniform`.
#. Sampling solutions from a CNF formula *non*-uniformly via
   :func:`sample_non_uniform`.
#. Determining whether a CNF formula is satisfiable via :func:`is_satisfiable`.
"""


from .is_satisfiable import cnf_is_satisfiable
from .sample_non_uniform import sample_non_uniform, sample_non_uniform_from_specification
from .sample_uniform import sample_uniform
from .utility import AssertionType, GenerationRequest, SampleType, ProblemSpecification, Solution, combine_cnf_with_requests
