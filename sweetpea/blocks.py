from abc import abstractmethod
from functools import reduce
from typing import List, Union, Tuple

from sweetpea.internal import get_all_level_names
from sweetpea.primitives import Factor, Transition, Window, get_level_name
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
    def variables_for_factor(self, f: Factor) -> int:
        trial_list = range(1, self.trials_per_sample() + 1)
        return reduce(lambda sum, t: sum + len(f.levels) if f.applies_to_trial(t) else sum, trial_list, 0)

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
    Given a factor and a trial number (1-based) this function will return a list of the variables
    representing the levels of the given factor for that trial. The variable list is also 1 based.
    """
    def factor_variables_for_trial(self, f: Factor, t: int) -> List[int]:
        if not f.applies_to_trial(t):
            raise ValueError('Factor does not apply to trial #' + str(t) + ' f=' + str(f))

        previous_trials = sum(map(lambda trial: 1 if f.applies_to_trial(trial + 1) else 0, range(t))) - 1
        levels = map(get_level_name, f.levels)
        initial_sequence = list(map(lambda l: self.first_variable_for_level(f.name, l), levels))

        offset = 0
        if f.has_complex_window():
            offset = len(f.levels) * previous_trials
        else:
            offset = self.variables_per_trial() * previous_trials

        return list(map(lambda n: n + offset + 1, initial_sequence))


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
                    return tuples[(variable - start) % len(f.levels)]

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
        # TODO: Ensure that no two factors in the crossing share a common ancestor.
        pass

    """
    Given a factor f, and a crossing size, this function will compute the number of trials
    required to fully cross f with the other factors.

    For example, if f is a transition, it doesn't apply to trial 1. So when the crossing_size
    is 4, we'd actually need 5 trials to fully cross with f.

    This is a helper for trials_per_sample.
    """
    def __trials_required_for_crossing(self, f: Factor, crossing_size: int) -> int:
        trial = 0
        counter = 0
        while counter != crossing_size:
            trial += 1
            if f.applies_to_trial(trial):
                counter += 1
        return trial

    def trials_per_sample(self):
        crossing_size = reduce(lambda sum, factor: sum * len(factor.levels), self.crossing, 1)
        required_trials = list(map(lambda f: self.__trials_required_for_crossing(f, crossing_size), self.crossing))
        return max(required_trials)

    def variables_per_trial(self):
        # Factors with complex windows are excluded because we don't want variables allocated
        # in every trial when the window spans multiple trials.
        grid_factors = filter(lambda f: not f.has_complex_window(), self.design)
        return sum([len(factor.levels) for factor in grid_factors])

    def grid_variables(self):
        return self.trials_per_sample() * self.variables_per_trial()

    def crossing_size(self):
        return reduce(lambda sum, factor: sum * len(factor.levels), self.crossing, 1)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
