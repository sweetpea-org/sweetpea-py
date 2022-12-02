
from typing import Tuple

from sweetpea._internal.primitive import Level

def combination_weight(levels: Tuple[Level, ...]) -> int:
    n = 1
    for l in levels:
        n *= l.weight
    return n
