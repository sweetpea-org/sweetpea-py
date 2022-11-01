"""This module provides combinatoric functionality."""


from typing import List, Tuple, Dict, Any, Union, Optional, cast
from math import factorial
from functools import reduce


def extract_components(sizes: List[int], n: int) -> List[int]:
    """Given a list of dimension sizes, and an integer less than the product of
    the sizes, this function will extract the component value for each
    dimension from the total.

    For example, if ``sizes`` is ``[3, 4, 2]``, there are 24 possible
    combinations of the three. If ``0 <= n < 24``, this function will return
    the selections for each dimension for that ``n``.
    """
    components = []
    for s in sizes:
        components.append(n % s)
        n //= s

    return components

##############################################################
# Finding combinations by index
#
# This is the simplest case: you want the `j`th unique combination of
# choices for `l` items, where each item has `n` possibilities. There
# are `pow(l, n)` such combinations, and we can treat the index as
# as base-n number.

def compute_jth_combination(l, n, j):
    """In a sequence of ``l`` items, where there are ``n`` choices for each
    item, this will compute the ``jth`` combination, out of all :math:`n^l`
    possibilities.
    """
    combination = [None] * l
    for k in range(l - 1, -1, -1):
        combination[k] = j % n
        j //= n

    return combination

##############################################################
# Finding combinations without replacement by index
#
# Treats the index as a number in the "combinatorial number system".

def compute_jth_combination_without_replacement(n, m, j) -> List[int]:
    """In a set of ``m`` items, where there are ``n`` choices for each
    item, this will compute the ``jth`` combination, out of all n-choose-m`
    possibilities.
    """
    combination = []
    while m > 0:
        c = m-1
        f_m = factorial(m)
        while c+1 < n and n_choose_m_given_m_factorial(c+1, m, f_m) <= j:
            c += 1
        j -= n_choose_m_given_m_factorial(c, m, f_m)
        combination.append(c)
        m -= 1

    return combination

def n_choose_m_given_m_factorial(n: int, m: int, f_m: int):
    if n < m:
        return 0
    if n == m:
        return 1
    p = 1
    h = n - m
    while n > h:
        p *= n
        n -= 1
    return p // f_m

def n_choose_m(n: int, m: int):
    return n_choose_m_given_m_factorial(n, m, factorial(m))

##############################################################
# Finding unique prefixes of permutations
#
# For permutations, the simple case is that you want the `j`th
# permutation of `n` elements, of which there are `factorial(n)`
# permutations.
#
# A case that's only slightly more complex: you want the `j`th
# distinct prefix of `m` elements in a `n`-element permutation. That's
# handled here, and it works due to the non-standard way we use the
# "inversion sequence" (so, it's not really an inversion sequence
# anymore, but it's closely related).

def compute_jth_permutation_prefix(n, m, j):
    """Compute the ``j``th prefix of ``m`` elements of a permutation of ``n`` elements.
    The ``j`` index is in terms of possible prefixes, not possible permutations."""
    inversion_sequence = compute_jth_inversion_sequence(n, m, j)
    return construct_permutation(inversion_sequence, n)

def compute_jth_inversion_sequence(n, m, j):
    """The are ``n!`` permutations of ``n`` elements. Each permutation can be
    uniquely identified by and constructed from its "inversion sequence". This
    function will compute the ``j``th inversion sequence for a set of ``n``
    elements.

    To deal with permutation prefixes, our ``j`` selects only the
    first m of n possible values. Also, we're going to change the
    usual meaning of an inversion sequence, using the values that we
    peel off (to construct a permutation) to mean how many unused
    numbers we skip over, because we want a prefix of the sequence to
    be able to represent any permutation prefix.

    Information on inversion sequences can be found:

    - `MathOnline <http://mathonline.wikidot.com/the-inversion-sequence-of-a-permutation>`__
    - "Introductory Combinatorics" by Richard A. Brualdi, ISBN 978-0136020400.

    """
    inversion = []
    for k in range(n, n-m, -1):
        result = j % k
        inversion.append(result)
        j //= k

    return inversion

