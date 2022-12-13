import pytest

from math import factorial

from sweetpea._internal.combinatorics import (
    extract_components, compute_jth_inversion_sequence, construct_permutation,
    compute_jth_combination, compute_jth_permutation_prefix,
    count_prefixes_of_permutations_with_copies, recur_count_prefixes_of_permutations_with_copies, k_prefixes_of_permutations_with_copies,
    count_permutations_with_copies, compute_jth_prefix_of_permutations_with_copies,
    PermutationMemo
)

@pytest.mark.parametrize('sizes, n, expected', [
    [[4, 2, 3], 0,  [0, 0, 0]],
    [[4, 2, 3], 1,  [1, 0, 0]],
    [[4, 2, 3], 2,  [2, 0, 0]],
    [[4, 2, 3], 3,  [3, 0, 0]],
    [[4, 2, 3], 4,  [0, 1, 0]],
    [[4, 2, 3], 5,  [1, 1, 0]],
    [[4, 2, 3], 6,  [2, 1, 0]],
    [[4, 2, 3], 7,  [3, 1, 0]],
    [[4, 2, 3], 8,  [0, 0, 1]],
    [[4, 2, 3], 9,  [1, 0, 1]],
    [[4, 2, 3], 10, [2, 0, 1]],
    [[4, 2, 3], 11, [3, 0, 1]],
    [[4, 2, 3], 12, [0, 1, 1]],
    [[4, 2, 3], 13, [1, 1, 1]],
    [[4, 2, 3], 14, [2, 1, 1]],
    [[4, 2, 3], 15, [3, 1, 1]],
    [[4, 2, 3], 16, [0, 0, 2]],
    [[4, 2, 3], 17, [1, 0, 2]],
    [[4, 2, 3], 18, [2, 0, 2]],
    [[4, 2, 3], 19, [3, 0, 2]],
    [[4, 2, 3], 20, [0, 1, 2]],
    [[4, 2, 3], 21, [1, 1, 2]],
    [[4, 2, 3], 22, [2, 1, 2]],
    [[4, 2, 3], 23, [3, 1, 2]]
])
def test_extract_components(sizes, n, expected):
    assert extract_components(sizes, n) == expected


