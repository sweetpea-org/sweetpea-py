"""This module provides a simple enumeration base class for managing return
codes in command-line utilities.
"""


from enum import Enum


__all__ = ['ReturnCodeEnum']


class ReturnCodeEnum(Enum):
    """Command-line functions produce return codes, and sometimes these do not
    necessarily indicate an error. Subclasses of this enum can be used for
    managing the various return codes and checking against them conveniently.
    """

    @classmethod
    def has_value(cls, value: int) -> bool:
        """Determines whether this :class:`ReturnCodeEnum` contains the
        indicated ``value``.
        """
        return value in (e.value for e in cls)
