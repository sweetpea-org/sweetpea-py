from typing import List, cast


"""
Given a list of dimension sizes, and an integer less than the product of the sizes,
this function will extract the component value for each dimension from the total.

For example, if sizes is [3, 4, 2], there are 24 possible combinations of the three.
If 0 <= n < 24, this function will return the selections for each dimension for that n.
"""
def extract_components(sizes: List[int], n: int) -> List[int]:
    components = []
    for s in sizes:
        components.append(n % s)
        n //= s

    return components


"""
The are n! permutations of n elements. Each permutation can be uniquely identified by and constructed from
its "inversion sequence". This function will compute the jth inversion sequence for a set of n elements.

Inversion Sequences: http://mathonline.wikidot.com/the-inversion-sequence-of-a-permutation
See also "Introductory Combinatorics" by Brualdi.
"""
def compute_jth_inversion_sequence(n, j):
    inversion = []
    for k in range(n, 1, -1):
        result = j % k
        inversion.append(result)
        j //= k

    inversion.append(0)
    return inversion


"""
Given an inversion sequence, construct the permutation.
"""
def construct_permutation(inversion_sequence: List[int]) -> List[int]:
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


"""
In a sequence of l items, where there are n choices for each item, this will compute
the jth combination, out of all n^l possibilities.
"""
def compute_jth_combination(l, n, j):
    combination = [None] * l
    for k in range(l - 1, -1, -1):
        combination[k] = j % n
        j //= n

    return combination
