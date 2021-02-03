"""This module provides simple CNF generation functionality."""


from typing import List

from ..cnf import CNF
from .tools.unigen import call_unigen
from .utility import GenerationRequest, Solution, combine_and_save_cnf, temporary_cnf_file


__all__ = ['generate_simple']


def generate_simple(initial_cnf: CNF,
                    fresh: int,
                    support: int,
                    generation_requests: List[GenerationRequest],
                    use_docker: bool = True
                    ) -> List[Solution]:
    # TODO DOC
    with temporary_cnf_file() as cnf_file:
        combine_and_save_cnf(cnf_file, initial_cnf, fresh, support, generation_requests)
        solution_str = call_unigen(cnf_file, docker_mode=use_docker)
        return [build_solution(line) for line in solution_str.strip().splitlines()]


def build_solution(line: str) -> Solution:
    # TODO DOC
    parts = line.replace('v', '').strip().split()
    assignment = [int(p) for p in parts[:-1]]
    frequency = int(parts[-1].split(':')[-1])
    return Solution(assignment, frequency)
