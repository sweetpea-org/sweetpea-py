"""This module provides functionality to test whether a CNF formula is
satisfiable.
"""


from ..cnf import CNF
from .tools.cryptominisat import cryptominisat_is_satisfiable
from .utility import save_cnf, temporary_cnf_file


__all__ = ['cnf_is_satisfiable']


def cnf_is_satisfiable(cnf: CNF) -> bool:
    """Determines whether the given CNF formula is satisfiable."""
    with temporary_cnf_file() as cnf_file:
        save_cnf(cnf_file, cnf)
        result = cryptominisat_is_satisfiable(cnf_file)
    if result:
        return True
    else:
        return False
