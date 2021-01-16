"""Provides simple type aliases used in SweetPea Core."""

# Allow type annotations to refer to not-yet-declared types.
from __future__ import annotations

from typing import Iterable, Iterator, NewType, Union

from .simple_sequence import SimpleSequence


__all__ = ['Count', 'Var', 'Clause', 'CNF']


Count = NewType('Count', int)


class Var:
    """A variable for use in a CNF formula.

    This is essentially a wrapper for the builtin `int` type, but with a few
    advantages:

      * It is semantically distinct from an `int`, so reading code is more
        sensible.
      * Type aliases for `int` can be obnoxious to deal with because you may
        want to use `int`-supported operations (like addition, negation, etc),
        but these are not cross-type compatible (i.e., `Var(3) + 2` produces an
        error in mypy).
      * We can implement custom behavior as a sort of micro-DSL without much
        overhead or issue.
    """

    def __init__(self, value: int):
        self._val: int
        if isinstance(value, Var):
            self._val = value._val
        elif isinstance(value, int):
            if value == 0:
                raise ValueError(f"Var values must be non-zero integers; got {value}")
            self._val = value
        else:
            raise TypeError(f"expected 'int'; got '{type(value).__name__}'")

    def __repr__(self) -> str:
        return f"Var({self._val})"

    def __str__(self) -> str:
        return str(self._val)

    def __int__(self) -> int:
        return self._val

    def __invert__(self) -> Var:
        """Logical NOT."""
        return Var(-self._val)

    def __or__(self, other: Var) -> Clause:
        """Logical OR."""
        if isinstance(other, Var):
            return Clause(self, other)
        return NotImplemented

    def __and__(self, other: Var) -> CNF:
        """Logical AND."""
        if isinstance(other, Var):
            return CNF(Clause(self), Clause(other))
        return NotImplemented

    def __xor__(self, other: Var) -> CNF:
        """Logical XOR."""
        if isinstance(other, Var):
            return CNF([[self, other], [~self, ~other]])
        return NotImplemented

    def __mod__(self, other: Var) -> CNF:
        """Logical XNOR."""
        # NOTE: This method is used to implement logical XNOR instead of
        #       modulo. If only Python allowed custom operators.
        if isinstance(other, Var):
            return CNF([[self, ~other], [~self, other]])
        return NotImplemented


class Clause(SimpleSequence[Var]):
    """A sequence of variables. Clauses indicate logical disjunction between
    the variables, i.e., `Clause(Var(3), Var(7))` encodes (3 ∨ 7).

    Clauses can also be instantiated with a list of variables. This method will
    also accept raw integers instead of instances of `Var`. For example:

        Clause([1, -2, 3])

    corresponds to the formula (1 ∨ ¬2 ∨ 3).
    """

    @classmethod
    @property
    def _element_type(cls):
        return Var

    def __add__(self, other: Union[Clause, Var]) -> Clause:
        """Logical OR. This alias exists due to the list-like interface of
        Clauses.
        """
        if isinstance(other, Clause):
            return Clause(*self, *other)
        if isinstance(other, Var):
            return Clause(*self, other)
        return NotImplemented

    def __radd__(self, other: Var) -> Clause:
        if isinstance(other, Var):
            return Clause(other, *self)
        return NotImplemented

    def __and__(self, other: Union[Clause, Var]) -> CNF:
        """Logical AND."""
        if isinstance(other, Clause):
            return CNF(self, other)
        if isinstance(other, Var):
            return CNF(self, Clause(other))
        return NotImplemented

    def __rand__(self, other: Var) -> CNF:
        if isinstance(other, Var):
            return CNF(Clause(other), self)
        return NotImplemented

    def __or__(self, other: Union[Clause, Var]):
        """Logical OR."""
        return self + other

    def __ror__(self, other: Var):
        return other + self


