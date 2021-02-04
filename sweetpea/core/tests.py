"""This module provides tests for SweetPea's Core framework."""


from typing import List, TypeVar

from .cnf import CNF


_T = TypeVar('_T')


def sequence(xss: List[List[_T]]) -> List[List[_T]]:
    if not xss:
        return [[]]
    return [[x] + xs for x in xss[0] for xs in sequence(xss[1:])]


def test_half_adder_dimacs() -> List[str]:
    cnf = CNF()
    a = cnf.get_fresh()
    b = cnf.get_fresh()
    _, _ = cnf.half_adder(a, b)
    all_inputs = sequence([[a, ~a], [b, ~b]])
    test_constraints = [cnf & p[0] & p[1] for p in all_inputs]
    # test_constraints = [cnf + CNF(x[0]) + CNF(x[1]) for x in all_inputs]
    return [cnf.as_unigen_string() for cnf in test_constraints]


def test_full_adder_dimacs() -> List[str]:
    cnf = CNF()
    a, b, c = cnf.get_n_fresh(3)
    _, _ = cnf.full_adder(a, b, c)
    all_inputs = sequence([[a, ~a], [b, ~b], [c, ~c]])
    test_constraints = [cnf & t[0] & t[1] & t[2] for t in all_inputs]
    return [cnf.as_unigen_string() for cnf in test_constraints]


def soln_full_adder() -> List[str]:
    cnf = CNF()
    a, b, c = cnf.get_n_fresh(3)
    all_inputs = sequence([[a, ~a], [b, ~b], [c, ~c]])
    int_inputs = [[int(v) for v in sl] for sl in all_inputs]
    return ["s SATISFIABLE\nv " + ' '.join(map(str, compute_soln_full_adder(t, 4, 5))) + " 0\n"
            for t in int_inputs]


def compute_soln_full_adder(incoming: List[int], c_index: int, s_index: int) -> List[int]:
    total = sum(map(lambda x: 0 if x < 0 else 1, incoming))
    c = c_index if total > 1 else (-c_index)
    s = s_index if total & 1 else (-s_index)
    return incoming + [c] + [s]


# TODO: Implement the rest of the tests here!