def construct_permutation(inversion_sequence: List[int], orig_n: int) -> List[int]:
    """Given an inversion sequence, construct the permutation."""
    used = [False for i in range(orig_n)]
    permutation = [-1 for i in inversion_sequence]
    for n, skip in enumerate(inversion_sequence):
        idx = 0
        while used[idx]:
            idx += 1
        while skip > 0:
            if not used[idx]:
                skip -= 1
            idx += 1
        while used[idx]:
            idx += 1
        permutation[n] = idx
        used[idx] = True

    return permutation

##############################################################
# Finding permutations with repetitions
#
# How many permutations of `n` elements are there when each of the `n`
# elements is repeated exactly `m` times? It's straightforward to
# count those when we want the whole `n*m` sequence (see
# `count_permutation_with_copies`). Enumerating them is somewhat more
# challenging, but it's bascially a search built on counting.
# We build on this furrher below to find prefixes of such sequencs.
#
# The implementation below is based on
#   https://math.stackexchange.com/questions/3802978/permutation-with-repetition-index-conversion
#   https://stackoverflow.com/questions/24506460/algorithm-for-finding-multiset-permutation-given-lexicographic-index
#
# Initially, we're given:
#
#   q = noncomplex factor crossing
#
#   m = complex factor crossing size
#       [generalized to counter buckets when noncomplex factors are weighted]
#
# We have m copies of q combinations, where each copy is
# indistinguishable. The number of distinct permutations is not
# (q*m)!, because that would treat the copies as distinguishable. That
# is, for each of q combinations, (q*m)! includes m! cases that should
# be the same per combination, so overall it's K = (q*m)!/(m! ^ q)
# combinations.
#
# More generally, as implemented here, we can assign each of the q
# elements a number of copies c[i] (for i in 0 to q-1), and then there
# are
#
#  (c[0] + ... c[q-1])! / c[0]! * ... c[q-1]!
#
# permutations. To generate a permutation given an index from 0 to
# K-1, start with a counter array c initialized to m (or, more generally,
# a counter array is given):
#
#  - Pick the first non-empty counter and decrement it. Count
#    how many solutions would continue:
#
#    * If the index is less then that, you've found the first element
#      of the permutation; recur for the rest.
#
#   * If the index is more than that, reincrement the counter,
#     decrement the index by the number of solutions being skipped,
#     and try the next non-empty counter.
#
def _construct_permutation_with_copies(idx: int, q: int, fill_n: int, counters: List[int]) -> List[int]:
    sequence = cast(List[int], [])

    # assert sum(counters) == fill_n

    while len(sequence) < fill_n:
        i = 0
        while i < q:
            if counters[i] > 0:
                counters[i] -= 1
                n = count_remaining_permutations(counters)
                if idx >= n:
                    idx -= n
                    counters[i] += 1
                else:
                    sequence.append(i)
                    break
                i += 1
            else:
                i += 1
        assert i < q

    return sequence

def construct_permutation_with_copies(idx: int, q: int, m: int) -> List[int]:
    counters = [m for i in range(q)]
    return _construct_permutation_with_copies(idx, q, q*m, counters)

def construct_permutation_with_varying_copies(idx: int, q: int, counters: List[int]) -> List[int]:
    counters = counters[:]
    return _construct_permutation_with_copies(idx, q, sum(counters), counters)

def count_remaining_permutations(counters: List[int]) -> int:
    d = 1
    for c in counters:
        if c > 1:
            d = d * factorial(c)
    return factorial(sum(counters)) // d

def count_permutations_with_copies(q: int, m: int, first_n: int) -> int:
    n = q * m;
    if n == first_n:
        return factorial(n) // pow(factorial(m), q)
    else:
        # We want only the first_n of the trials, so count permutations
        # that only use the different ways of having first_n distributed
        # among the q possibilities.
        return cast(int, count_prefixes_of_permutations_with_copies(q, m, first_n, PermutationMemo()))

