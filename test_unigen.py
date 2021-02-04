#!/usr/bin/env python3


"""A small script to test whether calls to Unigen work.

NOTE: These calls may be nonsensical --- I just put something together.

NOTE: I think cryptominisat may return a nonzero exit code on success. In the
      Haskell code, there was a note that unigen behaved this way, but there
      was no similar note about cryptominisat so I'm not 100% sure what's going
      on there. However, the call itself does appear to go through, so that's
      something?
TODO: I will investigate this.
"""


from sweetpea.core import (
    AssertionType, CNF, GenerationRequest, Var,
    generate_simple, generate_non_uniform)

cnf = CNF()
a, b = cnf.get_n_fresh(2)
_, _ = cnf.half_adder(a, b)

print("Calling generate_simple...")
generate_simple(cnf, 2, 0, [GenerationRequest(AssertionType.EQ, 3, [Var(1)])])
print("Success.")

print("")
print("Calling generate_non_uniform...")
generate_non_uniform(2, cnf, 2, 3, [GenerationRequest(AssertionType.EQ, 2, [Var(-2)])])
print("Success.")
