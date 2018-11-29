from abc import abstractmethod
from functools import reduce
from typing import List, Union

from sweetpea.primitives import Factor, Transition, Window
from sweetpea.logic import to_cnf_tseitin
from sweetpea.base_constraint import Constraint


"""
Abstract class for Blocks. Contains the required data, and defines abstract
methods that other blocks _must_ implement in order to work correctly.
"""
class Block:
    def __init__(self,
                 design: List[Factor],
                 crossing: List[Factor],
                 constraints: List[Constraint],
                 cnf_fn) -> None:
        self.design = design
        self.crossing = crossing
        self.constraints = constraints
        self.cnf_fn = cnf_fn
        # TODO: validation

    """
    Indicates the number of trials that are generated per sample for this block
    configuration.

    Analogous to the old __fully_cross_size function.
    """
    @abstractmethod
    def trials_per_sample(self):
        pass

    """
    Indicates the number of variables that are present in each trial.

    Analogous to the old __design_size function.
    """
    @abstractmethod
    def variables_per_trial(self):
        pass

    """
    Indicates the number of variables that are present in the core variable grid.
    this does not include variables used to encode complex windows.

    In a design _without_ complex windows, this is equivalent to variables_per_sample.
    """
    @abstractmethod
    def grid_variables(self):
        pass

    """
    Indicates the total number of variables needed to encode the core experiment
    description.

    Alternatively stated, this returns the number of variables in the formula
    that constitute the independent support.
    """
    @abstractmethod
    def variables_per_sample(self):
        pass

    @abstractmethod
    def variables_for_window(self, window: Union[Transition, Window]) -> int:
        pass

    """
    Retrieve a factor by name.
    """
    def get_factor(self, factor_name: str) -> Factor:
        return next(f for f in self.design if f.name == factor_name)


"""
A fully-crossed block. This block generates as many trials as needed to fully
cross all levels across all factors in the block's crossing.
"""
class FullyCrossBlock(Block):
    def __init__(self, design, crossing, constraints, cnf_fn=to_cnf_tseitin):
        super().__init__(design, crossing, constraints, cnf_fn)
        self.__validate()

    def __validate(self):
        # TODO: validation - 'Forbid' constraints aren't allowed with this block type.
        return

    def trials_per_sample(self):
        return reduce(lambda sum, factor: sum * len(factor.levels), self.crossing, 1)

    def variables_per_trial(self):
        # Factors with complex windows are excluded because we don't want variables allocated
        # in every trial when the window spans multiple trials.
        grid_factors = filter(lambda f: not f.has_complex_window(), self.design)
        return sum([len(factor.levels) for factor in grid_factors])

    def grid_variables(self):
        return self.trials_per_sample() * self.variables_per_trial()

    def variables_per_sample(self):
        complex_factors = list(filter(lambda f: f.has_complex_window(), self.design))
        windows = list(map(lambda f: f.levels[0].window, complex_factors))
        window_count = reduce(lambda total, w: total + self.variables_for_window(w), windows, 0)

        return self.grid_variables() + window_count

    def variables_for_window(self, window: Union[Transition, Window]) -> int:
        return self.trials_per_sample() * 2 - window.width

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
