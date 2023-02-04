from typing import List, cast, Tuple, Dict
from sweetpea._internal.weight import combination_weight
from sweetpea._internal.primitive import Level, Factor


def combinations_mismatched_weights(start: int, end: int, crossing: List[Factor], sample: dict, or_less: bool):
    """returns how many mismatches of frequencies are in a sample against the expected crossing"""

    mismatch = 0
    combos = cast(Dict[Tuple[Level, ...], int], {})
    for t in range(start, end):
        key = tuple([sample[f][t] for f in crossing])
        combos[key] = combos.get(key, 0) + 1
    for combo, count in combos.items():
        mismatch += abs(count - combination_weight(combo))
    return mismatch
