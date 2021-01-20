from .data_structures import CNF
from .haskell.data.list.split import chunks_of


__all__ = ['show_DIMACS', 'show_CNF']


def show_DIMACS(cnf: CNF, num_vars: int, support: int) -> str:
    return '\n'.join([
        f"p cnf {num_vars} {len(cnf)}",
        '\n'.join([
            "c ind " + ' '.join(map(str, chunk)) + " 0"
            for chunk in chunks_of(10, list(range(1, support + 1)))
        ]),
        show_CNF(cnf),
    ])


def show_CNF(cnf: CNF) -> str:
    return ''.join(map(lambda and_clause: ' '.join(map(str, and_clause)) + " 0\n", reversed(cnf)))
