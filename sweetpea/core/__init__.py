"""The behind-the-scenes stuff that powers SweetPea."""

from .cnf import Clause, CNF, Var
from .generate import (
    AssertionType, GenerationRequest, Solution,
    cnf_is_satisfiable, sample_non_uniform, sample_non_uniform_from_specification, sample_uniform,
    combine_cnf_with_requests
)
