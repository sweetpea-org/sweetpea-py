"""This module provides some convenience functions to be used internally."""


from itertools import islice, tee, chain, repeat
from typing import Any, Tuple, List, Iterator, Iterable, Union, cast

from sweetpea.primitives import Factor, DerivedLevel, get_internal_level_name, SimpleLevel, get_external_level_name
from sweetpea.internal.iter import *

def get_all_external_level_names(design: List[Factor]) -> List[Tuple[str, str]]:
    """Usage

    ::

        >>> color = Factor("color", ["red", "blue"])
        >>> text  = Factor("text",  ["red", "blue"])
        >>> get_all_internal_level_names([color, text])
        [('color', 'red'), ('color', 'blue'), ('text', 'red'), ('text', 'blue')]
    """
    return [(factor.factor_name, get_external_level_name(level)) for factor in design for level in factor.levels]


def get_all_internal_level_names(design: List[Factor]) -> List[Tuple[str, str]]:
    return [(factor.factor_name, get_internal_level_name(level)) for factor in design for level in factor.levels]


def get_all_levels(design: List[Factor]) -> List[Tuple[Factor, Union[SimpleLevel, DerivedLevel]]]:
    return [(factor, cast(Union[SimpleLevel, DerivedLevel], level)) for factor in design for level in factor.levels]
