"""This module provides the base constraint class."""


from abc import ABC, abstractmethod
from typing import List


class Constraint(ABC):
    """Generic interface for constraints."""

    @abstractmethod
    def validate(self, block) -> None:
        """Constraints can't be completely validated in isolation. This
        function will be called on all constraints with the block during the
        block initialization to ensure all constraints are valid.
        """
        pass

    @abstractmethod
    def apply(self, block, backend_request) -> None:
        pass

    def desugar(self) -> List:
        """Some constraints accept shorthand representations. (Like accepting a
        whole factor, rather than individual factor and level name pairs.)

        :func:`.Constraint.desugar` is responsible for returning the desugared
        representation of a constraint. When a block is constructed, it will
        desugar all constraints, replacing them with their desuagared versions
        before proceding.
        """
        return [self]