def count_permutations_with_varying_copies(q: int, counters: List[int], first_n: int) -> int:
    return cast(int, count_prefixes_of_permutations_with_copies(q, counters, first_n, PermutationMemo()))

##############################################################
# Finding unique prefixes of permutations with repetitions
#
# This is the general case. For a prefix of size `first_n` out of `q`
# elements repeated `m` times, just counting can be complex. One
# simple case is when `first_n` is no more than `m`; in that case,
# it's just a base-`q` number of `first_n` digits: `pow(q, first_n)`.
# Otherwise, the number of permutations depends on how you distribute
# `first_n` slots among the `q` choices, since using slots of one
# choice will reduce the number of distinct permutations. We use a
# dynamic-programming algorithm to count. The overall strategy is to
# try every allocation of `first_n` items to the `q` choices, and
# count the number of permutations of those `first_n` items (using the
# counter above, since we've reduced away the problem of prefixes).
#
# We start with a simple recursive algorithm, but that can easily blow
# the stack (thanks, Python!), so we also have one where we manage the
# continuation with our own stack. It's not much slower, but if the
# recursion wil be limited, we use the direct one, and otherwise we
# use the continuation one.
#
# We use the same algorithm to find the permutation at a given index,
# but always using the continuation one, so that we don't have to use
# a non-local escape in Python (although I guess an exception would
# work), but also so we don't have to implement that twice. If the
# memo table would cause us to skip over the item we want in the
# search, then we don't use it, which means that we navigate to the
# relevant choice of `first_n` items. We have to pass a multiplier
# down to that leaf, so it knows how many permutations total this leaf
# would account for; we keep that multiplier out of the memo table,
# because it would reduce sharing fatally.

class PermutationMemo():
    def __init__(self):
        self.memo = {}

def count_prefixes_of_permutations_with_copies(q: int, m_or_counters: Union[int, List[int]], first_n: int,
                                               pmemo: PermutationMemo) -> int:
    if isinstance(m_or_counters, list):
        return cast(int, k_prefixes_of_permutations_with_copies(q, m_or_counters, first_n, -1, pmemo))
    m = m_or_counters
    if first_n <= m:
        # Other techniques should produce the same result
        return pow(q, first_n)
    elif first_n < 100 and q < 100:
        return recur_count_prefixes_of_permutations_with_copies(q, m, first_n, pmemo)
    else:
        return cast(int, k_prefixes_of_permutations_with_copies(q, m, first_n, -1, pmemo))

def compute_jth_prefix_of_permutations_with_copies(q: int, m_or_counters: Union[int, List[int]], first_n: int, j: int,
                                                   pmemo: PermutationMemo) -> List[int]:
    if isinstance(m_or_counters, list):
        return cast(List[int], k_prefixes_of_permutations_with_copies(q, m_or_counters, first_n, j, pmemo))
    m = m_or_counters
    if first_n <= m:
        return compute_jth_combination(first_n, q, j)
    else:
        return cast(List[int], k_prefixes_of_permutations_with_copies(q, m, first_n, j, pmemo))

def recur_count_prefixes_of_permutations_with_copies(q: int, m: int, first_n: int,
                                                     pmemo: PermutationMemo) -> int:
    memo = pmemo.memo
    def recur(start_i: int, need_n: int, q: int, m: int) -> int:
        if need_n == 0:
            return 1
        elif start_i < q:
            if ((q - start_i) * m) >= need_n:
                combos = memo.get((start_i, need_n), None)
                if not combos:
                    combos = 0
                    for v in range(0, min(m, need_n)+1):
                        subs = recur(start_i+1, need_n - v, q, m)
                        combos += subs * count_interleavings(v, need_n)
                    memo[(start_i, need_n)] = combos
                return combos
            else:
                return 0
        else:
            return 0

    return recur(0, first_n, q, m)

