"""Provides the CNFState class, which is used to easily pass specific state
between various functions without over-complicating the functions' parameter
lists or return values.
"""


from dataclasses import dataclass, field
from typing import Iterator

from .simple_types import Clause, Count, CNF, Var


@dataclass
class CNFState:
    """Keeps track of the number of variables used during various operations on
    a CNF formula. This class is not strictly necessary, but it makes the code
    easier to deal with.

    A fresh state with no variables can be instantiated in one of two ways:

        fresh_state_1 = CNFState()
        fresh_state_2 = CNFState.empty
    """

    var_count: Count = field(default=Count(0))
    cnf: CNF = field(default_factory=list)

    @classmethod
    @property
    def empty(cls):
        """An empty CNFState."""
        return cls()

    def get_fresh(self) -> Count:
        """Creates a new variable for the formula."""
        # FIXME: mypy seems to be unhappy with this assignment because it
        #        appears to believe `self.var_count` is an int and not a Count.
        #        Executable versions at the time of writing:
        #            python3 --version :: Python 3.9.1
        #            mypy --version    :: mypy 0.790
        self.var_count += 1  # type: ignore
        return self.var_count

    def get_n_fresh(self, n: int) -> Iterator[Count]:
        """Generates the next n variables, numbered sequentially."""
        for _ in range(n):
            yield self.get_fresh()

    def append_cnf(self, new_entry: CNF):
        """Appends a CNF formula to the existing CNF formula."""
        self.cnf += new_entry

    def set_to_zero(self, variable: Var):
        """Zeroes the specified variable by appending its negation to the
        existing CNF formula.
        """
        self.append_cnf([[Var(-variable)]])

    def zero_out(self, in_list: Clause):
        """Appends a CNF formula negating the existing CNF formula."""
        self.append_cnf([[Var(-x)] for x in in_list])
