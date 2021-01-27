from dataclasses import dataclass
from enum import auto, Enum
from json import JSONDecodeError, loads as str_to_json
from typing import Any, Dict, List, Optional

from .code_gen import show_DIMACS
from .core import init_state, assert_k_of_n, k_less_than_n, k_greater_than_n
from .data_structures import Var, CNF, CountState
from .haskell.control.monad.trans.state import State
from .haskell.data.maybe import from_just
from .haskell.data.ord import Ordering, LT, EQ


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

    @staticmethod
    def decode(json_str: str) -> Optional['JSONSpec']:
        def decode(json: Dict[str, Any]):
            fields: Dict[str, Any] = {}
            for field_name in JSONSpec.__annotations__.keys():
                fields[field_name] = json.get(field_name, None)
            return JSONSpec(**fields)
        try:
            return str_to_json(json_str, object_hook=decode)
        except JSONDecodeError:
            return None


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
