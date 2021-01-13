"""Provides the CountState class, which is used to easily pass specific state
between various functions without over-complicating the functions' parameter
lists or return values.
"""


from dataclasses import dataclass

from .simple_types import Count, CNF


@dataclass
class CountState:
    """Keeps track of the state of counts during various operations. This class
    is not strictly necessary, but it makes the code easier to deal with.
    """

    count: Count
    cnf: CNF

    @classmethod
    @property
    def empty(cls):
        """Creates an empty CountState."""
        return cls(0, [[]])
