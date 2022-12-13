"""This module provides some convenience functions to be used internally."""


from itertools import islice, tee, chain, repeat
from typing import Any, Tuple, List, Iterator, Iterable, Union, cast

from sweetpea._internal.primitive import Factor, DerivedLevel, SimpleLevel


def get_all_levels(design: List[Factor]) -> List[Tuple[Factor, Union[SimpleLevel, DerivedLevel]]]:
    return [(factor, cast(Union[SimpleLevel, DerivedLevel], level)) for factor in design for level in factor.levels]