class CNF(SimpleSequence[Clause]):
    """A conjunction of disjunction clauses. For example:

        CNF(Clause(Var(3), Var(7)), Clause(Var(1), Var(13)))

    corresponds to the CNF formula ((3 ∨ 7) ∧ (1 ∨ 13)).

    CNF formulas can also be instantiated with a list of lists of variables,
    where each inner list represents a clause and the outer list represents the
    CNF formula itself. This method will also accept raw integers instead of
    instances of `Var`. For example:

        CNF([[1, 2, -3], [-2, 7, 1]])

    corresponds to the CNF formula ((1 ∨ 2 ∨ ¬3) ∧ (¬2 ∨ 7 ∨ 1)).
    """

    @classmethod
    @property
    def _element_type(cls):
        return Clause

    _num_vars: int

    @classmethod
    @property
    def empty(cls):
        """An empty CNF formula."""
        return cls()

    def __init__(self, *values):
        super().__init__(*values)
        self._num_vars = 0

    def __add__(self, other: Union[CNF, Clause, Var]) -> CNF:
        """Logical OR. This alias exists due to the list-like interface of CNF
        formulas.
        """
        if isinstance(other, CNF):
            return CNF(*self, *other)
        if isinstance(other, Clause):
            return CNF(*self, other)
        if isinstance(other, Var):
            return CNF(*self, [other])
        return NotImplemented

    def __iadd__(self, other: Union[CNF, Clause, Iterable[Clause], Var]) -> CNF:
        if isinstance(other, CNF):
            self._vals += other._vals
            return self
        if isinstance(other, Clause):
            self._vals += [other]
            return self
        if isinstance(other, (list, tuple)):
            self._vals += other
            return self
        if isinstance(other, Var):
            self._vals += [Clause(other)]
        return NotImplemented

    def __and__(self, other: Var) -> CNF:
        """Logical AND."""
        return CNF(self._vals + [other])

    def __rand__(self, other: Var) -> CNF:
        return CNF([other] + self._vals)

    def __or__(self, other: Var) -> CNF:
        """Logical OR."""
        return CNF([*self[:-1], self[-1] + other])

    def __ror__(self, other: Var) -> CNF:
        return CNF([other + self[0], *self[1:]])

    def __pow__(self, other: Var) -> CNF:
        """Distribution of a variable across the clauses of a CNF formula."""
        if isinstance(other, Var):
            return CNF([clause | other for clause in self])
        return NotImplemented

    def __rpow__(self, other: Var) -> CNF:
        if isinstance(other, Var):
            return CNF([other | clause for clause in self])
        return NotImplemented

    def get_fresh(self) -> int:
        """Creates a new variable for the formula."""
        self._num_vars += 1
        return self._num_vars

    def get_n_fresh(self, n: int) -> Iterator[int]:
        """Generates the next n variables, numbered sequentially."""
        for _ in range(n):
            yield self.get_fresh()

    def append(self, other: Union[CNF, Clause, Iterable[Clause], Var]):
        """Appends a CNF formula to this formula."""
        self += other

    def set_to_zero(self, variable: Var):
        """Zeroes the specified variable by appending its negation to the
        existing CNF formula.
        """
        self.append(~variable)

    def zero_out(self, in_list: Iterable[Var]):
        """Appends a CNF formula negating the existing CNF formula."""
        for variable in in_list:
            self.set_to_zero(variable)

    def set_to_one(self, variable: Var):
        """Sets the specified variable to 1 by appending it to the existing CNF
        formula.
        """
        self.append(variable)

    def distribute(self, variable: Var):
        """Distributes a variable across each clause in the CNF formula."""
        self._vals = [variable | clause for clause in self]

    @staticmethod
    def and_vars(a: Union[int, Var], b: Union[int, Var]) -> CNF:
        """Returns a CNF formula encoding (a ∧ b)."""
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return a & b

    @staticmethod
    def or_vars(a: Union[int, Var], b: Union[int, Var]) -> CNF:
        """Returns a CNF formula encoding (a ∨ b)."""
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return CNF(a | b)

    @staticmethod
    def xor_vars(a: Union[int, Var], b: Union[int, Var]) -> CNF:
        """Returns a CNF formula encoding (a ⊕ b) as ((a ∨ b) ∧ (¬a ∨ ¬b))."""
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return a ^ b

    @staticmethod
    def xnor_vars(a: Union[int, Var], b: Union[int, Var]) -> CNF:
        """Returns a CNF formula encoding (a ⊙ b) as ((a ∨ ¬b) ∧ (¬a ∨ b))."""
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return a % b
