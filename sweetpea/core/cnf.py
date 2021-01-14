"""Provides simple type aliases used in SweetPea Core."""


from typing import List, NewType


__all__ = ['Count', 'Var', 'Clause', 'CNF']


Count = NewType('Count', int)
Var = NewType('Var', int)
Clause = List[Var]
CNF = List[Clause]
