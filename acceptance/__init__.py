from typing import Tuple, List

from itertools import repeat

from sweetpea.primitives import Factor
from sweetpea.constraints import AtMostKInARow
from sweetpea.internal import get_all_level_names


def __assert_atmostkinarow_pair(k: int, level: Tuple[str, str], experiments: List[dict]) -> None:
    sublist = list(repeat(level[1], k + 1))
    for e in experiments:
        assert sublist not in [e[level[0]][i:i+k+1] for i in range(len(e[level[0]]) - (k + 1))]


def assert_atmostkinarow(c: AtMostKInARow, experiments: List[dict]) -> None:
    if isinstance(c.level, Factor):
        level_tuples = get_all_level_names([c.level])
        for t in level_tuples:
            __assert_atmostkinarow_pair(c.k, t, experiments)
    else:
        __assert_atmostkinarow_pair(c.k, c.level, experiments)


def assert_no_repetition(experiments: List[dict]) -> None:
    for seq in experiments:
        levels_lists = [levels for f, levels in seq.items()]
        transposed = list(map(list, zip(*levels_lists)))
        for t in transposed:
            assert transposed.count(t) == 1, "{} repeats in this trial sequence!".format(t)
