from typing import List, TypeVar


__all__ = ['chunks_of']


T = TypeVar('T')


def chunks_of(chunk_size: int, from_list: List[T]) -> List[List[T]]:
    prev = 0
    to_list = []
    while prev < len(from_list):
        to_list.append(from_list[prev:prev + chunk_size])
        prev += chunk_size
    return to_list
