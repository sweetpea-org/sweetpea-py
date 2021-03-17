"""This module provides non-uniform CNF sampling functionality."""


from pathlib import Path
from typing import List, Optional

from ..cnf import CNF
from .tools.cryptominisat import DEFAULT_DOCKER_MODE_ON, cryptominisat_solve
from .utility import GenerationRequest, ProblemSpecification, Solution, combine_and_save_cnf, temporary_cnf_file


__all__ = ['sample_non_uniform', 'sample_non_uniform_from_specification']


def sample_non_uniform(count: int,
                       initial_cnf: CNF,
                       fresh: int,
                       support: int,
                       generation_requests: List[GenerationRequest]
                       ) -> List[Solution]:
    # TODO DOC
    with temporary_cnf_file() as cnf_file:
        combine_and_save_cnf(cnf_file, initial_cnf, fresh, support, generation_requests)
        solutions = compute_solutions(cnf_file, support, count)
        return [Solution(solution, 1) for solution in solutions]


def sample_non_uniform_from_specification(spec: ProblemSpecification) -> List[Solution]:
    # TODO DOC
    return sample_non_uniform(spec.count, spec.cnf, spec.fresh, spec.support, spec.requests)


def compute_solutions(filename: Path,
                      support: int,
                      count: int,
                      solutions: Optional[List[List[int]]] = None,
                      use_docker: bool = DEFAULT_DOCKER_MODE_ON
                      ) -> List[List[int]]:
    # TODO DOC
    if solutions is None:
        solutions = []
    if count == 0:
        return solutions
    solution = cryptominisat_solve(filename, use_docker)
    if not solution:
        return solutions
    solution = solution[:support]
    update_file(filename, solution)
    return compute_solutions(filename, support, count - 1, solutions + [solution])


def update_file(filename: Path, solution: List[int]):
    # TODO DOC

    def update_header(additional_clause_count: int, header: str) -> str:
        segments = header.strip().split()
        new_clause_count = int(segments[3]) + additional_clause_count
        return ' '.join(segments[:3] + [str(new_clause_count)])

    def add_clause_to_header(clause: str) -> str:
        return update_header(1, clause)

    lines = filename.read_text().strip().splitlines()
    updated_header = add_clause_to_header(lines[0])
    negated_solution = [-1 * var for var in solution]
    negated_solution_str = ' '.join(str(var) for var in negated_solution + [0])
    updated_lines = [updated_header] + lines[1:] + [negated_solution_str]
    updated_contents = '\n'.join(updated_lines)
    filename.write_text(updated_contents)