@pytest.mark.parametrize('n, j, sequence', [
    # 4! = 24 Sequences
    [4, 0,  [0, 0, 0, 0]],
    [4, 1,  [1, 0, 0, 0]],
    [4, 2,  [2, 0, 0, 0]],
    [4, 3,  [3, 0, 0, 0]],
    [4, 4,  [0, 1, 0, 0]],
    [4, 5,  [1, 1, 0, 0]],
    [4, 6,  [2, 1, 0, 0]],
    [4, 7,  [3, 1, 0, 0]],
    [4, 8,  [0, 2, 0, 0]],
    [4, 9,  [1, 2, 0, 0]],
    [4, 10, [2, 2, 0, 0]],
    [4, 11, [3, 2, 0, 0]],
    [4, 12, [0, 0, 1, 0]],
    [4, 13, [1, 0, 1, 0]],
    [4, 14, [2, 0, 1, 0]],
    [4, 15, [3, 0, 1, 0]],
    [4, 16, [0, 1, 1, 0]],
    [4, 17, [1, 1, 1, 0]],
    [4, 18, [2, 1, 1, 0]],
    [4, 19, [3, 1, 1, 0]],
    [4, 20, [0, 2, 1, 0]],
    [4, 21, [1, 2, 1, 0]],
    [4, 22, [2, 2, 1, 0]],
    [4, 23, [3, 2, 1, 0]],

    # First is alway 0s, Last is always counting down to zero
    [10, 0,                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
    [10, factorial(10) - 1, [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]],
])
def test_compute_jth_inversion_sequence(n, j, sequence):
    assert compute_jth_inversion_sequence(n, n, j) == sequence


@pytest.mark.parametrize('inversion_sequence, expected_permutation', [
    [[0, 0, 0, 0], [0, 1, 2, 3]],
    [[1, 0, 0, 0], [1, 0, 2, 3]],
    [[2, 0, 0, 0], [2, 0, 1, 3]],
    [[3, 0, 0, 0], [3, 0, 1, 2]],
    [[0, 1, 0, 0], [0, 2, 1, 3]],
    [[1, 1, 0, 0], [1, 2, 0, 3]],
    [[2, 1, 0, 0], [2, 1, 0, 3]],
    [[3, 1, 0, 0], [3, 1, 0, 2]],
    [[0, 2, 0, 0], [0, 3, 1, 2]],
    [[1, 2, 0, 0], [1, 3, 0, 2]],
    [[2, 2, 0, 0], [2, 3, 0, 1]],
    [[3, 2, 0, 0], [3, 2, 0, 1]],
    [[0, 0, 1, 0], [0, 1, 3, 2]],
    [[1, 0, 1, 0], [1, 0, 3, 2]],
    [[2, 0, 1, 0], [2, 0, 3, 1]],
    [[3, 0, 1, 0], [3, 0, 2, 1]],
    [[0, 1, 1, 0], [0, 2, 3, 1]],
    [[1, 1, 1, 0], [1, 2, 3, 0]],
    [[2, 1, 1, 0], [2, 1, 3, 0]],
    [[3, 1, 1, 0], [3, 1, 2, 0]],
    [[0, 2, 1, 0], [0, 3, 2, 1]],
    [[1, 2, 1, 0], [1, 3, 2, 0]],
    [[2, 2, 1, 0], [2, 3, 1, 0]],
    [[3, 2, 1, 0], [3, 2, 1, 0]]
])
def test_construct_permutation(inversion_sequence, expected_permutation):
    assert construct_permutation(inversion_sequence, len(inversion_sequence)) == expected_permutation


@pytest.mark.parametrize('l, n, j, expected_combination', [
    [4, 2, 0,  [0, 0, 0, 0]],
    [4, 2, 1,  [0, 0, 0, 1]],
    [4, 2, 2,  [0, 0, 1, 0]],
    [4, 2, 3,  [0, 0, 1, 1]],
    [4, 2, 4,  [0, 1, 0, 0]],
    [4, 2, 5,  [0, 1, 0, 1]],
    [4, 2, 6,  [0, 1, 1, 0]],
    [4, 2, 7,  [0, 1, 1, 1]],
    [4, 2, 8,  [1, 0, 0, 0]],
    [4, 2, 9,  [1, 0, 0, 1]],
    [4, 2, 10, [1, 0, 1, 0]],
    [4, 2, 11, [1, 0, 1, 1]],
    [4, 2, 12, [1, 1, 0, 0]],
    [4, 2, 13, [1, 1, 0, 1]],
    [4, 2, 14, [1, 1, 1, 0]],
    [4, 2, 15, [1, 1, 1, 1]],

    [2, 3, 0, [0, 0]],
    [2, 3, 1, [0, 1]],
    [2, 3, 2, [0, 2]],
    [2, 3, 3, [1, 0]],
    [2, 3, 4, [1, 1]],
    [2, 3, 5, [1, 2]],
    [2, 3, 6, [2, 0]],
    [2, 3, 7, [2, 1]],
    [2, 3, 8, [2, 2]]
])
def test_compute_jth_combination(l, n, j, expected_combination):
    assert compute_jth_combination(l, n, j) == expected_combination

@pytest.mark.parametrize('n, m',
                         [[5, 5],
                          [7, 2],
                          [6, 5]])
def test_compute_jth_permutation(n, m):
    found = {}
    for j in range(factorial(n) // factorial(n-m)):
        p = compute_jth_permutation_prefix(n, m, j)
        assert len(p) == m
        assert tuple(p) not in found
        found[tuple(p)] = True

@pytest.mark.parametrize('q, m',
                         [[2, 2],
                          [32, 32],
                          [17, 5]])
def test_consistent_permuatations_with_copies_count(q, m):
    amt1 = count_permutations_with_copies(q, m, q*m)
    amt2 = count_prefixes_of_permutations_with_copies(q, m, q*m, PermutationMemo())
    amt3 = k_prefixes_of_permutations_with_copies(q, m, q*m, -1, PermutationMemo())
    assert amt1 == amt2
    assert amt1 == amt3

@pytest.mark.parametrize('q, m, first_n',
                         [[2, 2, 2],
                          [32, 32, 4],
                          [17, 5, 19]])
def test_consistent_prefix_permuatations_count(q, m, first_n):
    amt1 = count_prefixes_of_permutations_with_copies(q, m, first_n, PermutationMemo())
    amt2 = recur_count_prefixes_of_permutations_with_copies(q, m, first_n, PermutationMemo())
    amt3 = k_prefixes_of_permutations_with_copies(q, m, first_n, -1, PermutationMemo())
    assert amt1 == amt2
    assert amt1 == amt3

@pytest.mark.parametrize('q, m',
                         [[2, 2],
                          [3, 2],
                          [2, 3]])
def test_construct_jth_permutation_with_copies(q, m):
    found1 = {}
    found2 = {}
    n = q*m
    pmemo = PermutationMemo()
    pmemo2 = PermutationMemo()
    count = count_prefixes_of_permutations_with_copies(q, m, n, pmemo)
    for j in range(count):
        p1 = compute_jth_prefix_of_permutations_with_copies(q, m, n, j, pmemo)
        p2 = k_prefixes_of_permutations_with_copies(q, m, n, j, pmemo2)
        assert len(p1) == q*m
        assert len(p2) == q*m
        assert tuple(p1) not in found1
        assert tuple(p2) not in found2
        found1[tuple(p1)] = True
        found2[tuple(p2)] = True
    assert found1 == found2

@pytest.mark.parametrize('q, m, first_n',
                         [[16, 4, 21]])
def test_construct_jth_prefix_permutation_with_copies(q, m, first_n):
    found = {}
    pmemo = PermutationMemo()
    count = count_prefixes_of_permutations_with_copies(q, m, first_n, pmemo)
    for j in range(0, count, count // 10):
        p = compute_jth_prefix_of_permutations_with_copies(q, m, first_n, j, pmemo)
        assert len(p) == first_n
        assert tuple(p) not in found
        found[tuple(p)] = True
    p = compute_jth_prefix_of_permutations_with_copies(q, m, first_n, count-1, pmemo)
    assert len(p) == first_n
    assert tuple(p) not in found
    found[tuple(p)] = True
