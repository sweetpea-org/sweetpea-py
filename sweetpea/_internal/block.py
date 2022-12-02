"""This module provides the various kinds of blocks that can be used to create
a factorial experimental design.
"""

from abc import abstractmethod
from functools import reduce
from itertools import accumulate, combinations, product, repeat
from typing import List, Union, Tuple, Optional, cast, Any, Dict, Set
from math import ceil
from networkx import has_path

from sweetpea._internal.backend import BackendRequest
from sweetpea._internal.level import get_all_levels
from sweetpea._internal.primitive import (
    DerivedFactor, DerivedLevel, ElseLevel, Factor, SimpleLevel, Level
)
from sweetpea._internal.logic import to_cnf_tseitin
from sweetpea._internal.base_constraint import Constraint
from sweetpea._internal.design_graph import DesignGraph
from sweetpea._internal.iter import chunk_dict
from sweetpea._internal.weight import combination_weight
from sweetpea._internal.argcheck import argcheck, make_islistof

class Block:
    """Abstract class for Blocks. Contains the required data, and defines
    abstract methods that other blocks _must_ implement in order to work
    correctly.
    """

    def __init__(self,
                 design: List[Factor],
                 crossings: List[List[Factor]],
                 constraints: List[Constraint],
                 require_complete_crossing,
                 who: str) -> None:
        self.design = list(design).copy()
        self.crossings = list(map(lambda c: list(c).copy(), crossings))
        self.constraints = list(constraints).copy()
        self.cnf_fn = to_cnf_tseitin
        self.complex_factors_or_constraints = True
        self.min_trials = cast(int, 0)
        self.exclude = cast(List[Tuple[Factor, Union[SimpleLevel, DerivedLevel]]], [])
        self.excluded_derived = cast(List[Dict[Factor, SimpleLevel]], [])
        self.require_complete_crossing = require_complete_crossing
        self.errors = cast(Set[str], set())
        self.act_design = list(filter(lambda f: not self.factor_is_implied(f), self.design))
        self._trials_per_sample = None
        self._simple_tuples = cast(Optional[List[Tuple[Factor, Union[SimpleLevel, DerivedLevel]]]], None)
        self._variables_per_trial = None
        self.__validate(who)
        self._cached_previous_count = cast(Dict[Tuple[Factor, int], int], {})

    def show_errors(self) -> bool:
        failed = False
        if self.errors:
            for e in self.errors:
                if "WARNING" not in e:
                    print(e)
                    failed = True
            if not failed:
                for e in self.errors:
                    if "WARNING" in e:
                        print(e)
        return failed

    def extract_basic_factor_names(self, level: DerivedLevel) -> set:
        included_factor_names = set()
        for factor in level.window.factors:
            if isinstance(factor, DerivedFactor):
                for l in factor.levels:
                    included_factor_names.update(self.extract_basic_factor_names(l))
            else:
                included_factor_names.add(factor.name)
        return included_factor_names

    def __validate(self, who: str):
        for cr in self.crossings:
            names = set()
            for f in cr:
                if not f in self.design:
                    raise RuntimeError(f"{who}: factor in crossing is not in design: {f}")
                if f.name in names:
                    raise RuntimeError(f"{who}: multiple factors have the same name: {f.name}")
                if f.has_complex_window and cast(DerivedLevel, f.first_level).window.stride > 1:
                    raise RuntimeError(f"{who}: factor with stride > 1 not allowed in crossing: {f.name}")
                names.add(f.name)
        # Ensure basic factors of derived levels in design form complete subset
        # of all declared basic factors.
        basic_factor_names = set()
        included_factor_names = set()
        for design_factor in self.design:
            for level in design_factor.levels:
                if isinstance(level, SimpleLevel):
                    basic_factor_names.add(level.factor.name)
                elif isinstance(level, DerivedLevel):
                    included_factor_names.update(self.extract_basic_factor_names(level))
                else:
                    raise RuntimeError('Expected SimpleLevel or DerivedLevel but found ' + str(type(level)))
        undefined_factor_names = included_factor_names - basic_factor_names
        if undefined_factor_names:
            # The derived levels include factors that are not basic factors.
            raise RuntimeError(f"Derived levels in experiment design include factors that are not listed as basic "
                               f"factors: {', '.join(str(name) for name in undefined_factor_names)}.")
        from sweetpea._internal.constraint import AtLeastKInARow, MinimumTrials
        for c in self.constraints:
            c.validate(self)
            if isinstance(c, MinimumTrials):
                c.apply(self, None)
        for c in self.constraints:
            if isinstance(c, AtLeastKInARow):
                c.max_trials_required = self.trials_per_sample()*c.k

    @abstractmethod
    def trials_per_sample(self):
        """Indicates the number of trials that are generated per sample for
        this block configuration.

        Analogous to the old ``__fully_cross_size`` function.
        """
        pass

    @abstractmethod
    def variables_per_trial(self):
        """Indicates the number of variables that are present in each trial.

        Analogous to the old ``__design_size`` function.
        """
        pass

    @abstractmethod
    def grid_variables(self):
        """Indicates the number of variables that are present in the core
        variable grid. this does not include variables used to encode complex
        windows.

        In a design *without* complex windows, this is equivalent to
        :func:`.Block.variables_per_sample`.
        """
        pass

    def variables_per_sample(self):
        """Indicates the total number of variables needed to encode the core
        experiment description.

        Alternatively stated, this returns the number of variables in the
        formula that constitute the independent support.
        """
        return reduce(lambda sum, f: sum + self.variables_for_factor(f), self.act_design, 0)

    def support_variables(self) -> List[int]:
        """Returns the variables for all non-derived factors for all trials.
        The values of these variables determine the values of all others."""
        vars = []
        for t in range(self.trials_per_sample()):
            for f in self.act_design:
                if not isinstance(f, DerivedFactor):
                    vars += self.factor_variables_for_trial(f, t+1)
        return vars

    def variables_for_factor(self, f: Factor) -> int:
        """Indicates the number of variables needed to encode this factor."""
        trial_list = range(1, self.trials_per_sample() + 1)
        return reduce(lambda sum, t: sum + len(f.levels) if f.applies_to_trial(t) else sum, trial_list, 0)

    def has_factor(self, factor: Factor) -> Factor:
        """Determines whether a given factor is in this block."""
        if not isinstance(factor, Factor):
            raise ValueError('Non-factor argument to has_factor.')
        if factor in self.design:
            return factor
        return cast(Factor, None)

    def first_variable_for_level(self, factor: Factor, level: Any) -> int:
        """Returns the first index for this variable in a trial sequence
        representing the given factor and level. (0-based.)
        """
        if not isinstance(level, (SimpleLevel, DerivedLevel)):
            raise ValueError(f"Attempted to find first variable of non-Level object: {level}.")
        if factor.has_complex_window:
            offset = 0
            complex_factors = filter(lambda f: f.has_complex_window, self.act_design)
            for f in complex_factors:
                if f == factor:
                    offset += f.levels.index(level)
                    break
                else:
                    offset += self.variables_for_factor(f)

            return self.grid_variables() + offset

        else:
            simple_factors = list(filter(lambda f: not f.has_complex_window, self.act_design))
            simple_levels = get_all_levels(simple_factors)
            return simple_levels.index((factor, level))

    def _get_previous_trials_variable_count(self, f: Factor, trial: int):
        """The `trial` argument is 1-based."""
        t = trial
        while True:
            maybe_count = cast(Optional[int], 0)
            if t == 1:
                maybe_count = 0
            else:
                key = (f, t)
                maybe_count = self._cached_previous_count.get(key, None)
            if maybe_count is not None:
                count = maybe_count
                while t < trial:
                    if (f.applies_to_trial(t)):
                        count += 1
                    t += 1
                    self._cached_previous_count[(f, t)] = count
                return count
            t -= 1

    def factor_variables_for_trial(self, f: Factor, t: int) -> List[int]:
        """Given a factor and a trial number (1-based) this function will
        return a list of the variables representing the levels of the given
        factor for that trial. The variable list is also 1-based.
        """
        if not f.applies_to_trial(t):
            raise ValueError('Factor does not apply to trial #' + str(t) + ' f=' + str(f))

        previous_trials = self._get_previous_trials_variable_count(f, t)
        # this could be computed once per factor after self.exclude is in place
        initial_sequence = list(map(lambda l: self.first_variable_for_level(f, l),
                                    list(filter(lambda l: (f, l) not in self.exclude,
                                                f.levels))))
        offset = 0
        if f.has_complex_window:
            offset = len(f.levels) * previous_trials
        else:
            offset = self.variables_per_trial() * previous_trials
        return list(map(lambda n: n + offset + 1, initial_sequence))

    def variable_list_for_trial(self, t: int) -> List[List[int]]:
        """Given a trial number (1-based) this function will return a list of
        lists of the variables that pertain to that trial.

        For example, for stroop-2 with a congruency level, this method would
        return the following for trial ``1``::

          [[1, 2], [3, 4], [5, 6]]

        If a transition were involved, and it didn't apply to level one, then
        the factor would have an empty list::

          [[1, 2], [3, 4], []]
        """
        variables = cast(List[List[int]], [])
        for f in self.act_design:
            # Skip factors that don't apply.
            if not f.applies_to_trial(t):
                variables.append([])
                continue

            variables.append(self.factor_variables_for_trial(f, t))

        return variables
    
    def _encode_variable(self, f: Factor, l: Level, trial: int):
        offset = self.first_variable_for_level(f, l)
        previous_trials = self._get_previous_trials_variable_count(f, trial)
        if f.has_complex_window:
            offset += len(f.levels) * previous_trials
        else:
            offset += self.variables_per_trial() * previous_trials
        return offset+1

    def encode_combination(self, combination: Dict[Factor, Level], trial: int):
        return tuple([self._encode_variable(f, l, trial) for f,l in combination.items()])

    def decode_variable(self, variable: int) -> Tuple[Factor, Union[SimpleLevel, DerivedLevel]]:
        """Given a variable number from the SAT formula, this method will
        return the associated factor and level name.
        """
        # Shift to zero-based index
        variable -= 1

        if variable < self.grid_variables():
            variable = variable % self.variables_per_trial()
            if not self._simple_tuples:
                simple_factors = list(filter(lambda f: not f.has_complex_window, self.act_design))
                self._simple_tuples = get_all_levels(simple_factors)
            assert self._simple_tuples # for the type checker
            return self._simple_tuples[variable]
        else:
            complex_factors = list(filter(lambda f: f.has_complex_window, self.act_design))
            for f in complex_factors:
                start = self.first_variable_for_level(f, f.levels[0])
                end = start + self.variables_for_factor(f)
                if variable in range(start, end):
                    tuples = get_all_levels([f])
                    return tuples[(variable - start) % len(f.levels)]

        raise RuntimeError('Unable to find factor/level for variable!')

    def is_excluded_combination(self, di: Dict[Factor, SimpleLevel]) -> bool:
        """Given a combination of levels, reports whether this combination has been excluded,
        either explicitly or implicitly by the definition of a derived level."""
        # Check based on excluded simple levels:
        if any([t[0] in di and di[t[0]] == t[1] for t in self.exclude]):
            return True
        # Check based on excluded derived levels and derived-level definitions:
        if any([all([e[ex_level] == di.get(ex_level, None) for ex_level in e]) for e in self.excluded_derived]):
            return True
        return False

    def is_excluded_or_inconsistent_combination(self, di: Dict[Factor, SimpleLevel]) -> bool:
        """Like extends is_excluded_combination to also check for combinations that are
        inconsistent with derived-factor definitions. Assumes that `di` is based on the
        block's first crossing.
        """
        if self.is_excluded_combination(di):
            return True
        for f in self.crossings[0]:
            if isinstance(f, DerivedFactor) and not f.has_complex_window and f in di:
                l = cast(DerivedLevel, di[f])
                if all([df in di for df in l.window.factors]):
                    args = [di[df].name for df in l.window.factors]
                    if not l.window.predicate(*args):
                        return True
        return False
    
    def build_backend_request(self) -> BackendRequest:
        """Apply all constraints to build a :class:`.BackendRequest`. Formerly
        known as ``__desugar``.
        """
        fresh = 1 + self.variables_per_sample()
        backend_request = BackendRequest(fresh)

        from sweetpea._internal.constraint import MinimumTrials
        for c in self.constraints:
            if isinstance(c, MinimumTrials):
                continue
            c.apply(self, backend_request)

        return backend_request

    def get_variable(self, trial_number: int, level: Tuple[Factor, Any]) -> int:
        """Given a trial number (1-based), factor, and level, this method will
        return the SAT variable that represents that selection. Only works for
        factors without complex windows at the moment.
        """
        return self._encode_variable(level[0], level[1], trial_number)

    def build_variable_list(self, level_pair: Tuple[Factor, Union[SimpleLevel, DerivedLevel]]) -> List[int]:
        """Given a specific level (factor + level pair), this method will
        return the list of variables that correspond to that level in each
        trial in the encoding.
        """
        factor = level_pair[0]
        level = level_pair[1]
        if not isinstance(factor, Factor):
            raise ValueError("First element in level argument to variable list builder must be a Factor.")
        if not isinstance(level, (SimpleLevel, DerivedLevel)):
            raise ValueError("Second element in level argument to variable list builder must be a SimpleLevel "
                             "or a DERIVED LEVEL.")
        if factor.has_complex_window:
            return self.__build_complex_variable_list(level_pair)
        else:
            return self.__build_simple_variable_list(level_pair)

    def factor_in_crossing(self, factor):
        pass

    def factor_used_in_crossing(self, factor):
        pass

    def factor_is_implied(self, f: Factor) -> bool:
        """Determines whether a factor's level selection is completely implied by level selections
        other factors and is not involved directly in any constraints, so it doesn't have to be
        part of the problem that is passed along to a solver.
        """
        if not isinstance(f, DerivedFactor):
            return False
        if self.factor_used_in_crossing(f):
            return False
        return not any(list(map(lambda c: c.uses_factor(f), self.constraints)))

    def add_implied_levels(self, results: dict) -> dict:
        """Given a dictionary for an experiment that maps all non-implied factors to their levels,
        adds level values for implied factors"""
        n = len(list(results.values())[0])
        for f in self.design:
            if f not in self.act_design:
                vals = []
                for i in range(0, n):
                    if f.applies_to_trial(i+1):
                        for l in f.levels:
                            if isinstance(l, ElseLevel):
                                vals.append(l.name)
                            elif isinstance(l, DerivedLevel):
                                w = l.window
                                args = []
                                for idx, df in enumerate(w.factors):
                                    for j in range(w.width):
                                        shift = w.width - j - 1
                                        if i-shift >= 0:
                                            args.append(results[df.name][i-shift])
                                        else:
                                            args.append(None)
                                if w.width > 1:
                                    args = list(chunk_dict(args, w.width))
                                if w.predicate(*args):
                                    vals.append(l.name)
                            else:
                                raise RuntimeError("unexpected level in implied factor")
                    else:
                        vals.append("")
                results[f.name] = vals
        return results

    def __build_simple_variable_list(self, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]]) -> List[int]:
        first_variable = self.first_variable_for_level(level[0], level[1]) + 1
        design_var_count = self.variables_per_trial()
        num_trials = self.trials_per_sample()
        # TODO: This should be reworked. It's an accumulating fold where the
        #       folding function's second argument is just thrown away.
        return list(accumulate(repeat(first_variable, num_trials), lambda acc, _: acc + design_var_count))

    def __build_complex_variable_list(self, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]]) -> List[int]:
        factor = level[0]
        level_count = len(factor.levels)
        n = self.variables_for_factor(factor) // level_count
        start = self.first_variable_for_level(level[0], level[1]) + 1
        return reduce(lambda l, v: l + [start + (v * level_count)], range(n), [])

    def rearrage_samples(self, samples, results):
        pass

    def calculate_samples_required(self, samples):
        pass
