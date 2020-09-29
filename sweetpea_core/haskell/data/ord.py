from enum import IntEnum, auto


__all__ = ['Ordering', 'LT', 'EQ', 'GT']


class Ordering(IntEnum):
    LT = auto()
    EQ = auto()
    GT = auto()


LT = Ordering.LT
EQ = Ordering.EQ
GT = Ordering.GT
