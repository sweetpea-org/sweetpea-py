from abc import ABC, abstractmethod

"""
Generic interface for constraints.
"""
class Constraint(ABC):
    @abstractmethod
    def apply(self, block, backend_request) -> None:
        pass
