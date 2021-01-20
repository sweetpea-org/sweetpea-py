from contextlib import contextmanager
from enum import Enum, auto
from pathlib import Path
from shlex import split as shell_split
from subprocess import run
from typing import Callable, Iterator, List, NamedTuple, NoReturn, Optional
from uuid import uuid4 as generate_UUID

from .code_gen import show_DIMACS
from .core import assert_k_of_n, k_less_than_n, k_greater_than_n
from .data_structures import CNF, CountState, Var, init_state
from .haskell.control.monad.trans.state import State
from .haskell.data.list import drop, intercalate, take, unwords
from .unigen import call_unigen


@contextmanager
def temporary_CNF_file(base_path: Path = Path('.')) -> Iterator[Path]:
    cnf_file = base_path / Path(str(generate_UUID())).with_suffix('.cnf')
    try:
        yield cnf_file
    finally:
        if cnf_file.exists():
            cnf_file.unlink()


class GenerationType(Enum):
    """An enum that provides access to the three methods of CNF generation:

        1. Assert k == n.
        2. Assert k < n.
        3. Assert k > n.

    Instances of this enum also have the `.function` property, which allows
    calling the associated function.
    """
    EQ = (auto(), assert_k_of_n)
    LT = (auto(), k_less_than_n)
    GT = (auto(), k_greater_than_n)

    @property
    def function(self) -> Callable[[int, List[Var], CountState], NoReturn]:
        """Returns the function associated with this value.

        This property exists primarily to provide type-hinting, because an
        Enum's `.value` property is automatically given an `Any` type that
        cannot be overwritten.
        """
        return self.value[1]


class GenerationRequest(NamedTuple):
    generationType: GenerationType
    k: int
    boolean_values: List[Var]


class SolutionSpec(NamedTuple):
    assignment: List[int]
    frequency: int


def generate_CNF(initial_CNF: CNF,
                 fresh: int,
                 support: int,
                 generation_requests: List[GenerationRequest],
                 use_docker: bool = True
                 ) -> List[SolutionSpec]:
    def build_solution(line: str) -> SolutionSpec:
        parts = line.replace('v', '').strip().split()
        assignment = [int(s) for s in parts[:-1]]
        frequency = int(parts[-1].split(':')[-1])
        return SolutionSpec(assignment, frequency)

    with temporary_CNF_file() as cnf_file:
        save_CNF(cnf_file, initial_CNF, fresh, support, generation_requests)
        solution_str = call_unigen(cnf_file, docker_mode=use_docker)
        return [build_solution(line) for line in solution_str.strip().splitlines()]


# TODO
# split generation functions into new sub-module:
# sweetpea/core/generation/uniform
#                      .../non_uniform
#                      .../etc.
#                      .../__init__  <-- export stuff here

def sample_non_uniform(count: int,
                       initial_CNF: CNF,
                       fresh: int,
                       support: int,
                       generation_requests: List[GenerationRequest]
                       ) -> List[SolutionSpec]:
    with temporary_CNF_file() as cnf_file:
        save_CNF(cnf_file, initial_CNF, fresh, support, generation_requests)
        solutions = compute_solutions(cnf_file, support, count)
        return [SolutionSpec(solution, 1) for solution in solutions]


def compute_solutions(filename: Path, support: int, count: int, solutions: Optional[List[List[int]]] = None) -> List[List[int]]:
    if solutions is None:
        solutions = []
    if count == 0:
        return solutions
    command = shell_split(f"cryptominisat5 --verb=0 {filename}")
    result = run(command, capture_output=True)
    raw_solution = parse_CMSat_solution(result.stdout.decode())
    if not raw_solution:
        return solutions
    solution = take(support, raw_solution)
    update_file(filename, solution)
    return compute_solutions(filename, support, count - 1, solutions + [solution])


def update_file(filename: Path, solution: List[int]):
    lines = filename.read_text().strip().splitlines()
    updated_header = add_clause_to_header(lines[0])
    negated_solution = [-1 * val for val in solution]
    negated_solution_str = unwords([str(val) for val in negated_solution + [0]])
    updated_lines = [updated_header] + drop(1, lines) + [negated_solution_str]
    updated_contents = intercalate('\n', updated_lines)
    filename.write_text(updated_contents)


def add_clause_to_header(s: str) -> str:
    return update_header(1, s)


def update_header(additional_clause_count: int, header: str) -> str:
    segments = header.strip().split()
    new_clause_count = int(segments[3]) + additional_clause_count
    return ' '.join(take(3, segments) + [str(new_clause_count)])


def parse_CMSat_solution(output: str):
    if "s UNSATISFIABLE" in output:
        return []
    parts = ''.join(line for line in map(str.strip, output.strip().splitlines())
                    if line.startswith('v')).replace('v', '').split()
    return [int(s) for s in parts]


def build_CNF(initial_CNF: CNF,
              fresh: int,
              support: int,
              generation_requests: List[GenerationRequest]) -> str:
    """Returns a string encoding a CNF."""
    state = State(init_state(fresh))
    for request in generation_requests:
        request.generationType.function(request.k, request.boolean_values, state)
    (final_n_vars, generated_CNF) = state.get()
    final_CNF = generated_CNF + initial_CNF
    return show_DIMACS(final_CNF, final_n_vars, support)


def save_CNF(filename: Path,
             initial_CNF: CNF,
             fresh: int,
             support: int,
             generation_requests: List[GenerationRequest]):
    cnf_str = build_CNF(initial_CNF, fresh, support, generation_requests)
    filename.write_text(cnf_str)
