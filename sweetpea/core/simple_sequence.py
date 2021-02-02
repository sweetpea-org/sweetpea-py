"""Provides a simple custom sequence type for internal use."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence
from copy import deepcopy
from typing import Dict, Iterable, List, Type, TypeVar, Union, cast, overload


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
    def _element_type(cls) -> Type[_T]:
        """Returns the class corresponding to the element type, from which new
        elements can be constructed.
        """
        raise NotImplementedError()

    @classmethod
    def _construct_element(cls, value) -> _T:
        # NOTE: mypy 0.800 does not appear to correctly handle class properties
        #       produced with the `@classmethod` and `@property` decorators, so
        #       the following invocations of `cls._element_type` are flagged as
        #       incorrect.
        if isinstance(value, cls._element_type):  # type: ignore
            return value
        return cls._element_type(value)  # type: ignore

    def __init__(self, /, first_value: Union[None, List[Union[_T, int]], _T, int] = None, *rest_values: Union[_T, int]):
        values: Iterable[Union[_T, int]]
        if first_value is None:
            if rest_values:
                raise ValueError(f"cannot instantiate {type(self).__name__} with both None and variadic arguments")
            values = []
        elif isinstance(first_value, (list, tuple)):
            if rest_values:
                raise ValueError(f"cannot instantiate {type(self).__name__} with both list and variadic arguments")
            values = first_value
        else:
            values = first_value, *rest_values
        self._vals = [self._construct_element(value) for value in values]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(repr, self._vals))})"

    def __copy__(self) -> SimpleSequence[_T]:
        new_sequence = self.__class__()
        new_sequence._vals = self._vals
        return new_sequence

    def __deepcopy__(self, memo: Dict) -> SimpleSequence[_T]:
        new_base_vals = deepcopy(self._vals, memo)
        new_sequence = self.__class__()
        new_sequence._vals = new_base_vals
        return new_sequence

    @overload
    def __getitem__(self, index: int) -> _T:
        pass

    @overload
    def __getitem__(self, index: slice) -> SimpleSequence[_T]:
        pass

    def __getitem__(self, index: Union[int, slice]) -> Union[_T, SimpleSequence[_T]]:
        if isinstance(index, slice):
            return self.__class__(*self._vals[index])
        return self._vals[index]

    @overload
    def __setitem__(self, index: int, item: _T) -> None:
        pass

    @overload
    def __setitem__(self, index: slice, item: Iterable[_T]) -> None:
        pass

    def __setitem__(self, index: Union[int, slice], item: Union[_T, Iterable[_T]]) -> None:
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
