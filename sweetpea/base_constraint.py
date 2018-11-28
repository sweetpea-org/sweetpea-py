from abc import abstractmethod

"""
Generic interface for constraints.
"""
class Constraint:
    @abstractmethod
    def apply(self, block, backend_request) -> None:
        pass
