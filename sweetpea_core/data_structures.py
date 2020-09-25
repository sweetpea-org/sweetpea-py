from abc import ABC
from dataclasses import dataclass
from typing import cast, List, NewType, Tuple

from haskell.control.monad.trans.state import *


__all__ = [
    'Count', 'Var', 'Index', 'CNF',
    'CountingConstraint', 'Exactly', 'GreaterThan', 'LessThan',
    'Trial',
    'SATResult', 'Correct', 'Unsatisfiable', 'WrongResult', 'ParseError',
    'Logic', 'And', 'Or', 'Not', 'LogicVar', 'If', 'Iff',
    'empty_state', 'init_state', 'get_fresh', 'get_n_fresh', 'put_fresh',
    'append_CNF', 'zero_out', 'set_to_one', 'set_to_zero',
    'double_implies', 'a_double_implies_b_and_c', 'a_double_implies_list',
    'and_CNF', 'n_and_CNF', 'xor_CNF', 'distribute'
]


# AND of ORs
Count = NewType('Count', int)
Var = NewType('Var', int)
Index = NewType('Index', int)
CNF = List[List[Var]]


########################################
##
## CountingConstraint
##

@dataclass
class CountingConstraint(ABC):
    value: int
    vars: List[Var]

    def __new__(cls, *args, **kwargs):
        if cls is CountingConstraint:
            raise TypeError(f"Cannot directly instantiate ADT base class {cls.__name__}.")
        return super().__new__(cls)


@dataclass
class Exactly(CountingConstraint):
    pass


@dataclass
class GreaterThan(CountingConstraint):
    pass


@dataclass
class LessThan(CountingConstraint):
    pass


########################################
##
## Trial
##

@dataclass
class Trial:
    num_fields: int
    field_vars: List[Var]
    num_states: int
    state_vars: List[Var]


########################################
##
## SATResult
##

@dataclass
class SATResult(ABC):
    def __new__(cls, *args, **kwargs):
        if cls is SATResult:
            raise TypeError(f"Cannot directly instantiate ADT base class {cls.__name__}.")
        return super().__new__(cls)



@dataclass
class Correct(SATResult):
    pass


@dataclass
class Unsatisfiable(SATResult):
    pass


@dataclass
class WrongResult(SATResult):
    set_bits: int
    result_bits: int


@dataclass
class ParseError(SATResult):
    pass


########################################
##
## Logic
##

@dataclass
class Logic(ABC):
    def __new__(cls, *args, **kwargs):
        if cls is Logic:
            raise TypeError(f"Cannot directly instantiate ADT base class {cls.__name__}.")
        return super().__new__(cls)


@dataclass
class And(Logic):
    lhs: Logic
    rhs: Logic


@dataclass
class Or(Logic):
    lhs: Logic
    rhs: Logic


@dataclass
class Not(Logic):
    logic: Logic


@dataclass
class LogicVar(Logic):
    value: int


@dataclass
class If(Logic):
    condition: Logic
    then: Logic


@dataclass
class Iff(Logic):
    condition: Logic
    then: Logic


# TODO: Remove this. It's unused in the original code (not even exported!).
#       We include it here initially for completeness.
def process_q(a: Logic, p_var: Logic) -> Logic:
    if isinstance(a, And):
        (q0, q1) = (a.lhs, a.rhs)
        return And(Or(q0, p_var), process_q(q1, p_var))
    else:
        raise ValueError(f"process_q: first parameter must be instance of And. Got: {a}.")


########################################
##
## Helpful State Abstractions
##

CountStateState = Tuple[Count, CNF]
CountState = State[CountStateState]


# FIXME: Does this need to be made into a function to avoid undesirable
# container sharing?
empty_state: Tuple[Count, CNF] = (Count(0), [])


def init_state(max_var: int) -> Tuple[Count, CNF]:
    return (Count(max_var), [])


def get_fresh(state: CountState) -> Count:
    (num_vars, x) = state.get()
    state.put((Count(num_vars + 1), x))
    return Count(num_vars + 1)


def get_n_fresh(n: int, state: CountState) -> List[Count]:
    return [get_fresh(state) for _ in range(n)]


def put_fresh(value: int, state: CountState):
    (_, x) = state.get()
    state.put((Count(value), x))


def append_CNF(new_entry: CNF, state: CountState):
    (num_vars, x) = state.get()
    state.put((num_vars, new_entry + x))


def zero_out(in_list: List[Var], state: CountState):
    append_CNF([[Var(-x)] for x in in_list], state)


def set_to_one(value: Var, state: CountState):
    append_CNF([[value]], state)


def set_to_zero(value: Var, state: CountState):
    append_CNF([[Var(-value)]], state)


########################################
##
## Helper Functions
##

# (a or ~b) and (~a or b)
def double_implies(a: Var, b: Var) -> CNF:
    return [[a, Var(-b)], [Var(-a), b]]


# a <=> (b and c) = (-a v b) ^ (-a v c) ^ (a v -b v -c)
def a_double_implies_b_and_c(a: Var, b: Var, c: Var) -> CNF:
    return [[Var(-a), b], [Var(-a), c], [a, Var(-b), Var(-c)]]


# The double-implication generalization. See:
#
#     https://www.wolframalpha.com/input/?i=CNF+A++%3C%3D%3E+(B+%26%26+C+%26%26+D+%26%26+E)
#
# (-a or b)
# (-a or c)
# (-a or d)
# (a or -b or -c or -d)
def a_double_implies_list(a: Var, in_list: List[Var], state: CountState):
    # Make the list [-b, -c, ..., a].
    result_lhs: CNF = [[Var(-x) for x in (in_list + [a])]]
    # Make the list of lists [-a, b], [-a, c], ...
    result_rhs: CNF = [[Var(-a), x] for x in in_list]
    # Put the lists together.
    result: CNF = result_lhs + result_rhs
    append_CNF(result, state)


# Wraps values in an extra layer. This is just for readability.
def and_CNF(values: List[Var]) -> CNF:
    return [values]


# (~a v ~b)
def n_and_CNF(a: Var, b: Var) -> CNF:
    return [[Var(-a), Var(-b)]]


# (a v b) ^ (-a or -b)
def xor_CNF(a: Var, b: Var) -> CNF:
    return [[a, b], [Var(-a), Var(-b)]]


def distribute(input_ID: Var, cnf: CNF) -> CNF:
    return [[input_ID] + or_clause for or_clause in cnf]
