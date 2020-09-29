from typing import Callable, List, TypeVar


__all__ = ['chunks_of', 'concat', 'zip_with']


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


def chunks_of(chunk_size: int, from_list: List[T]) -> List[List[T]]:
    prev = 0
    to_list = []
    while prev < len(from_list):
        to_list.append(from_list[prev:prev + chunk_size])
        prev += chunk_size
    return to_list


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
