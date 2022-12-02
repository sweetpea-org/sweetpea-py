"""This module provides the core data types used in SweetPea Core.

Fundamentally, SweetPea deals with Boolean logic formulas written in
*conjunctive normal form (CNF)*. `Wikipedia says
<https://en.wikipedia.org/wiki/Conjunctive_normal_form>`_:

    a formula is in **conjunctive normal form (CNF)** [...] if it is a
    conjunction of one or more clauses, where a clause is a disjunction of
    literals; otherwise put, it is a **product of sums** or **an AND of ORs**.

In SweetPea, we refer to the "literals" as :class:`Vars <.Var>`. These are
combined into :class:`Clauses <.Clause>`, which are then combined into
:class:`CNFs <.CNF>`. Most SweetPea functionality revolves around building and
manipulating :class:`CNFs <.CNF>`.
"""

# Allow type annotations to refer to not-yet-declared types.
# flake8 doesn't know about this so we have to #noqa it.
from __future__ import annotations  # noqa

import math

from itertools import chain
from typing import Iterable, List, Optional, Sequence, Tuple, Union, cast

from .binary import BinaryNumber, int_to_binary
from .simple_sequence import SimpleSequence


__all__ = ['Var', 'Clause', 'CNF']

class Var:
    """A variable for use in a CNF formula.

    This is essentially a wrapper for the builtin :class:`int` type, but with a
    few advantages:

      * It is semantically distinct from an :class:`int`, so reading code is
        more sensible.
      * Type aliases for :class:`int` can be obnoxious to deal with because you
        may want to use :class:`int`-supported operations (like addition,
        negation, etc), but these are not cross-type compatible (e.g.,
        ``Var(3) + 2`` produces an error in mypy).
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

    def __hash__(self) -> int:
        return hash(self._val)

    def __eq__(self, other) -> bool:
        if isinstance(other, Var):
            return int(self) == int(other)
        return NotImplemented

    def __lt__(self, other: Var) -> bool:
        if isinstance(other, Var):
            return int(self) < int(other)
        return NotImplemented

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

    def __abs__(self) -> Var:
        return Var(abs(int(self)))


class Clause(SimpleSequence[Var]):
    """A sequence of :class:`Vars <.Var>`. A :class:`Clause` indicates a
    logical disjunction between the contained variables. For example,
    ``Clause(Var(3), Var(7))`` encodes (3 ∨ 7).

    A :class:`Clause` can also be instantiated with a :class:`list` of
    :class:`Vars <.Var>`. This mode of instantiation will also accept raw
    :class:`ints <int>` in addition to instances of :class:`Var`. For example,
    ``Clause([1, -2, 3])`` corresponds to the formula (1 ∨ ¬2 ∨ 3).
    """

    @classmethod
    def _get_element_type(cls):
        return Var

    def __str__(self) -> str:
        return ' '.join(str(var) for var in self)

    def __add__(self, other: Union[Clause, Var]) -> Clause:
        """Logical OR. This alias exists due to the :class:`list`-like
        interface of :class:`Clauses <.Clause>`.
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
    """A conjunction of disjunction :class:`Clauses <.Clause>`. For example,
    ``CNF(Clause(Var(3), Var(7)), Clause(Var(1), Var(13)))`` corresponds to the
    CNF formula ((3 ∨ 7) ∧ (1 ∨ 13)).

    :class:`CNFs <.CNF>` can also be instantiated with a :class:`list` of
    :class:`lists <list>` of :class:`Vars <.Var>`, where each inner
    :class:`list` represents a :class:`Clause` and the outer :class:`list`
    represents the CNF formula itself. Similar to :class:`Clause`, this mode of
    instantiation will also accept raw :class:`ints <int>` in addition to
    instances of :class:`Var`. For example, ``CNF([[1, 2, -3], [-2, 7, 1]])``
    corresponds to the CNF formula ((1 ∨ 2 ∨ ¬3) ∧ (¬2 ∨ 7 ∨ 1)).
    """

    ########################################
    ##
    ## Static Methods
    ##

    ## This method is for initializing a CNF from a given number of fresh vars.
    @staticmethod
    def from_fresh(fresh: int) -> CNF:
        """Returns an empty :class:`CNF` with the given number of fresh
        :class:`Vars <.Var>` already allocated.

        .. note::

            This method probably shouldn't exist! The number of fresh variables
            should be deduced from the formulas themselves. This exists for
            legacy compatibility and should eventually be removed.
        """
        cnf = CNF()
        cnf._num_vars = fresh
        return cnf

    ## These are used for creating CNF formulas by combining two variables in a
    ## particular way.

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

        .. note::

            (a ⊙ b) is logically equivalent to (a ⇔ b), so this function
            replaces the original Haskell version's |doubleImpliesLink|_.

        .. |doubleImpliesLink| replace:: ``doubleImplies`` function
        .. _doubleImpliesLink:
            https://github.com/sweetpea-org/sweetpea-core/blob/20493dd1ffc8f5a53bd4004286e6a64298a16ce3/src/DataStructures.hs#L122-L124
        """
        if not isinstance(a, Var):
            a = Var(a)
        if not isinstance(b, Var):
            b = Var(b)
        return a % b

    @staticmethod
    def distribute(v: Var, cnf: CNF) -> CNF:
        """Distributes the given :class:`Var` across each :class:`Clause` of
        the given CNF formula, producing a new :class`CNF`.
        """
        return v ** cnf

    ########################################
    ##
    ## Class Configuration/Initialization
    ##

    @classmethod
    def _get_element_type(cls):
        return Clause

    _num_vars: int

    def __init__(self, *values):
        super().__init__(*values)
        self._num_vars = len({abs(var) for clause in self._vals for var in clause})

    ########################################
    ##
    ## String Rendering
    ##

    def __str__(self) -> str:
        return ''.join(str(clause) + ' 0\n' for clause in reversed(self._vals))

    def as_opb_string(self) -> str:
        def count_false_var(clause : Clause):
            return len(list(v for v in clause if str(v)[0] == '-'))

        return '\n'.join(' '.join(map(lambda v : '-1 v' + str(v)[1:]
                                    if str(v)[0] == '-'
                                    else '+1 v' + str(v), clause)) \
                                + ' >= ' + str(-count_false_var(clause) + 1) + ' ;'
                                for clause in reversed(self._vals))

    def as_dimacs_string(self, fresh_variable_count: Optional[int] = None) -> str:
        """Represents the :class:`CNF` as a string in the DIMACS format.

        The DIMACS format is a standardized method of representing CNF formulas
        as strings. This implementation is based on the details given `here
        <https://people.sc.fsu.edu/~jburkardt/data/cnf/cnf.html>`_.
        """
        if fresh_variable_count is None:
            fresh_variable_count = self._num_vars
        header = f"p cnf {fresh_variable_count} {len(self)}\n\n"
        return header + str(self)

    def as_unigen_string(self,
                         fresh_variable_count: Optional[int] = None,
                         support_set_length: Optional[int] = None,
                         sampled_variables: Optional[List[Var]] = None) -> str:
        """Returns a string representing the CNF formula in the modified DIMACS
        format used by Unigen.

        See :meth:`CNF.as_dimacs_string` for details about the DIMACS format.

        Unigen adds an extra line at the top that describes the list of
        variables you would like to sample (instead of sampling among all
        variables). This line is given in the form::

            c ind v1 v2 ... vn 0

        where ``v1``, ``v2``, ..., ``vn`` represent variables in the formula.
        This line is placed just below the "problem" line (the line beginning
        with ``p``).
        """
        if support_set_length is not None and sampled_variables is not None:
            raise ValueError("cannot give both a support set length and sampled variables list to as_unigen_string!")
        elif support_set_length is not None:
            support_set = [Var(n) for n in range(1, support_set_length + 1)]
        elif sampled_variables is not None:
            support_set = sampled_variables
        else:
            support_set = []

        # This fun list comprehension divides the list of variables in the
        # support set into separate lists of no more than ten variables each,
        # due to restrictions in the file format.
        support_chunks = [[n for n in support_set[idx:idx + 10]] for idx in range(0, len(support_set), 10)]
        support_string = '\n'.join("c ind " + ' '.join(map(str, chunk)) + " 0"
                                   for chunk in support_chunks)

        # Now we modify the base DIMACS string by inserting the Unigen
        # modifications after the "problem" line. We know the problem line is
        # the first line, so we just do a simple substitution on the first
        # newline character in the string.
        dimacs_string = self.as_dimacs_string(fresh_variable_count)
        unigen_string = dimacs_string.replace('\n', '\n' + support_string, 1)

        # Done!
        return unigen_string

    def as_list_of_list_of_ints(self) -> List[List[int]]:
        """Converts the :class:`CNF` to a :class:`list` of
        :class:`lists <list>` of :class:`ints <int>`.
        """
        return [[int(var) for var in clause] for clause in self]

    def as_haskell_cnf(self) -> Tuple[int, List[List[int]]]:
        """Converts the :class:`CNF` to a :class:`tuple` whose first element is
        the number of fresh variables in the formula and whose second element
        is the :class:`CNF` represented as a :class:`list` of
        :class:`lists <list>` of :class:`ints <int>`.

        .. note::

            This is the way CNF formulas were encoded in the original Haskell
            code. It only exists for consistency checks across the two code
            bases.
        """
        return (self._num_vars, self.as_list_of_list_of_ints())

    ########################################
    ##
    ## Operator Overloads
    ##

    # CNF + ___
    def __add__(self, other: Union[CNF, Clause, Var]) -> CNF:
        """Logical OR. This alias exists due to the :class:`list`-like
        interface of :class:`CNFs <.CNF>`.
        """
        if isinstance(other, CNF):
            return CNF(*self, *other)
        if isinstance(other, Clause):
            return CNF(*self, other)
        if isinstance(other, Var):
            return CNF(*self, [other])
        return NotImplemented

    # CNF += ___
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
        return NotImplemented

    # CNF & ___
    def __and__(self, other: Union[Clause, Var]) -> CNF:
        """Logical AND."""
        if isinstance(other, Clause):
            return CNF(self._vals + [other])
        return CNF(self._vals + [Clause(other)])

    # ___ & CNF
    def __rand__(self, other: Union[Clause, Var]) -> CNF:
        if isinstance(other, Clause):
            return CNF([other] + self._vals)
        return CNF([Clause(other)] + self._vals)

    # CNF | ___
    def __or__(self, other: Var) -> CNF:
        """Logical OR."""
        return CNF([*self[:-1], self[-1] + other])

    # ___ | CNF
    def __ror__(self, other: Var) -> CNF:
        return CNF([other + self[0], *self[1:]])

    # CNF ** ___
    def __pow__(self, other: Var) -> CNF:
        """Distribution of a :class:`Var` across the :class:`Clauses <.Clause>`
        of a :class:`CNF`.
        """
        if isinstance(other, Var):
            return CNF([clause | other for clause in self])
        return NotImplemented

    # ___ ** CNF
    def __rpow__(self, other: Var) -> CNF:
        if isinstance(other, Var):
            return CNF([other | clause for clause in self])
        return NotImplemented

    ########################################
    ##
    ## Variable Manipulation Functions
    ##

    def get_fresh(self) -> Var:
        """Creates a new :class:`Var` for the formula."""
        # NOTE: I think this is a weird interface. A new variable is generated,
        #       permanently affecting this CNF formula... but there's no
        #       guarantee that the caller actually incorporates that variable
        #       into the formula.
        self._num_vars += 1
        return Var(self._num_vars)

    def get_n_fresh(self, n: int) -> List[Var]:
        """Creates the next *n* :class:`Vars <.Var>`, numbered sequentially."""
        return [self.get_fresh() for _ in range(n)]

    def append(self, other: Union[CNF, Clause, Iterable[Clause], Var]):
        """Appends a :class:`CNF` to this :class:`CNF`."""
        self += other

    def prepend(self, other: Union[CNF, Clause, Iterable[Clause], Var]):
        """Prepends a :class:`CNF` to this :class:`CNF`."""
        if isinstance(other, Var):
            self._vals.append(Clause(other))
        elif isinstance(other, Clause):
            self._vals.append(other)
        elif isinstance(other, CNF):
            self._vals.extend(other._vals)
        else:
            raise NotImplementedError()

    def set_to_zero(self, variable: Var):
        """Zeroes the specified :class:`Var` by appending its negation to the
        existing CNF formula.
        """
        self.prepend(~variable)

    def zero_out(self, in_list: Iterable[Var]):
        """Appends a CNF formula negating the existing CNF formula."""
        zeroed_cnf = CNF([[~var] for var in in_list])
        self.prepend(zeroed_cnf)

    def set_to_one(self, variable: Var):
        """Sets the specified variable to ``1`` by appending it to the existing
        CNF formula.
        """
        self.prepend(variable)

    ########################################
    ##
    ## CNF Assertions
    ##

    def assert_k_of_n(self, k: int, in_list: Sequence[Var]):
        # TODO DOC
        # TODO: Describe this function's purpose.
        in_binary =  int_to_binary(k)
        sum_bits = self.pop_count(in_list, len(in_binary)+1)
        # Add zero padding to the left.
        in_binary.reverse()
        left_padded: BinaryNumber = in_binary[:len(sum_bits)]
        left_padded += [-1 for _ in range(len(sum_bits) - len(left_padded))]
        left_padded.reverse()
        # Form the assertion.
        assertion = [Var(lp * sb.value) for (lp, sb) in zip(left_padded, sum_bits)]
        # Append the assertion to the formula.
        self.prepend(CNF([Clause(x) for x in assertion]))

    def assert_k_less_than_n(self, k: int, in_list: Sequence[Var]):
        # TODO DOC
        self._inequality_assertion(True, k, in_list)

    def assert_k_greater_than_n(self, k: int, in_list: Sequence[Var]):
        # TODO DOC
        self._inequality_assertion(False, k, in_list)

    def _inequality_assertion(self, assert_less_than: bool, k: int, in_list: Sequence[Var]):
        in_binary = int_to_binary(k)
        sum_bits = self.pop_count(in_list, len(in_binary)+1)
        k_vars = self.get_n_fresh(len(in_binary))
        assertion = [Var(kv.value * b) for (kv, b) in zip(k_vars, in_binary)]
        self.prepend(CNF([Clause(x) for x in assertion]))
        self._make_same_length(k_vars, sum_bits)
        if assert_less_than:
            kbs, nbs = sum_bits, k_vars
        else:
            kbs, nbs = k_vars, sum_bits
        neg_twos_comp_nbs = self._convert_to_negative_twos_complement(nbs)
        (_, ss) = self.ripple_carry(kbs, neg_twos_comp_nbs)
        self.set_to_one(ss[-1])

    def _make_same_length(self, xs: List[Var], ys: List[Var]):
        if len(xs) == len(ys):
            return
        elif len(xs) < len(ys):
            zero_padding = self.get_n_fresh(len(ys) - len(xs) + 1)
            self.zero_out(zero_padding)
            xs[:0] = zero_padding
            one_more_zero = self.get_n_fresh(1)
            self.zero_out(one_more_zero)
            ys[:0] = one_more_zero
        else:
            self._make_same_length(ys, xs)

    def _convert_to_negative_twos_complement(self, bits: List[Var]) -> List[Var]:
        # Flip the bits, i.e., assert flipped_bits[i] ⇔ bits[i].
        flipped_bits = self.get_n_fresh(len(bits))
        flipped_cnf = CNF()
        for lhs, rhs in zip(flipped_bits, (~b for b in bits)):
            double_implied = CNF.xnor_vars(lhs, rhs)
            flipped_cnf += double_implied
        self.prepend(flipped_cnf)
        # Make a zero-padded one (for the addition) of the correct dimension.
        one_vars = self.get_n_fresh(len(bits))
        # Set all the top bits to 0 and the bottom bit to 1.
        self.zero_out(one_vars[:-1])
        self.set_to_one(one_vars[-1])
        # Add the lists.
        (_, ss) = self.ripple_carry(flipped_bits, one_vars)
        ss.reverse()
        return ss

    ########################################
    ##
    ## Pop Count
    ##

    def pop_count(self, in_list: Sequence[Var], saturate_at: int) -> List[Var]:
        """Returns the list of :class:`Vars <.Var>` that represents the bits of
        the given list variable in binary.
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
        return self._pop_count_layer([[x] for x in chain(in_list, aux_list)], saturate_at)

    def _pop_count_layer(self, bit_list: List[List[Var]], saturate_at: int) -> List[Var]:
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
            if saturate_at == 0:
                (max_c, ss) = self.ripple_carry(l, r)
                var_list.append([max_c] + list(reversed(ss)))
            else:
                var_list.append(self.ripple_saturate(l, r, saturate_at))
        # Reverse the list because of append ordering.
        var_list.reverse()
        return self._pop_count_layer(var_list, saturate_at)

    ########################################
    ##
    ## Adders
    ##

    def half_adder(self, a: Var, b: Var) -> Tuple[Var, Var]:
        # TODO DOC
        c = self.get_fresh()
        s = self.get_fresh()

        c_val = CNF.and_vars(a, b)
        c_neg_val = CNF.or_vars(~a, ~b)
        c_implies_c_val = CNF.distribute(~c, c_val)
        c_val_implies_c = CNF.distribute(c, c_neg_val)
        computed_c = c_implies_c_val + c_val_implies_c
        self.prepend(computed_c)

        s_val = CNF.xor_vars(a, b)
        s_neg_val = CNF.xnor_vars(a, b)
        s_implies_s_val = CNF.distribute(~s, s_val)
        s_val_implies_s = CNF.distribute(s, s_neg_val)
        computed_s = s_implies_s_val + s_val_implies_s
        self.prepend(computed_s)

        return (c, s)

    def full_adder(self, a: Var, b: Var, cin: Optional[Var]) -> Tuple[Var, Var]:
        # TODO DOC

        if not cin:
            return self.half_adder(a, b)
        
        cout = self.get_fresh()
        s = self.get_fresh()

        c_val     = (a | b) & (a | cin) & (b | cin)
        c_neg_val = (~a | ~b) & (~a | ~cin) & (~b | ~cin)
        c_implies_c_val = CNF.distribute(~cout, c_val)
        c_val_implies_c = CNF.distribute(cout, c_neg_val)
        computed_c = c_implies_c_val + c_val_implies_c
        self.prepend(computed_c)

        s_val     = (~a | ~b | cin) & (~a | b | ~cin) & (a | ~b | ~cin) & (a | b | cin)
        s_neg_val = (~a | ~b | ~cin) & (~a | b | cin) & (a | ~b | cin) & (a | b | ~cin)
        s_implies_s_val = CNF.distribute(~s, s_val)
        s_val_implies_s = CNF.distribute(s, s_neg_val)
        computed_s = s_implies_s_val + s_val_implies_s
        self.prepend(computed_s)

        return (cout, s)

    def saturate_adder(self, a: Var, b: Var, cin: Optional[Var]) -> Var:
        # TODO DOC
        s = self.get_fresh()

        if (cin):
            s_val     = CNF(a | b | cin)
            s_neg_val = (~a & ~b & ~cin)
        else:
            s_val     = CNF(a | b)
            s_neg_val = (~a & ~b)
        s_implies_s_val = CNF.distribute(~s, s_val)
        s_val_implies_s = CNF.distribute(s, s_neg_val)
        computed_s = s_implies_s_val + s_val_implies_s
        self.prepend(computed_s)

        return s

    def ripple_carry(self, xs: List[Var], ys: List[Var]) -> Tuple[Var, List[Var]]:
        # TODO DOC
        cin = None

        s_accum: List[Var] = []

        for x, y in zip(reversed(xs), reversed(ys)):
            (c, s) = self.full_adder(x, y, cin)
            s_accum.append(s)
            cin = c

        return (cast(Var, cin), s_accum)

    def ripple_saturate(self, xs: List[Var], ys: List[Var], saturate_at: int) -> List[Var]:
        # Assuming xs and ys have no more than `saturate_at` variables,
        # generate a saturating sum with no more than `saturate_at` variables
        cin = None

        s_accum: List[Var] = []

        for i, (x, y) in enumerate(zip(reversed(xs), reversed(ys))):
            if i+1 == saturate_at:
                s = self.saturate_adder(x, y, cin)
                s_accum.append(s)
            else:
                (c, s) = self.full_adder(x, y, cin)
                s_accum.append(s)
                cin = c

        if len(xs) < saturate_at:
            s_accum.append(cast(Var, cin))

        s_accum.reverse()
        return s_accum
