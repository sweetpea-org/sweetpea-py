"""The behind-the-scenes stuff that powers SweetPea."""

from .cnf import Clause, CNF, Var
from .generate import (
    AssertionType, GenerationRequest, Solution,
    cnf_is_satisfiable, generate_non_uniform, generate_simple
)
