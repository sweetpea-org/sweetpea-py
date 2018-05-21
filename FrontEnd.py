from functools import reduce
from collections import namedtuple

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         Named Tuples
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Everything the user interacts with
Factor       = namedtuple('Factor', 'name levels')
Window       = namedtuple('Window', 'func args stride')
Window.__new__.__defaults__ = (None, None, 1)

WithinTrial  = namedtuple('WithinTrial', 'func args')
Transition   = namedtuple('Transition', 'func args')
DerivedLevel = namedtuple('DerivedLevel', 'name window')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Everything from the frontend

HLBlock = namedtuple('HLBlock', 'design xing hlconstraints')
ILBlock = namedtuple('ILBlock', 'startAddr endAddr design xing constraints')

# constraints
FullyCross = namedtuple('FullyCross', '')
Consistency = namedtuple('Consistency', '')

NoMoreThanKInARow = namedtuple('NoMoreThanK', 'k levels')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         "Front End" transformations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
A full crossing is the product of the number of levels 
in all the factors in the xing.

Usage::

    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue"])
    >>> fullyCrossSize([color, text])
    4

:param xing: A list of Factor namedpairs ``Factor(name, levels)``.
:rtype: Int
"""
def fullyCrossSize(xing) -> int:
    acc = 1
    for fact in xing:
        acc *= len(fact.levels)
    return acc

