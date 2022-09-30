"""This module provides non-uniform CNF sampling functionality through the
:func:`sample_non_uniform` function.

.. note::

    For compatibility with older testing mechanisms, there is also the
    :func:`sample_non_uniform_from_specification` function, which takes a
    :class:`.ProblemSpecification` as input. The :class:`.ProblemSpecification`
    can be generated with an appropriately formatted JSON file, which is how
    inputs were given in the original Haskell version of SweetPea Core. This
    function (and the associated classes) will likely be removed from SweetPea
    at some point.
"""


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
    """Samples solutions to a CNF problem non-uniformly. Produces ``count``
    solutions, each with a support set of length ``support``.
    """
    with temporary_cnf_file() as cnf_file:
        combine_and_save_cnf(cnf_file, initial_cnf, fresh, support, generation_requests)
        print("Running CryptoMiniSat...")
        solutions = compute_solutions(cnf_file, support, count)
        return [Solution(solution, 1) for solution in solutions]


def sample_non_uniform_from_specification(spec: ProblemSpecification) -> List[Solution]:
    """Samples solutions to a CNF problem non-uniformly, using a
    :class:`.ProblemSpecification`.

    .. note::

        This function exists for easier legacy compatibility from when
        SweetPea's input was given as JSON files. This should no longer be
        necessary.
    """
    return sample_non_uniform(spec.sample_count, spec.cnf, spec.fresh, spec.support, spec.requests)


def compute_solutions(filename: Path,
                      support: int,
                      count: int,
                      solutions: Optional[List[List[int]]] = None,
                      use_docker: bool = DEFAULT_DOCKER_MODE_ON
                      ) -> List[List[int]]:
    """Attempts to solve a CNF problem ``count`` times with CryptoMiniSAT. Each
    time a solution is generated, it is added to the problem file's header so
    new solutions may be generated. If at any point CryptoMiniSAT fails to
    generate a solution, execution terminates and the existing list of
    solutions will be returned.
    """
    # TODO: Implement iteratively instead of recursively.
    while True:
        if solutions is None:
            solutions = []
        if count == 0:
            return solutions
        solution = cryptominisat_solve(filename, use_docker)
        if not solution:
            return solutions
        solution = solution[:support]
        update_file(filename, solution)
        count -= 1
        solutions += [solution]


def update_file(filename: Path, solution: List[int]):
    """Updates a CNF file by adding a solution to the enclosed problem to the
    header. This allows CryptoMiniSAT to find additional (distinct) solutions
    to the problem.
    """

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
