from dataclasses import dataclass
from typing import Generic, TypeVar


__all__ = ['State']


# A generic type variable for type-checking.
T = TypeVar('T')


@dataclass
class State(Generic[T]):
    """
    A simple encoding of the Control.Monad.Trans.State monad, implementing only
    the functionality necessary in this library.

    This is really just a glorified container for any arbitrary data, but it
    makes the code more readable and makes type checking nicer, so we use it.
    """
    # "What's in there?"
    # "Only what you take with you."
    state: T

    # Returns the current state.
    def get(self) -> T:
        return self.state

    # Replaces the current state with the given state.
    def put(self, val: T):
        self.state = val
