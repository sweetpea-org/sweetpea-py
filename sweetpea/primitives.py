from typing import Any, Type, List


def require_type(label: str, type: Type, value: Any):
    if not isinstance(value, type):
        raise ValueError(label + ' must be a ' + str(type) + '.')


def require_non_empty_list(label: str, value: Any):
    require_type(label, List, value)
    if len(value) == 0:
        raise ValueError(label + ' must not be empty.')


class Factor:
    def __init__(self, name: str, levels) -> None:
        self.name = name
        self.levels = levels
        self.__validate()

    def __validate(self):
        require_type('Factor name', str, self.name)
        require_non_empty_list('Factor levels', self.levels)
        # TODO: Validate that levels are all either strings or Derived levels.


class DerivedLevel:
    def __init__(self, name, window):
        self.name = name
        self.window = window
        # TODO: validation


class WithinTrial:
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        # TODO: validation


class Transition:
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        # TODO: validation


class Window:
    def __init__(self, fn, args, stride):
        self.fn = fn
        self.args = args
        self.stride = stride
        # TODO: validation