import math
import operator

from typing import cast, List, Tuple

from .data_structures import (
    Count, Var, CountState,
    empty_state, init_state, get_fresh, get_n_fresh, append_CNF, zero_out, set_to_one, set_to_zero,
    double_implies,
    and_CNF, n_and_CNF, xor_CNF, xnor_CNF, distribute)
from .haskell.data.list import concat, zip_with


__all__ = [
    'assert_k_of_n', 'k_less_than_n', 'k_greater_than_n', 'make_same_length',
    'half_adder', 'full_adder', 'ripple_carry', 'pop_count',
    'to_binary', 'to_neg_twos_comp',
    # Re-export from data_structures:
    'empty_state', 'init_state'
]


########################################
##
## High-Level Functions (Assert ==, <, >)
##

def assert_k_of_n(k: int, in_list: List[Var], state: CountState):
    sum_bits = pop_count(in_list, state)
    in_binary = to_binary(k)
    in_binary.reverse()
    left_padded = in_binary[:len(sum_bits)] + ([-1] * (len(sum_bits) - len(in_binary)))
    left_padded.reverse()
    assertion = zip_with(operator.mul, left_padded, sum_bits)
    append_CNF([[x] for x in assertion], state)


def k_less_than_n(k: int, in_list: List[Var], state: CountState):
    inequality(True, k, in_list, state)


def k_greater_than_n(k: int, in_list: List[Var], state: CountState):
    inequality(False, k, in_list, state)


########################################
##
## High-Level Function Helpers
##

def to_binary(value: int) -> List[int]:
    """
    Converts an integer value to binary where the output representation is a
    list of binary digits of the alphabet {-1, 1} (i.e., similar to a
    traditional binary representation except the "false" value is -1 instead of
    0).

    For example:

        2  => [1, -1]
        11 => [1, -1, 1, 1]

    :param value: The integer value to convert to binary.
    :type value: int
    :return: A binary representation of the input value.
    :rtype: list[int]
    """
    accumulator: List[int] = []
    while value != 0:
        if value & 1:
            accumulator.append(-1)
        else:
            accumulator.append(1)
        value = value // 2
    accumulator.reverse()
    return accumulator


def inequality(is_less_than: bool, k: int, in_list: List[Var], state: CountState):
    pop_count_sum = pop_count(in_list, state)
    k_binary = to_binary(k)
    k_vars = cast(List[Var], get_n_fresh(len(k_binary), state))
    append_CNF(zip_with(operator.mul, k_vars, k_binary), state)

    (k_vars_, pop_count_sum_) = make_same_length(k_vars, pop_count_sum, state)

    if is_less_than:
        assert_less_than(pop_count_sum_, k_vars_, state)
    else:
        assert_less_than(k_vars_, pop_count_sum_, state)


def make_same_length(xs: List[Var], ys: List[Var], state: CountState) -> Tuple[List[Var], List[Var]]:
    if len(xs) < len(ys):
        # Extend the bit-width by one to safely negate two's complement.
        zero_padding = cast(List[Var], get_n_fresh(len(ys) - len(xs) + 1, state))
        zero_out(zero_padding, state)
        xs_ = zero_padding + xs
        one_more_zero = cast(List[Var], get_n_fresh(1, state))
        zero_out(one_more_zero, state)
        ys_ = one_more_zero + ys
        return (xs_, ys_)
    else:
        zero_padding = cast(List[Var], get_n_fresh(len(xs) - len(ys) + 1, state))
        zero_out(zero_padding, state)
        ys_ = zero_padding + ys
        one_more_zero = cast(List[Var], get_n_fresh(1, state))
        zero_out(one_more_zero, state)
        xs_ = one_more_zero + xs
        return (xs_, ys_)


def assert_less_than(k: List[Var], n: List[Var], state: CountState):
    neg_twos_comp_n = cast(List[Var], to_neg_twos_comp(cast(List[int], n), state))
    (cs, ss) = ripple_carry(k, neg_twos_comp_n, state)
    set_to_one(ss[-1], state)


def to_neg_twos_comp(in_list: List[int], state: CountState) -> List[int]:
    """
    Computes the negative two's complement of a number. The number is
    represented as a list of binary digits. The algorithm used is:

        - https://courses.cs.vt.edu/csonline/NumberSystems/Lessons/SubtractionWithTwosComplement/index.html

    :param in_list: A list of binary digits representing a number.
    :type in_list: list[int]
    :param state: The current state.
    :type state: CountState
    :return: The negative two's complement of the input number as a list of
             binary digits.
    :rtype: list[int]
    """
    flipped_bits_vars = cast(List[Var], get_n_fresh(len(in_list), state))
    # Flip the bits, i.e., assert flipped_bits_vars[i] iff ~in_list[i].
    append_CNF(concat(zip_with(double_implies, flipped_bits_vars, [Var(-x) for x in in_list])), state)
    # Make a zero-padded one (for the addition) of the correct dimensions.
    one_vars = cast(List[Var], get_n_fresh(len(in_list), state))
    # Set all the top bits to 0 and the bottom bit to 1.
    zero_out(one_vars[:-1], state)
    set_to_one(one_vars[-1], state)
    # Add the lists.
    (_, ss) = ripple_carry(flipped_bits_vars, one_vars, state)
    ss.reverse()
    return cast(List[int], ss)


