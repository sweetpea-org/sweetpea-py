from typing import (
    cast, overload,
    Callable, Iterable, Iterator, List, Optional, Sequence, TypeVar, Union)


__all__ = [
    'concat', 'concat_map', 'drop', 'find_index',
    'intersperse', 'intercalate', 'repeat', 'take', 'zip_with',
    # Functions on strings.
    'lines', 'words', 'unlines', 'unwords'
]


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')

StrOrSequence = Union[str, Sequence[T]]
StrOrList = Union[str, List[T]]


def concat(xss: Sequence[StrOrSequence[T]]) -> StrOrList[T]:
    if not xss:
        return []
    if isinstance(xss[0], str):
        xss = cast(Sequence[str], xss)
        return ''.join(xss)
    else:
        xss = cast(Sequence[Sequence[T]], xss)
        return [x for xs in xss for x in xs]


def concat_map(func: Callable[[T], Sequence[U]], xs: Sequence[T]) -> List[U]:
    return [y for ys in (func(x) for x in xs) for y in ys]


def drop(amount: int, xs: Iterable[T]) -> List[T]:
    it = iter(xs)
    try:
        for _ in range(amount):
            next(it)
    finally:
        return list(it)


def find_index(pred: Callable[[T], bool], xs: Sequence[T]) -> Optional[int]:
    index = 0
    for x in xs:
        if pred(x):
            return index
        index += 1
    return None


def intersperse(sep: T, xs: Iterable[T]) -> List[T]:
    it = iter(xs)
    nxt: Optional[T] = next(it)

    def _intersperserator() -> Iterator[T]:
        nonlocal it
        nonlocal nxt
        while True:
            try:
                if nxt is not None:
                    tmp = nxt
                    nxt = None
                    yield tmp
                else:
                    nxt = next(it)
                    yield sep
            except StopIteration:
                break

    return list(_intersperserator())


@overload
def intercalate(xs: List[T], xss: Sequence[Sequence[T]]) -> List[T]:
    ...


@overload
def intercalate(sep: str, ss: Sequence[str]) -> str:
    ...


def intercalate(sep, elems):
    return concat(intersperse(sep, elems))


def repeat(value: T) -> Iterator[T]:
    while True:
        yield value


def take(amount: int, xs: Iterable[T]) -> List[T]:
    it = iter(xs)
    result = []
    try:
        for _ in range(amount):
            result.append(next(it))
    finally:
        return result


def zip_with(transformer_function: Callable[[T, U], V], ts: List[T], us: List[U]) -> List[V]:
    ts_len = len(ts)
    us_len = len(us)
    index = 0
    result: List[V] = []
    while index < ts_len and index < us_len:
        result.append(transformer_function(ts[index], us[index]))
        index += 1
    return result


####################
# Functions on strings

# NOTE: `s.split('\n')` doesn't match up with Haskell's `lines` function, so we
#       have a more complex implementation here.
def lines(s: str) -> List[str]:
    def s_break():
        break_index = find_index(lambda c: c == '\n', list(s))
        if break_index is None:
            return (s, "")
        return (''.join(take(break_index, s)), ''.join(drop(break_index, s)))

    if s == "":
        return []
    ls = []
    while s:
        (l, s_) = s_break()
        ls.append(l)
        s = s_[1:]
    return ls


def words(line: str) -> List[str]:
    return line.split()


def unlines(lines: List[str]) -> str:
    return '\n'.join(lines)


def unwords(words: List[str]) -> str:
    return ' '.join(words)
