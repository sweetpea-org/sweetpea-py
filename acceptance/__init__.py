from typing import Tuple, List, Union

from itertools import repeat

from sweetpea.primitives import Factor, SimpleLevel, DerivedLevel
from sweetpea.constraints import AtMostKInARow
from sweetpea.internal import get_all_levels


def __assert_atmostkinarow_pair(k: int, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], experiments: List[dict]) -> None:
    sublist = list(repeat(level[1], k + 1))
    for e in experiments:
        assert sublist not in [e[level[0]][i:i+k+1] for i in range(len(e[level[0]]) - (k + 1))]

def __assert_atmostkinarow_factor(k: int, f: Factor, experiments: List[dict]) -> None:
    for l in f.levels:
        sublist = list(repeat(l[1], k + 1))
        for e in experiments:
            assert sublist not in [e[level[0]][i:i+k+1] for i in range(len(e[level[0]]) - (k + 1))]


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
