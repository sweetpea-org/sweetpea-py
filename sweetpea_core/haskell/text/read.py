from typing import Callable, Optional, TypeVar


__all__ = ['read_maybe']


T = TypeVar('T')


def read_maybe(func: Callable[[str], T], x: str) -> Optional[T]:
    try:
        return func(x)
    except ValueError:
        return None
