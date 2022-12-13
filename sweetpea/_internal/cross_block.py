"""This module provides the various kinds of blocks that can be used to create
a factorial experimental design.
"""

from abc import abstractmethod
from functools import reduce
from itertools import accumulate, combinations, product, repeat, chain
from typing import List, Union, Tuple, Optional, cast, Any, Dict, Set
from math import ceil
from networkx import has_path

from sweetpea._internal.block import Block
from sweetpea._internal.backend import BackendRequest
from sweetpea._internal.level import get_all_levels
from sweetpea._internal.primitive import (
    DerivedFactor, DerivedLevel, ElseLevel, Factor, SimpleFactor, SimpleLevel, Level
)
from sweetpea._internal.logic import to_cnf_tseitin
from sweetpea._internal.base_constraint import Constraint
from sweetpea._internal.design_graph import DesignGraph
from sweetpea._internal.iter import chunk_list
from sweetpea._internal.weight import combination_weight
from sweetpea._internal.argcheck import argcheck, make_islistof

class MultiCrossBlock(Block):
    """A :class:`.Block` with multiple crossings, meant to be used in
    experiment synthesis. Similar to :func:`fully_cross_block`, except it can
    be configured with multiple crossings.

    :param design:
        A :class:`list` of all the :class:`Factors <.Factor>` in the design.
        When a sequence of trials is generated, each trial will have one level
        from each factor in ``design``.

    :param crossings:
        A :class:`list` of :class:`lists <list>` of :class:`Factors <.Factor>`
        representing crossings. The number of trials in each run of the
        experiment is determined by the *maximum* product among the number of
        levels in the crossings.

        Every combination of levels in each individual crossing in
        ``crossings`` appears at least once. Different crossings can refer to
        the same factors, which constrains how factor levels are chosen across
        crossings.

    :param constraints:
        A :class:`list` of :class:`Constraints <.Constraint>` that restrict the
        generated trials.

    :param require_complete_crossing:
        Whether every combination in ``crossing`` must appear in a block of
        trials. ``True`` by default. A ``False`` value is appropriate if
        combinations are excluded through an :class:`.Exclude`
        :class:`.Constraint`.
    """
    def __init__(self,
                 design: List[Factor],
                 crossings: List[List[Factor]],
                 constraints: List[Constraint],
                 require_complete_crossing: bool = True):
        who = "MultiCrossBlock"
        argcheck(who, design, make_islistof(Factor), "list of Factors for design")
        argcheck(who, crossings, make_islistof(make_islistof(Factor)), "list of list of Factors for crossings")
        argcheck(who, constraints, make_islistof(Constraint), "list of Constraints for constraints")
        self._create(who, design, crossings, constraints, require_complete_crossing)

    def _create(self,
                who: str,
                design: List[Factor],
                crossings: List[List[Factor]],
                constraints: List[Constraint],
                require_complete_crossing: bool):
        from sweetpea._internal.constraint import Cross, Consistency
        from sweetpea._internal.derivation_processor import DerivationProcessor
        design,crossings,replacements = _desugar_factors_with_weights(design, crossings)
        all_constraints = cast(List[Constraint], [Cross(), Consistency()]) + constraints
        all_constraints = _desugar_constraints(all_constraints, replacements) # expand the constraints into a form we can process
        super().__init__(design, crossings, all_constraints, require_complete_crossing, who)
        self.constraints += DerivationProcessor.generate_derivations(self)
        if (not list(filter(lambda c: c.is_complex_for_combinatoric(), self.constraints))
            and not list(filter(lambda f: f.has_complex_window, design))):
            self.complex_factors_or_constraints = False
        self.__validate(who)

    def __validate(self, who: str):
        self.__validate_crossing(who)

    def __validate_crossing(self, who: str):
        dg = DesignGraph(self.design).graph
        warnings = []
        template = " '{}' depends on '{}'"
        for crossing in self.crossings:
            combos = combinations(crossing, 2)

            for c in combos:
                if has_path(dg, c[0].name, c[1].name):
                    warnings.append(template.format(c[0].name, c[1].name))
                elif has_path(dg, c[1].name, c[0].name):
                    warnings.append(template.format(c[1].name, c[0].name))

        if warnings:
            self.errors.add("WARNING: Dependencies among factors may make the"
                            " crossing unsatisfiable:"
                            + reduce(lambda accum, s: accum + "\n" + s, warnings, ""))

    def __trials_required_for_crossing(self, f: Factor, crossing_size: int) -> int:
        """Given a factor ``f``, and a crossing size, this function will
        compute the number of trials required to fully cross ``f`` with the
        other factors.

        For example, if ``f`` is a transition, it doesn't apply to trial 1. So
        when the ``crossing_size`` is ``4``, we'd actually need 5 trials to
        fully cross with ``f``.

        This is a helper for :class:`.MultipleCrossBlock.trials_per_sample`.
        """
        trial = 0
        counter = 0
        while counter != crossing_size:
            trial += 1
            if f.applies_to_trial(trial):
                counter += 1
        return trial

    def _trials_per_sample_for_crossing(self):
        crossing_size = max(map(lambda c: self.crossing_size(c), self.crossings))
        required_trials = list(map(max, list(map(lambda c: list(map(lambda f: self.__trials_required_for_crossing(f, crossing_size),
                                                                    c)),
                                                 self.crossings))))
        return max(required_trials)

    def _trials_per_sample_for_one_crossing(self, c: List[Factor]):
        crossing_size = self.crossing_size(c)
        return max(map(lambda f: self.__trials_required_for_crossing(f, crossing_size), c))

    def trials_per_sample(self):
        if self._trials_per_sample:
            return self._trials_per_sample
        self._trials_per_sample = max([self.min_trials, self._trials_per_sample_for_crossing()])
        return self._trials_per_sample

    def variables_per_trial(self):
        # Factors with complex windows are excluded because we don't want variables allocated
        # in every trial when the window spans multiple trials.
        if self._variables_per_trial:
            return self._variables_per_trial
        grid_factors = filter(lambda f: not f.has_complex_window, self.act_design)
        self._variables_per_trial = sum([len(factor.levels) for factor in grid_factors])
        return self._variables_per_trial

    def grid_variables(self):
        return self.trials_per_sample() * self.variables_per_trial()

    def __count_exclusions(self, crossing):
        """This method is responsible for determining the number of trials that
        should be excluded from the full crossing, based on any
        :class:`Exclude` constraints that the user provides, as well as combinations
        that are impossible based on a derived level's definition. A single
        :class:`Exclude` constraint may prevent multiple crossings, depending
        on the derivation function used.
        """
        from sweetpea._internal.constraint import Exclude

        excluded_crossings = cast(Set[Tuple[Level, ...]], set())

        # Generate the full crossing as a list of tuples.
        levels_lists = [list(f.levels) for f in crossing]
        all_crossings = list(product(*levels_lists))

        # Get the exclude constraints.
        exclusions = list(filter(lambda c: isinstance(c, Exclude), self.constraints))

        # Check for impossible combinations
        for c in all_crossings:
            for l in c:
                if isinstance(l, DerivedLevel):
                    f = l.factor
                    if isinstance(f, DerivedFactor) and not f.has_complex_window:
                        argss = []
                        for af in l.window.factors:
                            if af in crossing:
                                # Find level in `c`:
                                for al in c:
                                    if al in af.levels:
                                        argss.append([al.name])
                                        break
                            else:
                                # We'll need to try all possible levels in `af`
                                argss.append([ll.name for ll in af.levels])
                        all_possible_argss = list(product(*argss))
                        if not any([l.window.predicate(*args) for args in all_possible_argss]):
                            excluded_crossings.add(tuple(c))

        # Check for excluded combinations
        for constraint in exclusions:
            # Retrieve the derivation function that defines this exclusion.
            excluded_level = constraint.level

            if excluded_level.factor in crossing:
                for c in all_crossings:
                    if excluded_level in c:
                        excluded_crossings.add(tuple(c))

            if isinstance(excluded_level, SimpleLevel):
                # nothing more to do
                pass
            elif constraint.factor.has_complex_window:
                # We are not obliged to filter impossible cases for a complex level
                continue
            elif excluded_level.factor not in crossing:
                # For each crossing, ensure that at least one combination is possible with the design-only
                # factor, keeping in mind the exclude contraints.
                for c in all_crossings:
                    if all(map(lambda d: self.__excluded_derived(excluded_level, c+d),
                               list(product(*[list(f.levels) for f in filter(lambda f: f not in crossing,
                                                                             self.act_design)])))):
                        excluded_crossings.add(tuple(c))

        if len(excluded_crossings) != 0:
            if self.require_complete_crossing:
                er = "Complete crossing unsatisfiable"
            else:
                er = "WARNING: crossing incomplete"
            er += " due to excluded or impossible combinations:"
            for c in excluded_crossings:
                names = ', '.join([f"'{l.name}'" for l in c])
                er += "\n " + names
            self.errors.add(er)

        return sum([combination_weight(c) for c in excluded_crossings])

    def __excluded_derived(self, excluded_level, c):
        """Given the complete crossing and an exclude constraint, returns true
        if that combination results in the exclude level or if the combination
        is not possible based on the level's definition.
        """
        ret = []

        cx = {l.factor: l.name for l in c}

        for f in filter(lambda f: isinstance(f, DerivedFactor), excluded_level.window.factors):
            if self.__excluded_derived(cx[f], c):
                return True

        # Invoking the predicate this way is only ok because we only do this for WithinTrial windows.
        # With complex windows, it wouldn't work due to the list aspect for each argument.
        return excluded_level.window.predicate(*[cx[f] for f in excluded_level.window.factors])

    def crossing_size(self, crossing: Optional[List[Factor]] = None):
        """The crossing argument must be one of the block's crossings."""
        if not crossing:
            if len(self.crossings) != 1:
                raise ValueError("Not a single-crossing block, so crossing must be provided to crossing_size")
            crossing = self.crossings[0]
        crossing_size = self.crossing_size_without_exclusions(crossing)
        crossing_size -= self.__count_exclusions(crossing)
        return crossing_size

    def crossing_size_without_exclusions(self, crossing: List[Factor]):
        """The crossing argument must be one of the block's crossings."""
        return reduce(lambda sum, factor: sum * factor.level_weight_sum(), crossing, 1)

    def draw_design_graph(self):
        dg = DesignGraph(self.design)
        dg.draw()

    def factor_in_crossing(self, factor):
        return any(list(map(lambda c: factor in c, self.crossings)))

    def factor_used_in_crossing(self, factor):
        return any(list(map(lambda c: any(list(map(lambda f: f.uses_factor(factor), c))),
                            self.crossings)))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

