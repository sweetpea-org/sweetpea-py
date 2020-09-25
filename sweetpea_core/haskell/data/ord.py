from enum import IntEnum, auto


class Ordering(IntEnum):
    LT = auto()
    EQ = auto()
    GT = auto()


LT = Ordering.LT
EQ = Ordering.EQ
GT = Ordering.GT
