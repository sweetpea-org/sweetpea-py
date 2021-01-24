"""Provides simple type aliases used in SweetPea Core."""

# Allow type annotations to refer to not-yet-declared types.
from __future__ import annotations

import math

from itertools import chain
from typing import Iterable, Iterator, List, Sequence, Union

from .binary import BinaryNumber, binary
from .simple_sequence import SimpleSequence


__all__ = ['Var', 'Clause', 'CNF']


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

    @property
    def value(self) -> int:
        """The integer value of this variable."""
        return self._val

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
            return self
        if hasattr(other, '__next__'):
            for item in other:
                self._vals += item
            return self
        return NotImplemented

    def __and__(self, other: Var) -> CNF:
        """Logical AND."""
        return CNF(self._vals + [Clause(other)])

    def __rand__(self, other: Var) -> CNF:
        return CNF([Clause(other)] + self._vals)

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
        """Returns a CNF formula encoding (a ⊙ b) as ((a ∨ ¬b) ∧ (¬a ∨ b)).

        NOTE: (a ⊙ b) is logically equivalent to (a ⇔ b).
        """
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return a % b

    def get_fresh(self) -> Var:
        """Creates a new variable for the formula."""
        # NOTE: I think this is a weird interface. A new variable is generated,
        #       permanently affecting this CNF formula... but there's no
        #       guarantee that the caller actually incorporates that variable
        #       into the formula.
        self._num_vars += 1
        return Var(self._num_vars)

    def get_n_fresh(self, n: int) -> Iterator[Var]:
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

    def assert_k_of_n(self, k: int, in_list: Sequence[Var]):
        # TODO: Describe this function's purpose.
        sum_bits = self.pop_count(in_list)
        # Add zero padding to the left.
        in_binary = binary(k)
        in_binary.reverse()
        left_padded: BinaryNumber = in_binary[:len(sum_bits)]
        left_padded += [-1 for _ in range(len(left_padded) - len(sum_bits))]
        left_padded.reverse()
        # Form the assertion.
        assertion = [Var(lp * sb.value) for (lp, sb) in zip(left_padded, sum_bits)]
        # Append the assertion to the formula.
        self.append(Clause(x) for x in assertion)

    def pop_count(self, in_list: Sequence[Var]) -> List[Var]:
        """Returns the list that represents the bits of the `sum` variable in
        binary.
        """
        if not in_list:
            raise ValueError("cannot take pop count of empty list")
        # Our pop count algorithm assumes the input is a binary number with a
        # power-of-two number of digits. So first, we find out what the next
        # power of two is for our number (which may be just the length of that
        # number).
        nearest_largest_power = math.ceil(math.log(len(in_list), 2))
        # Then we generate a sequence of fresh variables (new digits) equal to
        # the difference and set them all to 0.
        aux_list = self.get_n_fresh((2 ** nearest_largest_power) - len(in_list))
        self.zero_out(aux_list)
        # Now we can start computing the actual pop count.
        return self._pop_count_layer([[x] for x in chain(in_list, aux_list)])

    def _pop_count_layer(self, bit_list: List[List[Var]]) -> List[Var]:
        if len(bit_list) == 1:
            return bit_list[0]
        midpoint = len(bit_list) // 2
        left_half = bit_list[:midpoint]
        right_half = bit_list[midpoint:]
        var_list: List[List[Var]] = []
        # This zip assumes the two lists are of equal length. This is a safe
        # assumption since we've guaranteed the input to have a length that's a
        # power of two greater than one.
        for (l, r) in zip(left_half, right_half):
            (cs, ss) = self.ripple_carry(l, r)
            max_c = max(cs)
            var_list.append([max_c] + list(reversed(ss)))
        # Reverse the list because of append ordering.
        var_list.reverse()
        return self._pop_count_layer(var_list)
