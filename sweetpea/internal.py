"""This module provides some convenience functions to be used internally."""


from itertools import islice, tee, chain, repeat
from typing import Any, Tuple, List, Iterator, Iterable, Union, cast

from sweetpea.primitives import Factor, DerivedLevel, get_internal_level_name, SimpleLevel, get_external_level_name


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


def chunk(it: Iterable[Any], size: int) -> Iterator[Tuple[Any, ...]]:
    """Handy-dandy chunker from SO:
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    # TODO: Add a canary print statement in case the resulting lists are not
    #       all the same length --- that is not the expected behavior (at least
    #       how it's used in desugar_fullycrossed)
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def chunk_list(it: Iterable[Any], size: int) -> Iterator[List[Any]]:
    it = iter(it)
    return iter(lambda: list(islice(it, size)), [])


def pairwise(iterable):
    """Helper recipe from:
    https://docs.python.org/3/library/itertools.html#itertools-recipes

    ``s -> (s0,s1), (s1,s2), (s2, s3), ...``
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def intersperse(delimiter, seq, repeat_delimiter = 1):
    """Another helper from SO, with modification for repeating the delimiter.
    https://stackoverflow.com/questions/5655708/python-most-elegant-way-to-intersperse-a-list-with-an-element
    """
    nested_list_seq = map(lambda elem: [elem], seq)
    new_seq = zip(repeat([delimiter] * repeat_delimiter), nested_list_seq)
    return chain(*islice(chain.from_iterable(new_seq), 1, None))
