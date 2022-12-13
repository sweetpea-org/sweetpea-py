from abc import ABC, abstractmethod
from typing import List, cast
from itertools import repeat

from sweetpea._internal.block import Block
from sweetpea._internal.iter import intersperse


"""
Data object for sampling result.
"""
class SamplingResult:
    def __init__(self, samples: List[dict], metrics: dict) -> None:
        self.samples = samples
        self.metrics = metrics

"""
Generic interface for sampling strategies.
"""
class Gen(ABC):

    """
    Sample some number of trial sequences for the given block.

    TODO: This should accept some kind of options structure. What if we want
    to disable metrics? Or use some other feature flag?
    """
    @staticmethod
    @abstractmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        pass

    """
    Decodes a single solution into a dict of this form:

        {
        '<factor name>': ['<trial 1 label>', '<trial 2 label>, ...]
        ...
        }

    For factors that don't have a value for a given level, such as Transitions,
    the label will be ''.
    """
    @staticmethod
    def decode(block: Block, solution: List[int]) -> dict:
        # Sort the list and remove any negative (false) variables
        solution.sort()
        solution = list(filter(lambda v: v > 0, solution))

        # Separate into simple/complex variables.
        simple_variables = list(filter(lambda v: v <= block.grid_variables(), solution))
        complex_variables = list(filter(lambda v: v > block.grid_variables(), solution))

        experiment = cast(dict, {})

        # Simple factors
        tuples = list(map(lambda v: block.decode_variable(v), simple_variables))
        string_tuples = list(map(lambda t: (t[0].name, t[1].name), tuples))
        for (factor_name, level_name) in string_tuples:
            if factor_name not in experiment:
                experiment[factor_name] = []
            experiment[factor_name].append(level_name)

        # Complex factors - The challenge here is knowing when to insert '', rather than using the variables.
        # Start after 'width' trials, and shift 'stride' trials for each variable.
        complex_factors = list(filter(lambda f: f.has_complex_window, block.act_design))
        for f in complex_factors:
            # Get variables for this factor
            start = block.first_variable_for_level(f, f.levels[0]) + 1
            end = start + block.variables_for_factor(f)
            variables = list(filter(lambda n: n in range(start, end), complex_variables))

            # Get the level names for the variables in the solution.
            level_tuples = list(map(lambda v: block.decode_variable(v), variables))
            level_names = list(map(lambda t: (t[1].name), level_tuples))

            # Intersperse empty strings for the trials to which this factor does not apply.
            #level_names = list(intersperse('', level_names, f.levels[0].window.stride - 1))
            #level_names = list(repeat('', f.levels[0].window.width - 1)) + level_names
            level_names_fill = []
            for n in range(block.trials_per_sample()):
                level_names_fill.append(level_names.pop(0) if f.applies_to_trial(n+1) else '')
            experiment[f.name] = level_names_fill

        return experiment

    @staticmethod
    def class_name():
        return "Unknown Sampling Strategy"
