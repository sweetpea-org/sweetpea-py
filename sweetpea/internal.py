from itertools import islice, tee, chain, repeat
from typing import Any, Tuple, List, Iterator, Iterable

from sweetpea.primitives import Factor, DerivedLevel, get_level_name


"""
Usage:

    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    get_all_level_names([color, text])

    [('color', 'red'), ('color', 'blue'), ('text', 'red'), ('text', 'blue')]

"""
def get_all_level_names(design: List[Factor]) -> List[Tuple[Any, Any]]:
    return [(factor.name, get_level_name(level)) for factor in design for level in factor.levels]


"""
Handy-dandy chunker from SO:
https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
"""
# TODO: add a canary print statement in case the resulting lists are not all the same length-- that is not the expected behavior (at least how it's used in desugar_fullycrossed)
def chunk(it: Iterable[Any], size: int) -> Iterator[Tuple[Any, ...]]:
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def chunk_list(it: Iterable[Any], size: int) -> Iterator[List[Any]]:
    it = iter(it)
    return iter(lambda: list(islice(it, size)), [])


"""
Helper recipe from:
https://docs.python.org/3/library/itertools.html#itertools-recipes
"""
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


"""
Another helper from SO, with modification for repeating the delimiter.
https://stackoverflow.com/questions/5655708/python-most-elegant-way-to-intersperse-a-list-with-an-element
"""
def intersperse(delimiter, seq, repeat_delimiter = 1):
    nested_list_seq = map(lambda elem: [elem], seq)
    new_seq = zip(repeat([delimiter] * repeat_delimiter), nested_list_seq)
    return chain(*islice(chain.from_iterable(new_seq), 1, None))
