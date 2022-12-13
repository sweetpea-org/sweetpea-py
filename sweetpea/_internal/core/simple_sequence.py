"""Provides a simple custom sequence type for internal use."""

from __future__ import annotations

from abc import abstractmethod
from copy import deepcopy
from typing import Dict, Iterable, List, MutableSequence, Type, TypeVar, Union, overload


__all__ = ['SimpleSequence']


#: A generic type.
_T = TypeVar('_T')


class SimpleSequence(MutableSequence[_T]):
    """A custom generic sequence. :class:`SimpleSequence` features an advanced
    initialization mechanism that allows for automatically converting given
    arguments into elements of the desired type. It can also smartly handle
    being given lists of elements for initialization.

    The purpose of :class:`SimpleSequence` was to grant classes like
    :class:`Clause` and :class:`CNF` the ability to be initialized with
    literals without needing to duplicate that code. :class:`SimpleSequence` is
    a :class:`typing.MutableSequence` with all the expected functionality, and
    it also provides built-in support for :func:`copy.copy` and
    :func:`copy.deepcopy`.

    :class:`SimpleSequence` was also built to support better type-checking
    throughout SweetPea. To that effect, the implementation was inspired by
    discussion in `mypy issue #4108
    <https://github.com/python/mypy/issues/4108>`_.
    """

    _vals: List[_T]

    @classmethod
    @abstractmethod
    def _get_element_type(cls) -> Type[_T]:
        """Returns the class corresponding to the element type, from which new
        elements can be constructed.
        """
        raise NotImplementedError()

    @classmethod
    def _construct_element(cls, value) -> _T:
        if isinstance(value, cls._get_element_type()):
            return value
        # NOTE: mypy reports "Too many arguments for 'object'" on the following
        #       line. However, the code works as expected, so typechecking is
        #       disabled for this line.
        return cls._get_element_type()(value)  # type: ignore

    def __init__(self, first_value: Union[None, List[Union[_T, int]], _T, int] = None, *rest_values: Union[_T, int]):
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

    def __delitem__(self, index: Union[int, slice]) -> None:
        self._vals.__delitem__(index)

    def insert(self, index: int, item: _T) -> None:
        """Inserts the ``item`` before the given ``index`` in the sequence."""
        self._vals.insert(index, item)

    def __len__(self) -> int:
        return len(self._vals)
