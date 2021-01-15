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
            self._val = value
        else:
            raise TypeError(f"expected 'int'; got '{type(value).__name__}'")

    def __repr__(self) -> str:
        return f"Var({self._val})"

    def __str__(self) -> str:
        return str(self._val)

    def __int__(self) -> int:
        return self._val

    def __neg__(self) -> Var:
        return Var(-self._val)

    def __invert__(self) -> Var:
        return -self

    def __add__(self, other) -> Var:
        if isinstance(other, Var):
            return Var(int(self) + int(other))
        if isinstance(other, int):
            return Var(int(self) + other)
        return NotImplemented

    def __iadd__(self, other):
        raise NotImplementedError()

    def __radd__(self, other) -> Var:
        if isinstance(other, int):
            return Var(other + int(self))
        return NotImplemented

    def __sub__(self, other) -> Var:
        if isinstance(other, Var):
            return Var(int(self) - int(other))
        if isinstance(other, int):
            return Var(int(self) - other)
        return NotImplemented

    def __isub__(self, other):
        raise NotImplementedError()

    def __rsub__(self, other) -> Var:
        if isinstance(other, int):
            return Var(other - int(self))
        return NotImplemented

    def __or__(self, other) -> Clause:
        if isinstance(other, Var):
            return Clause(self, other)
        return NotImplemented

    def __ior__(self, other):
        raise NotImplementedError()

    def __and__(self, other) -> CNF:
        if isinstance(other, Var):
            return CNF(Clause(self), Clause(other))
        return NotImplemented

    def __iand__(self, other):
        raise NotImplementedError()


class Clause(SimpleSequence[Var]):
    """A sequence of variables. Clauses indicate logical disjunction between
    the variables, i.e., `Clause(Var(3), Var(7))` encodes (3 ∨ 7).
    """

    @classmethod
    @property
    def _element_type(cls):
        return Var

    def __add__(self, other) -> Clause:
        if isinstance(other, Clause):
            return Clause(*self._vals, *other._vals)
        if isinstance(other, Var):
            return Clause(*self._vals, other)
        return NotImplemented

    def __radd__(self, other) -> Clause:
        if isinstance(other, Var):
            return Clause(other, *self._vals)
        return NotImplemented

    def __and__(self, other) -> CNF:
        if isinstance(other, Clause):
            return CNF(self, other)
        return NotImplemented


class CNF(SimpleSequence[Clause]):
    """A conjunction of disjunction clauses. For example:

        CNF(Clause(Var(3), Var(7)), Clause(Var(1), Var(13)))

    corresponds to the CNF formula ((3 ∨ 7) ∧ (1 ∨ 13)).
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
        if isinstance(other, CNF):
            return CNF(*self._vals, *other._vals)
        if isinstance(other, Clause):
            return CNF(*self._vals, other)
        if isinstance(other, Var):
            return CNF(*self._vals, Clause(other))
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
