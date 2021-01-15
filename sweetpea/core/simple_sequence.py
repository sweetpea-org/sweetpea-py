"""Provides a simple custom sequence type for internal use."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence
from typing import Callable, Iterable, List, TypeVar, Union, overload


__all__ = ['SimpleSequence']


_T = TypeVar('_T')


class SimpleSequence(MutableSequence[_T]):
    """A simple, custom generic sequence.

    Implementation inspired by:
        https://github.com/python/mypy/issues/4108
    """

    _vals: List[_T]

    # TODO: I wasn't able to get this to work with @staticmethod, even though
    #       it really *is* static. It could probably be done with a custom
    #       decorator to mash-up the @staticmethod and @property or something.
    # TODO: Even better would be to replace this with a simple attribute (like
    #       _vals above) and build a custom class decorator that can manipulate
    #       this. It'd look a lot cleaner, anyway.
    @classmethod
    @property
    @abstractmethod
    def _element_type(cls) -> Callable[..., _T]:
        """Returns a function that can produce instances of the element type.
        (The simplest option is to just supply the element type's class
        directly.)
        """
        raise NotImplementedError()

    def __init__(self, /, first_value: Union[List[Union[_T, int]], _T, int], *rest_values: Union[_T, int]):  # pylint: disable=unsubscriptable-object,line-too-long
        if isinstance(first_value, (list, tuple)):
            if rest_values:
                raise ValueError(f"cannot instantiate {type(self).__name__} with both list and variadic arguments")
            values = first_value
        else:
            values = first_value, *rest_values
        self._vals = [self._element_type(value) for value in values]

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
