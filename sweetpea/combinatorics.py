"""This module provides combinatoric functionality."""


from typing import List, cast


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


def compute_jth_inversion_sequence(n, j):
    """The are ``n!`` permutations of ``n`` elements. Each permutation can be
    uniquely identified by and constructed from its "inversion sequence". This
    function will compute the ``j``th inversion sequence for a set of ``n``
    elements.

    Information on inversion sequences can be found:

    - `MathOnline <http://mathonline.wikidot.com/the-inversion-sequence-of-a-permutation>`__
    - "Introductory Combinatorics" by Richard A. Brualdi, ISBN 978-0136020400.
    """
    inversion = []
    for k in range(n, 1, -1):
        result = j % k
        inversion.append(result)
        j //= k

    inversion.append(0)
    return inversion


def construct_permutation(inversion_sequence: List[int]) -> List[int]:
    """Given an inversion sequence, construct the permutation."""
    length = len(inversion_sequence)
    permutation = cast(List[int], [None] * len(inversion_sequence))
    for n, b in enumerate(inversion_sequence):
        idx = 0
        step = -1
        while idx < length:
            if permutation[idx] == None:
                step += 1
                if step == b:
                    break
            idx += 1
        permutation[idx] = n

    return permutation


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
