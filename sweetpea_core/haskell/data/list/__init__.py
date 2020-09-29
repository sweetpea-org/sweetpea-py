from typing import Callable, List, TypeVar


__all__ = ['concat', 'zip_with']


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


def concat(xss: List[List[T]]) -> List[T]:
    return [x for xs in xss for x in xs]


def zip_with(transformer_function: Callable[[T, U], V], ts: List[T], us: List[U]) -> List[V]:
    ts_len = len(ts)
    us_len = len(us)
    index = 0
    result: List[V] = []
    while index < ts_len and index < us_len:
        result.append(transformer_function(ts[index], us[index]))
        index += 1
    return result
