from typing import List, Tuple, TypeVar


__all__ = ['even', 'fst', 'snd', 'sequence']


T = TypeVar('T')
U = TypeVar('U')


def even(x: int) -> bool:
    return not x & 1


def fst(pair: Tuple[T, U]) -> T:
    return pair[0]


def snd(pair: Tuple[T, U]) -> U:
    return pair[1]


def sequence(xss: List[List[T]]) -> List[List[T]]:
    if not xss:
        return [[]]
    return [[x] + xs for x in xss[0] for xs in sequence(xss[1:])]
