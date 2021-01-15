"""Provides a simple custom sequence type for internal use."""


from collections.abc import MutableSequence
from typing import Iterable, List, TypeVar, Union, overload


__all__ = ['SimpleSequence']


_T = TypeVar('_T')


class SimpleSequence(MutableSequence[_T]):
    """A simple, custom generic sequence.

    Implementation inspired by:
        https://github.com/python/mypy/issues/4108
    """

    _vals: List[_T]

    def __init__(self, *values: _T):
        self._vals = list(values)

    def __repr__(self) -> str:
        return self.__class__.__name__ + str(self._vals)

    @overload
    def __getitem__(self, index: int) -> _T:
        pass

    @overload
    def __getitem__(self, index: slice) -> SimpleSequence[_T]:
        pass

    # FIXME: As of pylint 2.6.0 with Python 3.9.1, pylint mistakenly labels
    #        Union (and Optional) as unsubscriptable objects. This will be
    #        fixed soon, and when it is the pylint pragma on the following line
    #        should be removed.
    def __getitem__(self, index: Union[int, slice]) -> Union[_T, SimpleSequence[_T]]:  # pylint: disable=unsubscriptable-object,line-too-long
        if isinstance(index, slice):
            return self.__class__(*self._vals[index])
        return self._vals[index]

    @overload
    def __setitem__(self, index: int, item: _T) -> None:
        pass

    @overload
    def __setitem__(self, index: slice, item: Iterable[_T]) -> None:
        pass

    # FIXME: See FIXME for SimpleSequence.__getitem__.
    def __setitem__(self, index: Union[int, slice], item: Union[_T, Iterable[_T]]) -> None:  # pylint: disable=unsubscriptable-object,line-too-long
        # FIXME: As of mypy 0.790 with Python 3.9.1, mypy is unable to handle
        #        the separate overloads for this function as documented in:
        #            https://github.com/python/mypy/issues/7858
        #        If this is fixed, remove the following pragma.
        self._vals[index] = item  # type: ignore

    @overload
    def __delitem__(self, index: int) -> None:
        pass

    @overload
    def __delitem__(self, index: slice) -> None:
        pass

    # FIXME: See FIXME for SimpleSequence.__getitem__.
    def __delitem__(self, index: Union[int, slice]) -> None:  # pylint: disable=unsubscriptable-object
        self._vals.__delitem__(index)

    def insert(self, index: int, item: _T) -> None:
        """Inserts an item before the index."""
        self._vals.insert(index, item)

    def __len__(self) -> int:
        return len(self._vals)
