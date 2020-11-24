from functools import reduce
from typing import cast, Callable, List

from .code_gen import show_DIMACS
from .core import assert_k_of_n, k_less_than_n, half_adder, full_adder, ripple_carry, pop_count
from .data_structures import (
    Var,
    SATResult, Unsatisfiable, ParseError, Correct, WrongResult,
    init_state, and_CNF)
from .haskell.control.monad.trans.state import State
from .haskell.data.list import concat_map
from .haskell.prelude import snd, sequence
from .haskell.text.read import read_maybe


def test_half_adder_DIMACS() -> List[str]:
    # This poor code is good motivation to either improve the State "monad"
    # translation or else seek an entirely different representation.
    state = State(init_state(2))
    _ = half_adder(Var(1), Var(2), state)
    constraints = snd(state.get())
    all_inputs = sequence([[1, -1], [2, -2]])
    test_constraints = [constraints + and_CNF(cast(List[Var], x[0])) + and_CNF(cast(List[Var], x[1]))
                        for x in all_inputs]
    return [show_DIMACS(cnf, 4, 0) for cnf in test_constraints]


def test_full_adder_DIMACS() -> List[str]:
    state = State(init_state(3))
    _ = full_adder(Var(1), Var(2), Var(3), state)
    constraints = snd(state.get())
    all_inputs = sequence([[1, -1], [2, -2], [3, -3]])
    test_constraints = [constraints
                        + and_CNF(cast(List[Var], x[0]))
                        + and_CNF(cast(List[Var], x[1]))
                        + and_CNF(cast(List[Var], x[2]))
                        for x in all_inputs]
    return [show_DIMACS(cnf, 5, 0) for cnf in test_constraints]


def soln_full_adder() -> List[str]:
    all_inputs = sequence([[1, -1], [2, -2], [3, -3]])
    return ["s SATISFIABLE\nv  " + ' '.join(map(str, compute_soln_full_adder(x, 4, 5))) + " 0\n"
            for x in all_inputs]


def compute_soln_full_adder(incoming: List[int], c_index: int, s_index: int) -> List[int]:
    total = sum(map(lambda x: 0 if x < 0 else 1, incoming))
    c = c_index if total > 1 else (- c_index)
    s = s_index if total % 2 == 0 else (- s_index)
    return incoming + [c] + [s]


def ripple_carry_DIMACS(num_digits: int) -> List[str]:
    state = State(init_state(num_digits))
    _ = ripple_carry([Var(x) for x in range(1, num_digits + 1)],
                     [Var(x) for x in range(num_digits + 1, (num_digits * 2) + 1)],
                     state)
    final_n_vars, cnf = state.get()
    all_inputs = exhaust(list(range(1, num_digits + 1)))
    return [show_DIMACS([cast(List[Var], x)] + cnf, final_n_vars, 0) for x in all_inputs]


def pop_count_DIMACS(num_digits: int) -> List[str]:
    state = State(init_state(num_digits))
    _ = pop_count([Var(x) for x in range(1, num_digits + 1)], state)
    final_n_vars, cnf = state.get()
    all_inputs = exhaust(list(range(1, num_digits + 1)))
    return [show_DIMACS([cast(List[Var], x)] + cnf, final_n_vars, 0) for x in all_inputs]


def exhaust(xs: List[int]) -> List[List[int]]:
    if not xs:
        return []
    x, *xs = xs
    if not xs:
        return [[x], [-x]]
    else:
        return concat_map(lambda ys: [[x] + ys, [-x] + ys], exhaust(xs))


def assert_k_of_n_DIMACS(num_digits: int, k: int) -> str:
    state = State(init_state(num_digits))
    _ = assert_k_of_n(k, [Var(x) for x in range(1, num_digits + 1)], state)
    final_n_vars, cnf = state.get()
    return show_DIMACS(cnf, final_n_vars, 0)


def assert_all_k_of_n_DIMACS(num_digits: int) -> List[str]:
    return [assert_k_of_n_DIMACS(num_digits, k) for k in range(0, num_digits + 1)]


def pop_count_k_less_than_n_DIMACS(num_digits: int, k: int) -> str:
    state = State(init_state(num_digits))
    _ = k_less_than_n(k, [Var(x) for x in range(1, num_digits + 1)], state)
    final_n_vars, cnf = state.get()
    return show_DIMACS(cnf, final_n_vars, 0)


def pop_count_all_k_less_than_n_DIMACS(num_digits: int) -> List[str]:
    return [pop_count_k_less_than_n_DIMACS(num_digits, k) for k in range(1, num_digits + 1)]


def test_result_pop_count(result: str, set_vars: int) -> SATResult:
    lines = result.split('\n')
    if len(lines) == 1:
        return Unsatisfiable()
    state = State(init_state(set_vars))
    result_vars = pop_count([Var(x) for x in range(1, set_vars + 1)], state)
    # There is no good Python equivalent to mapM as used in the original code.
    in_list = [read_maybe(int, x) for x in concat_map(lambda l: l[1:].split(), lines[1:])[:-1]]
    if all(in_list):
        # Every value in the list was successfully converted to an integer.
        return is_pop_count_correct(cast(List[int], in_list), set_vars, cast(List[int], result_vars))
    else:
        # There exists at least one None in the list.
        return ParseError()


def is_pop_count_correct(in_list: List[int], set_vars: int, result_vars: List[int]) -> SATResult:
    n_set_bits = sum([0 if x < 0 else 1 for x in in_list[:set_vars]])
    result_bools = [in_list[x - 1] > 0 for x in result_vars]
    result_set_bits = reduce(lambda acc, bit: acc * 2 + 1 if bit else acc * 2, result_bools, 0)
    if n_set_bits == result_set_bits:
        return Correct()
    else:
        return WrongResult(n_set_bits, result_set_bits)


def test_result_k_and_n(result: str, k: int, n_set_vars: int, eq_or_less_than: Callable[[int, int], bool]) -> SATResult:
    lines = result.split('\n')
    if len(lines) == 1:
        return Unsatisfiable()
    # There is no good Python equivalent to mapM as used in the original code.
    in_list = [read_maybe(int, x) for x in concat_map(lambda l: l[1:].split(), lines[1:])[:-1]]
    if all(in_list):
        return is_k_and_n_correct(cast(List[int], in_list), k, n_set_vars, eq_or_less_than)
    else:
        return ParseError()


def is_k_and_n_correct(in_list: List[int], k: int, n_set_vars: int, eq_or_less_than: Callable[[int, int], bool]) -> SATResult:
    n_set_bits = sum([0 if x < 0 else 1 for x in in_list[:n_set_vars]])
    if eq_or_less_than(n_set_bits, k):
        return Correct()
    else:
        return WrongResult(k, n_set_bits)
