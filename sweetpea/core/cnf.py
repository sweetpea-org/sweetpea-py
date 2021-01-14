"""Provides simple type aliases used in SweetPea Core."""

# Allow type annotations to refer to not-yet-declared types.
from __future__ import annotations

from typing import Any, List, NewType


__all__ = ['Count', 'Var', 'Clause', 'CNF']


Count = NewType('Count', int)


def IncompatibleTypesError(op_name: str, lhs: Any, rhs: Any) -> TypeError:  # pylint: disable=invalid-name
    """A formatted `TypeError` for unsupported operator application."""
    return TypeError(f"unsupported operand type(s) for {op_name}: "
                     f"'{type(lhs).__name__}' and '{type(rhs).__name__}'")


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
        self._val = value

    def __repr__(self) -> str:
        return f"Var({self._val})"

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
        raise IncompatibleTypesError('+', self, other)

    def __radd__(self, other) -> Var:
        if isinstance(other, int):
            return Var(other + int(self))
        raise IncompatibleTypesError('+', other, self)

    def __sub__(self, other) -> Var:
        if isinstance(other, Var):
            return Var(int(self) - int(other))
        if isinstance(other, int):
            return Var(int(self) - other)
        raise IncompatibleTypesError('-', self, other)

    def __rsub__(self, other) -> Var:
        if isinstance(other, int):
            return Var(other - int(self))
        raise IncompatibleTypesError('-', other, self)


Clause = List[Var]
CNF = List[Clause]


def and_vars(a: Var, b: Var) -> CNF:  # pylint: disable=invalid-name
    """Returns a CNF formula encoding (a ∨ b).

    NOTE: The original version of this function in the Haskell code was named
          `andCNF`. It took a clause (list of variables) as argument, and
          simply returned that clause embedded in another list. In all cases,
          the function was invoked with a list of two variables.
              The name seems strange to me, because the variables themselves
          are combined with ∨ to build a single clause. We might change this
          name in the future to, e.g., `or_vars` for semantic consistency.
    """
    return [[a, b]]


def xor_vars(a: Var, b: Var) -> CNF:  # pylint: disable=invalid-name
    """Returns a CNF formula encoding (a ⊕ b) as ((a ∨ b) ∧ (¬a ∨ ¬b))."""
    return [[a, b], [~a, ~b]]


def xnor_vars(a: Var, b: Var) -> CNF:  # pylint: disable=invalid-name
    """Returns a CNF formula encoding (a ⊙ b) as ((a ∨ ¬b) ∧ (¬a ∨ b))."""
    return [[a, ~b], [~a, b]]


def distribute(x: Var, cnf: CNF) -> CNF:  # pylint: disable=invalid-name
    """Distributes a given variable `x` across every clause in the given CNF
    formula by replacing each `clause` with (`x` ∨ `clause`).
    """
    return [[x] + clause for clause in cnf]
