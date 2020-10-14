from typing import Callable, List, TypeVar


__all__ = ['concat', 'concat_map', 'zip_with']


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


def concat(xss: List[List[T]]) -> List[T]:
    return [x for xs in xss for x in xs]


def concat_map(func: Callable[[T], List[U]], xs: List[T]) -> List[U]:
    return [y for ys in (func(x) for x in xs) for y in ys]


def zip_with(transformer_function: Callable[[T, U], V], ts: List[T], us: List[U]) -> List[V]:
    ts_len = len(ts)
    us_len = len(us)
    index = 0
    result: List[V] = []
    while index < ts_len and index < us_len:
        result.append(transformer_function(ts[index], us[index]))
        index += 1
    return result
