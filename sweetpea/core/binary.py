"""This module provides aliases for values used in representing numbers in a
binary format.
"""


from typing import List


__all__ = ['BinaryNumber', 'int_to_binary']


#: A representation of a binary number as a list of integers, where each
#: element of the list is either 1 or -1.
BinaryNumber = List[int]


def int_to_binary(value: int) -> BinaryNumber:
    """Converts an integer value to binary where the output representation is a
    list of binary digits of the alphabet {-1, 1} (i.e., similar to a normal
    binary representation except the "false" value is -1 instead of 0).

    For example:

    =======  =================  ==========
    Decimal  ``int_to_binary``  Binary
    =======  =================  ==========
    ``2``    ``[1, -1]``        ``0b10``
    ``11``   ``[1, -1, 1, 1]``  ``0b1011``
    =======  =================  ==========
    """
    output: BinaryNumber = []
    while value != 0:
        if value % 2 == 0:
            output.append(-1)
        else:
            output.append(1)
        value //= 2
    output.reverse()
    return output
