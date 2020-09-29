from typing import cast, Optional, TypeVar


__all__ = ['from_just']


T = TypeVar('T')


def from_just(a: Optional[T]) -> T:
    return cast(T, a)
