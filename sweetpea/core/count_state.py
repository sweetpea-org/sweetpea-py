"""Provides the CountState class, which is used to easily pass specific state
between various functions without over-complicating the functions' parameter
lists or return values.
"""


from dataclasses import dataclass, field
from typing import Iterator

from .simple_types import Clause, Count, CNF, Var


@dataclass
class CountState:
    """Keeps track of the state of counts during various operations. This class
    is not strictly necessary, but it makes the code easier to deal with.
    """

    count: Count
    cnf: CNF = field(default_factor=list)

    @classmethod
    @property
    def empty(cls):
        """Creates an empty CountState."""
        return cls(0)

    def get_fresh(self) -> Count:
        """Increments the count by 1 and return the result."""
        self.count += 1
        return self.count

    def get_n_fresh(self, n: int) -> Iterator[Count]:
        """Generates the next n variables in the state."""
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
