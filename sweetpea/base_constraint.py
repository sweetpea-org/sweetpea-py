"""This module provides the base constraint class."""


from abc import ABC, abstractmethod
from typing import List

from sweetpea.primitives import Factor


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

    def is_complex_for_combinatoric(self) -> bool:
        return True

    def desugar(self, replacements: dict) -> List:
        """Some constraints accept shorthand representations. (Like accepting a
        whole factor, rather than individual factor and level name pairs.)

        :func:`.Constraint.desugar` is responsible for returning the desugared
        representation of a constraint. When a block is constructed, it will
        desugar all constraints, replacing them with their desuagared versions
        before proceding.
        """
        return [self]

    def uses_factor(self, f: Factor) -> bool:
        """Reports whether the given factor is relevant to the constraint, and
        can return False when a factor is known to be relevant to the
        crossing or some other constraint.
        """
        return False

    @abstractmethod
    def potential_sample_conforms(self, sample: dict) -> bool:
        """For rejection sampling, checks whether a given potential sample
        matches a constraint, as long as crossing, exclusion for non-complex factors, and
        minimum-trial contraints are already satisfied.
        """
        pass
