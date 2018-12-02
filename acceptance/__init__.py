from typing import Tuple, List

from itertools import repeat

from sweetpea.primitives import Factor
from sweetpea.constraints import NoMoreThanKInARow
from sweetpea.internal import get_all_level_names


def __assert_nomorethankinarow_pair(k: int, level: Tuple[str, str], experiments: List[dict]) -> None:
    sublist = list(repeat(level[1], k + 1))
    for e in experiments:
        assert sublist not in [e[level[0]][i:i+k+1] for i in range(len(e[level[0]]) - (k + 1))]


def assert_nomorethankinarow(c: NoMoreThanKInARow, experiments: List[dict]) -> None:
    if isinstance(c.levels, Factor):
        level_tuples = get_all_level_names([c.levels])
        for t in level_tuples:
            __assert_nomorethankinarow_pair(c.k, t, experiments)
    else:
        __assert_nomorethankinarow_pair(c.k, c.levels, experiments)