def k_prefixes_of_permutations_with_copies(q: int, m_or_counters: Union[int, List[int]], first_n: int, find: int,
                                           pmemo: PermutationMemo) -> Union[int, List[int]]:
    # Dispatch on `m_or_counters` as a number (representing a uniform array) or an array:
    def available_after(start_i: int) -> int:
        nonlocal m_or_counters, q
        if isinstance(m_or_counters, list):
            return sum(m_or_counters[start_i:])
        else:
            return ((q - start_i) * m_or_counters)
    def available_at(start_i: int) -> int:
        nonlocal m_or_counters
        if isinstance(m_or_counters, list):
            return m_or_counters[start_i]
        else:
            return m_or_counters
    # Implements a find operation if `find` is > -1, otherwise just counts.
    # Based on `recur_count_prefixes_of_permutations_with_copies`, but explicitly
    # managing the continuation (so it can grows as deep as needed), and with two
    # extra arguments to enable generating the permutation instead of just counting.
    # Continuation frame ids:
    DoCount = 0
    DoNext = 1
    DoRecord = 2
    # Memo table for dynamic programming:
    memo = pmemo.memo
    # Value delivered to a continuation:
    value = 0
    # Our continuation, initialized with a call to count
    ks = cast(list, [(DoCount, (0,        # start_i
                                first_n,  # need_n
                                (),       # buckets: a cons-style list in reverse order, number of items allocated to a choice in `q`
                                1))])     # multiplier: so we can find a specific permutation
    while ks:
        k, state = ks.pop()
        if k == DoCount:
            start_i, need_n, buckets, multiplier = state
            if need_n == 0:
                # There's only one 0-length permutation
                value = 1
                if find > -1:
                    if find < multiplier:
                        # The permutation we want is within this bucket configuration
                        return _construct_permutation_with_copies(find, q, first_n, buckets_to_counters(buckets, q))
                    else:
                        find -= multiplier
            elif start_i >= q:
                value = 0
            elif available_after(start_i) < need_n:
                value = 0
            else:
                m_value = memo.get((start_i, need_n), None)
                if m_value and find > -1:
                    total = m_value * multiplier
                    if find < total:
                        m_value = None # explore this subtree, so we find the permutation
                    else:
                        find -= total
                if not m_value:
                    ks.append((DoNext, (0, start_i, need_n, 0, buckets, multiplier, 0)))
                    value = 0
                else:
                    value = m_value
        elif k == DoNext:
            v, start_i, need_n, count, buckets, multiplier, this_mult = state
            next_mult = count_interleavings(v, need_n)
            count += value * this_mult
            if v < min(available_at(start_i), need_n):
                ks.append((DoNext, (v+1, start_i, need_n, count, buckets, multiplier, next_mult)))
            else:
                ks.append((DoRecord, (v, start_i, need_n, count, next_mult)))
            ks.append((DoCount, (start_i+1, need_n - v, (v, buckets), next_mult * multiplier)))
        elif k == DoRecord:
            v, start_i, need_n, count, this_mult = state
            value = count + (value * this_mult)
            memo[(start_i, need_n)] = value
    return value

def count_interleavings(v: int, need_n: int) -> int:
    v_n = need_n - v
    # combinations with `v_n` elements, interleaved with `v` elements:
    return count_remaining_permutations([v_n, v])

# Converts the cons-style bucket representation of allocations
# to the `q` choices into a mutable-array counter representation
def buckets_to_counters(buckets: Any, q: int) -> List[int]:
    counters = [0 for i in range(q)]
    rev_buckets = cast(Any, ())
    while buckets != ():
        rev_buckets = (cast(Tuple[int, Any], buckets)[0], rev_buckets)
        buckets = cast(Tuple[int, Any], buckets)[1]
    i = 0;
    while rev_buckets != ():
        counters[i] = rev_buckets[0]
        rev_buckets = rev_buckets[1]
        i += 1
    return counters