########################################
##
## Adders
##


def half_adder(a: Var, b: Var, state: CountState) -> Tuple[Var, Var]:
    c = Var(get_fresh(state))
    s = Var(get_fresh(state))

    c_val = and_CNF([a, b])
    c_neg_val = n_and_CNF(a, b)
    c_implies_c_val = distribute(Var(-c), c_val)
    c_val_implies_c = distribute(Var(c), c_neg_val)
    computed_c = c_implies_c_val + c_val_implies_c
    append_CNF(computed_c, state)

    s_val = xor_CNF(a, b)
    s_neg_val = xnor_CNF(a, b)
    s_implies_s_val = distribute(Var(-s), s_val)
    s_val_implies_s = distribute(Var(s), s_neg_val)
    computed_s = s_implies_s_val + s_val_implies_s
    append_CNF(computed_s, state)

    return (c, s)


def full_adder(a: Var, b: Var, cin: Var, state: CountState) -> Tuple[Var, Var]:
    cout = Var(get_fresh(state))
    s = Var(get_fresh(state))

    c_val = [[a, b], [a, cin], [b, cin]]
    c_neg_val = [[-a, -b], [-a, -cin], [-b, -cin]]
    c_implies_c_val = distribute(Var(-cout), c_val)
    c_val_implies_c = distribute(Var(cout), cast(List[List[Var]], c_neg_val))
    computed_c = c_implies_c_val + c_val_implies_c
    append_CNF(computed_c, state)

    s_val = [[-a, -b, cin], [-a, b, -cin], [a, -b, -cin], [a, b, cin]]
    s_neg_val = [[-a, -b, -cin], [-a, b, cin], [a, -b, cin], [a, b, -cin]]
    s_implies_s_val = distribute(Var(-s), cast(List[List[Var]], s_val))
    s_val_implies_s = distribute(Var(s), cast(List[List[Var]], s_neg_val))
    computed_s = s_implies_s_val + s_val_implies_s
    append_CNF(computed_s, state)

    return (cout, s)


def ripple_carry(xs: List[Var], ys: List[Var], state: CountState) -> Tuple[List[Var], List[Var]]:
    cin = get_fresh(state)
    set_to_zero(Var(cin), state)

    c_accum: List[Var] = []
    s_accum: List[Var] = []

    for x, y in zip(reversed(xs), reversed(ys)):
        (c, s) = full_adder(x, y, Var(cin), state)
        c_accum.append(c)
        s_accum.append(s)
        cin = Count(c)

    return (c_accum, s_accum)


def pop_count(in_list: List[Var], state: CountState) -> List[Var]:
    if len(in_list) == 0:
        raise RuntimeError("Why did you call pop_count with an empty list?")
    nearest_largest_pow = math.ceil(math.log(len(in_list), 2))
    aux_list = get_n_fresh(2 ** nearest_largest_pow - len(in_list), state)
    zero_out(cast(List[Var], aux_list), state)
    return pop_count_layer([[x] for x in in_list + cast(List[Var], aux_list)], state)


def pop_count_layer(bit_list: List[List[Var]], state: CountState) -> List[Var]:
    if len(bit_list) == 0:
        raise RuntimeError("Why did you call pop_count_layer with an empty list?")
    elif len(bit_list) == 1:
        return bit_list[0]
    else:
        half_way = len(bit_list) // 2
        first_half = bit_list[:half_way]
        second_half = bit_list[half_way:]
        var_list = pop_count_compute(first_half, second_half, state)
        return pop_count_layer(var_list, state)


def pop_count_compute(xs: List[List[Var]], ys: List[List[Var]], state: CountState) -> List[List[Var]]:
    index = 0
    accum: List[List[Var]] = []

    while index < len(xs) and index < len(ys):
        x = xs[index]
        y = ys[index]
        (cs, ss) = ripple_carry(x, y, state)
        formatted_result = format_sum(cs, ss)
        accum.append(formatted_result)
        index += 1

    return accum


def format_sum(cs: List[Var], ss: List[Var]) -> List[Var]:
    max_c = max(cs)
    return [max_c] + list(reversed(ss))
