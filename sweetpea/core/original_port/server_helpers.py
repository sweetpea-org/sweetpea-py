from typing import List

from .data_structures import Var, CNF


__all__ = [
    'add_clause_to_header', 'update_header', 'cnf_clause_to_line',
    'cnf_to_line', 'add_clauses_to_cnf', 'parse_CMSat_solution',
    'is_formula_sat'
]


def add_clause_to_header(header: str) -> str:
    return update_header(1, header)


def update_header(additional_clause_count: int, header: str) -> str:
    segments: List[str] = header.strip().split(' ')
    new_clause_count: int = additional_clause_count + int(segments[3])
    return ''.join(segments[:3] + [str(new_clause_count)])


def cnf_clause_to_line(clause: List[Var]) -> str:
    return ' '.join([str(elem) for elem in clause] + ["0"])


def cnf_to_line(cnf: CNF) -> List[str]:
    return [cnf_clause_to_line(clause) for clause in cnf]


def add_clauses_to_cnf(cnf_string: str, clauses: CNF) -> str:
    lines = cnf_string.strip().split('\n')
    updated_header = update_header(len(clauses), lines[0])
    updated_lines = [updated_header] + lines[1:] + cnf_to_line(clauses)
    return '\n'.join(updated_lines)


def parse_CMSat_solution(output: str) -> List[int]:
    if 's UNSATISFIABLE' in output:
        return []
    lines = [line for line in
             (segment.strip() for segment in output.split('\n'))
             if line.startswith('v')]
    return [int(s) for s in ''.join([line.replace('v', '') for line in lines]).split(' ')]


def is_formula_sat(output: str) -> bool:
    return 's SATISFIABLE' in output
