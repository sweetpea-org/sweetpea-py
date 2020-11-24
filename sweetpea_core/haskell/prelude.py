from typing import List, Tuple, TypeVar


__all__ = ['fst', 'snd', 'sequence']


T = TypeVar('T')
U = TypeVar('U')


def fst(pair: Tuple[T, U]) -> T:
    return pair[0]


def snd(pair: Tuple[T, U]) -> U:
    return pair[1]


def sequence(xss: List[List[T]]) -> List[List[T]]:
    if not xss:
        return [[]]
    return [[x] + xs for x in xss[0] for xs in sequence(xss[1:])]
