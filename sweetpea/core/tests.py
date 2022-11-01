"""This module provides tests for SweetPea's Core framework."""


from operator import invert
from typing import Callable, List, Optional, TypeVar

from .cnf import CNF, Var


T = TypeVar('T')


def sequence(xss: List[List[T]]) -> List[List[T]]:
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


def ripple_carry_dimacs(num_digits: int) -> List[str]:
    cnf = CNF()
    variables = cnf.get_n_fresh(num_digits)
    # TODO: Verify that it's correct to use variables that are not part of the
    #       CNF formula for the second argument to ripple_carry.
    cnf.ripple_carry(variables,
                     [Var(n) for n in range(num_digits + 1, (num_digits * 2) + 1)])
    all_inputs = permute_complements(variables)
    result_cnfs = [CNF([[x] for x in xs]) + cnf for xs in all_inputs]
    return [result_cnf.as_dimacs_string() for result_cnf in result_cnfs]


def pop_count_dimacs(num_digits: int) -> List[str]:
    cnf = CNF()
    variables = cnf.get_n_fresh(num_digits)
    cnf.pop_count(variables, 0)
    all_inputs = permute_complements(variables)
    result_cnfs = [CNF([[x] for x in xs]) + cnf for xs in all_inputs]
    return [result_cnf.as_dimacs_string() for result_cnf in result_cnfs]


def permute_complements(xs: List[T],
                        to_position: Optional[int] = None,
                        complement_func: Callable[[T], T] = invert) -> List[List[T]]:
    """Given a list of elements, computes a list of each possible permutation
    of that list with complements. That is, given a list like:

        [1, 2, 3]

    permute_complements will return:

        [[1, 2, 3], [-1, 2, 3], [1, -2, 3], [-1, -2, 3],
         [1, 2, -3], [-1, 2, -3], [1, -2, -3], [-1, -2, -3]]
    """
    if not xs:
        return []
    if to_position is None:
        return permute_complements(xs, len(xs) - 1, complement_func)
    elif to_position == 0:
        return [[xs[0]], [complement_func(xs[0])]]
    else:
        results: List[List[T]] = []
        permuted_xss = permute_complements(xs, to_position - 1, complement_func)
        for permuted_xs in permuted_xss:
            results.append([x for x in permuted_xs] + [xs[to_position]])
        for permuted_xs in permuted_xss:
            results.append([x for x in permuted_xs] + [complement_func(xs[to_position])])
        return results


def assert_k_of_n_dimacs(num_digits: int, k: int) -> str:
    cnf = CNF()
    variables = cnf.get_n_fresh(num_digits)
    cnf.assert_k_of_n(k, variables)
    return cnf.as_dimacs_string()


def assert_all_k_of_n_dimacs(num_digits: int) -> List[str]:
    return [assert_k_of_n_dimacs(num_digits, k) for k in range(num_digits + 1)]


def pop_count_k_less_than_n_dimacs(num_digits: int, k: int) -> str:
    cnf = CNF()
    variables = cnf.get_n_fresh(num_digits)
    cnf.assert_k_less_than_n(k, variables)
    return cnf.as_dimacs_string()


def pop_count_all_k_less_than_n_dimacs(num_digits: int) -> List[str]:
    return [pop_count_k_less_than_n_dimacs(num_digits, k) for k in range(num_digits + 1)]
