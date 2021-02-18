#!/usr/bin/env python3


"""A small script to test whether calls to Unigen work.

NOTE: These calls may be nonsensical --- I just put something together.
"""


from sweetpea.core import (
    AssertionType, CNF, GenerationRequest, Var,
    cnf_is_satisfiable, sample_uniform, sample_non_uniform)

cnf = CNF()
a, b = cnf.get_n_fresh(2)
_, _ = cnf.half_adder(a, b)

print("Calling sample_uniform...")
sample_uniform(cnf, 2, 0, [GenerationRequest(AssertionType.EQ, 3, [Var(1)])])
print("Success.")

print("")
print("Calling sample_non_uniform...")
sample_non_uniform(2, cnf, 2, 3, [GenerationRequest(AssertionType.EQ, 2, [Var(-2)])])
print("Success.")

print("")
print("Calling cnf_is_satisfiable...")
cnf_is_satisfiable(cnf)
print("Success.")