class CrossBlock(MultiCrossBlock):
    """A fully crossed :class:`.Block` meant to be used in experiment
    synthesis. This is the preferred mechanism for describing an experiment.

    :param design:
        A :class:`list` of all the :class:`Factors <.Factor>` in the design.
        When a sequence of trials is generated, each trial will have one level
        from each factor in ``design``.

    :param crossing:
        A :class:`list` of :class:`Factors <.Factor>` used to produce
        crossings. The number of trials in each run of the experiment is
        determined as the product of the number of levels of factors in
        ``crossing``.

        If ``require_complete_crossing`` is ``False``, the ``constraints`` can
        reduce the total number of trials.

        Different trial sequences of the experiment will have different
        combinations of levels in different orders. The factors in ``crossing``
        supply an implicit constraint that every combination of levels in the
        cross should appear once. Derived factors impose additional
        constraints: only combinations of levels that are consistent with
        derivations can appear as a trial. Additional constraints can be
        manually imposed via the ``constraints`` parameter.

    :param constraints:
        A :class:`list` of :class:`Constraints <.Constraint>` that restrict the
        generated trials.

    :param require_complete_crossing:
        Whether every combination in ``crossing`` must appear in a block of
        trials. ``True`` by default. A ``False`` value is appropriate if
        combinations are excluded through an :class:`.Exclude`
        :class:`.Constraint`.
    """
    def __init__(self,
                 design: List[Factor],
                 crossing: List[Factor],
                 constraints: List[Constraint],
                 require_complete_crossing: bool = True):    
        who = "CrossBlock"
        argcheck(who, design, make_islistof(Factor), "list of Factors for design")
        argcheck(who, crossing, make_islistof(Factor), "list of Factors for crossing")
        argcheck(who, constraints, make_islistof(Constraint), "list of Constraints for constraints")
        self._create(who, design, [crossing], constraints, require_complete_crossing)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~                         Helper functions                            ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _desugar_factors_with_weights(design: List[Factor], crossings: List[List[Factor]]) -> Tuple[List[Factor], List[List[Factor]], dict]:
    # When a derived factor has weighted levels and is in the
    # crossing, then the weight have to be handed by sampling, because
    # it doesn't work to have multiple levels in a derived factor that
    # match the same cases. If a derived factor is not in the
    # crossing, the weights are irrelevnt, because other factors
    # chosen for a combination determine a derived level.
    #
    # For a non-derived factor, weighting is effecively the same as
    # having multiple levels with the same name. Still, as long as a
    # factor with weights is used in the crossing (all of them, in the
    # case of multiple crossings), then we leave the weights in place
    # and handling them in sampling.
    #
    # But when a non-derived factor with weights is not in (all of
    # the) crossing(s), we desugar to a factor with multiple levels
    # that have the same name. That makes the biasing effect of
    # weighting work for formula-based samplers, and it geneally means
    # that samplers do not have to handle the weights specifically.
    #
    # To desugar, we create new factors and levels, and we rewrite all
    # constraints and derived factors to refer to the new ones. Each
    # desugared factor has two replacements: a non-derived factors
    # with the weights turned into multiple levels, and a derived
    # factor that has the same level names as before. The derived
    # factor is needed in case a constraint refers to an weighted
    # level that gets expanded in the non-derived factor.
    #
    # The `replacements` dictionary maps a level to its replacement,
    # and it maps factor to a list of two factors: the derived
    # replacement and non-derived replacement.
    #
    weighted = []
    for f in design:
        if (not isinstance(f, DerivedFactor)) and any([l.weight > 1 for l in f.levels]):
            if all([not f in c for c in crossings]):
                weighted.append(f)
    if not weighted:
        # No desugaring needed
        return (design, crossings, {})
    else:
        # Desugaring needed
        replacements = cast(dict, {})
        for f in weighted:
            # Adds to `replacements`:
            cast(SimpleFactor, f).desugar_weights(replacements)
        for f in design:
            if isinstance(f, DerivedFactor):
                # Uses `replacements`:
                f.desugar_for_weights(replacements)
        # Returned `replacements` is also used for constraint desugaring
        return (list(chain.from_iterable([replacements.get(f, [f]) for f in design])),
                [[replacements.get(f, [f, f])[1] for f in c] for c in crossings],
                replacements)

def _desugar_constraints(constraints: List[Constraint], replacements: dict) -> List[Constraint]:
    desugared_constraints = []
    for c in constraints:
        desugared_constraints.extend(c.desugar(replacements))
    return desugared_constraints
