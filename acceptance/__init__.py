import os
from typing import Tuple, List, Union
from itertools import repeat, permutations
from random import shuffle

from sweetpea._internal.primitive import Factor, SimpleLevel, DerivedLevel
from sweetpea._internal.constraint import  AtMostKInARow
from sweetpea._internal.level import get_all_levels
from sweetpea._internal.derivation_processor import DerivationProcessor

def __assert_atmostkinarow_pair(k: int, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], experiments: List[dict]) -> None:
    sublist = list(repeat(level[1], k + 1))
    for e in experiments:
        assert sublist not in [e[level[0]][i:i+k+1] for i in range(len(e[level[0]]) - (k + 1))]

def __assert_atmostkinarow_factor(k: int, f: Factor, experiments: List[dict]) -> None:
    factor_name = f.name
    for level in f.levels:
        sublist = list(repeat(level.name, k + 1))
        for e in experiments:
            assert sublist not in [e[factor_name][i:i + k + 1] for i in range(len(e[factor_name]) - (k + 1))]

def assert_atmostkinarow(c: AtMostKInARow, experiments: List[dict]) -> None:
    if isinstance(c.level, Factor):
        __assert_atmostkinarow_factor(c.k, c.level, experiments)
    else:
        level_tuples = get_all_levels([c.level])
        for t in level_tuples:
            __assert_atmostkinarow_pair(c.k, t, experiments)

def assert_no_repetition(experiments: List[dict]) -> None:
    for seq in experiments:
        levels_lists = [levels for f, levels in seq.items()]
        transposed = list(map(list, zip(*levels_lists)))
        for t in transposed:
            assert transposed.count(t) == 1, "{} repeats in this trial sequence!".format(t)

def shuffled_design_sample(input, num):
    perms = list(permutations(input))
    shuffle(perms)
    return perms[:num]

# Set to True to reset recorded files that have specific CNF encodings,
# but leave as False to perform regression tests where the CNF should
# not change:
reset_expected_solutions = False

path_to_cnf_files = os.path.dirname(os.path.abspath(__file__)) + "/cnf_files"
