"""This module provides aliases for values used in representing numbers in a
binary format.
"""


from typing import List


__all__ = ['BinaryNumber']


BinaryNumber = List[int]


def binary(value: int) -> BinaryNumber:
    """Converts an integer value to binary where the output representation is a
    list of binary digits of the alphabet {-1, 1} (i.e., similar to a normal
    binary representation except the "false" value is -1 instead of 0).

    For example:

        2  => [1, -1]       == 0b10
        11 => [1, -1, 1, 1] == 0b1011
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
