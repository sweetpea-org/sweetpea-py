from abc import ABC
from dataclasses import dataclass
from enum import auto, Enum
from typing import List, Optional

from .code_gen import *
from .core import *
from .data_structures import *
from .haskell.control.monad.trans.state import *
from .haskell.data.maybe import *
from .haskell.data.ord import *


@dataclass
class Request:
    equality_type: Ordering
    k: int
    boolean_values: List[Var]


class ActionType(Enum):
    BuildCNF = auto()
    SampleNonUniform = auto()
    IsSAT = auto()


@dataclass
class JSONSpec:
    action: Optional[ActionType]
    fresh: Optional[int]
    cnfs: Optional[CNF]
    cnf_id: Optional[str]
    support: Optional[int]
    requests: Optional[List[Request]]
    unigen_options: Optional[str]
    sample_count: Optional[int]


def process_requests(spec: JSONSpec) -> str:
    state = State(init_state(from_just(spec.fresh)))
    for request in from_just(spec.requests):
        process_a_request(request, state)
    (final_n_vars, cnf) = state.get()
    final_cnf = cnf + from_just(spec.cnfs)
    return show_DIMACS(final_cnf, final_n_vars, from_just(spec.support))


def process_a_request(request: Request, state: CountState):
    if request.equality_type is EQ:
        assert_k_of_n(request.k, request.boolean_values, state)
    elif request.equality_type is LT:
        k_less_than_n(request.k, request.boolean_values, state)
    else:
        k_greater_than_n(request.k, request.boolean_values, state)
