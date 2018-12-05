from abc import abstractmethod
from functools import reduce
from typing import List, Union, Tuple

from sweetpea.internal import get_all_level_names
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
        # TOOD: Make sure factor names are unique

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
    def variables_per_sample(self):
        return reduce(lambda sum, f: sum + self.variables_for_factor(f), self.design, 0)

    """
    Indicates the number of variables needed to encode this factor.
    """
    def variables_for_factor(self, factor: Factor) -> int:
        variable_count = self.trials_per_sample() * len(factor.levels)
        if factor.has_complex_window():
            variable_count -= len(factor.levels) * (factor.levels[0].window.width - 1)

        return variable_count

    """
    Retrieve a factor by name.
    """
    def get_factor(self, factor_name: str) -> Factor:
        return next(f for f in self.design if f.name == factor_name)

    """
    Returns the first index for this variable in a trial sequence representing the given factor and level.
    (0 based)
    """
    def first_variable_for_level(self, factor_name: str, level_name: str) -> int:
        f = self.get_factor(factor_name)

        if f.has_complex_window():
            offset = 0
            complex_factors = filter(lambda f: f.has_complex_window(), self.design)
            for f in complex_factors:
                if f.name == factor_name:
                    offset += f.levels.index(f.get_level(level_name))
                    break
                else:
                    offset += self.variables_for_factor(f)

            return self.grid_variables() + offset

        else:
            simple_factors = list(filter(lambda f: not f.has_complex_window(), self.design))
            simple_levels = get_all_level_names(simple_factors)
            return simple_levels.index((factor_name, level_name))


    """
    Given a variable number from the SAT formula, this method will return
    the associated factor and level name.
    """
    def decode_variable(self, variable: int) -> Tuple[str, str]:
        # Shift to zero-based index
        variable -= 1

        if variable < self.grid_variables():
            variable = variable % self.variables_per_trial()
            simple_factors = list(filter(lambda f: not f.has_complex_window(), self.design))
            simple_tuples = get_all_level_names(simple_factors)
            return simple_tuples[variable]
        else:
            complex_factors = list(filter(lambda f: f.has_complex_window(), self.design))
            for f in complex_factors:
                start = self.first_variable_for_level(f.name, f.levels[0].name)
                end = start + self.variables_for_factor(f)
                if variable in range(start, end):
                    tuples = get_all_level_names([f])
                    return tuples[(variable - start) % f.levels[0].window.width]

        raise RuntimeError('Unable to find factor/level for variable!')


"""
A fully-crossed block. This block generates as many trials as needed to fully
cross all levels across all factors in the block's crossing.
"""
class FullyCrossBlock(Block):
    def __init__(self, design, crossing, constraints, cnf_fn=to_cnf_tseitin):
        super().__init__(design, crossing, constraints, cnf_fn)
        self.__validate()

    def __validate(self):
        simple_factors = list(filter(lambda f: not f.is_derived(), self.crossing))
        if len(simple_factors) != len(self.crossing):
            raise ValueError('Factors with DerivedLevels are not allowed in the crossing!')

    def trials_per_sample(self):
        return reduce(lambda sum, factor: sum * len(factor.levels), self.crossing, 1)

    def variables_per_trial(self):
        # Factors with complex windows are excluded because we don't want variables allocated
        # in every trial when the window spans multiple trials.
        grid_factors = filter(lambda f: not f.has_complex_window(), self.design)
        return sum([len(factor.levels) for factor in grid_factors])

    def grid_variables(self):
        return self.trials_per_sample() * self.variables_per_trial()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
