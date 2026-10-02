"""This module provides constraints for CNF generation."""

import operator as op
from abc import abstractmethod
from copy import copy, deepcopy
from typing import List, Tuple, Any, Union, cast, Dict, Callable, Optional
from itertools import chain, combinations, product
from math import ceil
import inspect

from sweetpea._internal.base_constraint import Constraint
from sweetpea._internal.iter import chunk, chunk_list
from sweetpea._internal.block import Block, BlockGeometry
from sweetpea._internal.cross_block import MultiCrossBlockRepeat
from sweetpea._internal.backend import LowLevelRequest, BackendRequest
from sweetpea._internal.logic import If, Iff, And, Or, Not, Formula, FormulaWithIff
from sweetpea._internal.primitive import DerivedFactor, DerivedLevel, Factor, Level, SimpleLevel, ContinuousFactor
from sweetpea._internal.argcheck import argcheck, make_istuple, make_islistof
from sweetpea._internal.weight import combination_weight
from sweetpea._internal.beforestart import BeforeStart

def validate_factor(block: Block, factor: Factor) -> None:
    if not block.has_factor(factor):
        raise ValueError(("A factor with name '{}' wasn't found in the design. "
                          "Are you sure the factor was included, and that the name is spelled "
                          "correctly?").format(factor.name))

def validate_factor_and_level(block: Block, factor: Factor, level: Union[SimpleLevel, DerivedLevel]) -> None:
    validate_factor(block, factor)

    if not level in factor:
        raise ValueError(("A level with name '{}' wasn't found in the '{}' factor").format(
                              level.name,
                              factor.name))


class Consistency(Constraint):
    """This constraint ensures that only one level of each factor is 'on' at a
    time. So for instance in the experiment::

        color = Factor("color", ["red", "blue"])
        text  = Factor("text",  ["red", "blue"])
        design = crossing = [color, text, conFactor]
        experiment   = fully_cross_block(design, crossing, [])

    The first trial is represented by the boolean vars ``[1, 2, 3, 4]``:

    - 1 is true iff the trial is color:red
    - 2 is true iff the trial is color:blue
    - 3 is true iff the trial is text:red
    - 4 is true iff the trial is text:blue

    The second trial is represented by the boolean vars ``[5-8]``, the third by
    ``[9-12]``, the fourth by ``[13-16]``. So this desugaring applies the
    following constraints::

        sum(1, 2) EQ 1
        sum(3, 4) EQ 1
        sum(5, 6) EQ 1
        ...
        sum(15, 16) EQ 1
    """

    def validate(self, block: Block) -> None:
        pass

    @staticmethod
    def apply(block: Block, backend_request: BackendRequest) -> None:
        next_var = 1
        for _ in range(block._trials_per_sample()):
            for f in filter(lambda f: not f.has_complex_window, block.act_design):
                number_of_levels = len(f.levels)
                new_request = LowLevelRequest("EQ", 1, list(range(next_var, next_var + number_of_levels)))
                backend_request.ll_requests.append(new_request)
                next_var += number_of_levels

        for f in filter(lambda f: f.has_complex_window, block.act_design):
            variables_for_factor = block.variables_for_factor(f)
            var_list = list(map(lambda n: n + next_var, range(variables_for_factor)))
            chunks = list(chunk_list(var_list, len(f.levels)))
            backend_request.ll_requests += list(map(lambda v: LowLevelRequest("EQ", 1, v), chunks))
            next_var += variables_for_factor

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        # conformance by construction in combinatoric
        return True

class Cross(Constraint):
    """We represent the fully crossed constraint by allocating additional
    boolean variables to represent each unique state. Only factors in crossing
    will contribute to the number of states (there may be factors in the design
    that aren't in the crossing).

    Continuing with the example from :class:`.Consistency`, we will represent
    the states::

        (color:red, text:red)
        (color:red, text:blue)
        (color:blue, text:red)
        (color:blue, text:blue)

    The steps taken are:

    1. Generate intermediate vars

        Using the fresh var counter, allocate ``numTrials * num_states`` new
        vars

    2. Entangle them with block vars

        Add to the CNF queue: ``toCNF(Iff(newVar, And(levels)))``, e.g., if the
        variable ``1`` indicates ``color:red``, the var ``3`` indicates
        ``text:red``, and the var ``25`` represents ``(color:red, text:red)``,
        do ``toCNF(Iff(25, And([1, 3])))``

    3. 1 hot the *states* e.g., 1 red circle, etc

        Same as :class:`.Consistency` above, collect all the state vars that
        represent each state & enforce that only one of those states is true,
        e.g., ``sum(25, 29, 33, 37) EQ 1`` (and 3 more of these for each of the
        other states).
    """

    def validate(self, block: Block) -> None:
        pass

    @staticmethod
    def apply(block: MultiCrossBlockRepeat, backend_request: BackendRequest) -> None:
        # Treat each crossing seperately, but they're related by shared variables, which
        # are the per-trial, per-level variables of factors used in multiple crossings
        for c in block.crossings:
            fresh = backend_request.fresh

            crossing_size = block.crossing_size(c)
            preamble_size = block.preamble_size(c)
            crossing_weight = block.crossing_weight(c)

            # Step 1a: Get a list of the trials that are involved in the crossing. That list
            # omits leading trials that will be present to initialize transitions, and the
            # number of trials may have been reduced by exclusions.
            crossing_trials = list(range(1+preamble_size, block._trials_per_sample() + 1))

            # Step 1b: For each trial, cross all levels of all factors in the crossing.
            # We exclude any combination that is dsiallowed by implicit or explicit exlcusions.
            level_lists = [list(f.levels) for f in c]
            crossings = [{level.factor: level for level in levels} for levels in product(*level_lists)]
            trial_combinations = list(filter(lambda c: not block.is_excluded_or_inconsistent_combination(c), crossings))
            crossing_combinations = [[block.encode_combination(c, t) for c in trial_combinations] for t in crossing_trials]
            # Each trial is now represented in `crossing_factors` by a list
            # of potential level combinations, where each level combination is represented
            # as tuple of CNF variables.

            # Step 2a: Allocate additional variables to represent each crossing in each trial.
            num_state_vars = len(crossing_trials) * len(crossing_combinations[0])
            state_vars = list(range(fresh, fresh + num_state_vars))
            fresh += num_state_vars

            # Step 2b: Associate each state variable with its combination in each trial.
            flattened_combinations = list(chain.from_iterable(crossing_combinations))
            iffs = list(map(lambda n: Iff(state_vars[n], And([*flattened_combinations[n]])), range(len(state_vars))))

            # Step 2c: Get weight associated with each combination.
            sustain_count = block.sustain_count(c[0])
            combination_weights = [combination_weight(tuple(c.values())) * sustain_count for c in trial_combinations]

            # Step 3: Constrain each crossing to occur exactly according to its weight time the
            # crossing weight in each `crossing_size * crossing_weight` set of trials, or at most
            # that much in a last set of trials that is less than `crossing_size * crossing_weight`
            # in length.
            states = list(chunk(state_vars, len(trial_combinations)))
            transposed = cast(List[List[int]], list(map(list, zip(*states))))
            reqss = map(lambda l, w: Cross.__add_weight_constraint(l, w, crossing_size, crossing_weight),
                        transposed,
                        combination_weights)
            backend_request.ll_requests += list(chain.from_iterable(reqss))

            (cnf, new_fresh) = block.cnf_fn(And(iffs), fresh)

            backend_request.cnfs.append(cnf)
            backend_request.fresh = new_fresh

    @staticmethod
    def __add_weight_constraint(variables: List[int],
                                weight: int,
                                crossing_size: int,
                                crossing_weight: int) -> List[LowLevelRequest]:
        """Constrain to a weight of each `crossing_size` sequence of variables, and at
        at most one for an ending sequence that is less than `crossing_size` in length.
        """
        to_add = len(variables)
        reqs = cast(List[LowLevelRequest], [])
        while to_add > 0:
            if (to_add >= (crossing_size * crossing_weight)):
                reqs.append(LowLevelRequest("EQ", weight*crossing_weight, variables[:(crossing_size*crossing_weight)]))
            else:
                reqs.append(LowLevelRequest("LT", weight*crossing_weight+1, variables))
            variables = variables[(crossing_size*crossing_weight):]
            to_add -= crossing_size * crossing_weight
        return reqs

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        # conformance by construction or direct checking in combinatoric
        return True

class Sustain(Constraint):
    """A sustain constraint forces consecutive trials to have the same variable assignments"""

    def validate(self, block: Block) -> None:
        pass

    @staticmethod
    def apply(block: MultiCrossBlockRepeat, backend_request: BackendRequest) -> None:
        iffs = []
        for f in block.design:
            sustain_count = block.sustain_count(f)
            for l in f.levels:
                varss = block.build_variable_lists((f, cast(Union[SimpleLevel, DerivedLevel], l)), None)
                for vars in list(varss):
                    for i in range(0, len(vars)):
                        same_as_i = (i // sustain_count) * sustain_count
                        iffs.append(Iff(vars[i], vars[same_as_i]))

        (cnf, new_fresh) = block.cnf_fn(And(iffs), backend_request.fresh)
        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        for f in block.design:
            sustain_count = block.sustain_count(f)
            if sustain_count > 1:
                levels = sample[f]
                for i in range(0, len(levels), sustain_count):
                    if f.applies_to_trial(i//sustain_count + 1):
                        level = levels[i]
                        for j in range(1, sustain_count):
                            if levels[i+j] != level:
                                return False
        return True

class Derivation(Constraint):
    """A derivation such as::

        Derivation(4, [[0, 2], [1, 3]])

    where the index of the derived level is ``4``, and ``[[0, 2], [1, 3]]`` is
    the list of dependent indices, represents the logical formula::

        4 iff (0 and 2) or (1 and 3)

    These indicies are used the get the corresponding trial variables.
    Continuing from the example in of processDerivations, the first trial is
    represented by variables ``[1-6]`` (notice this feels like an off-by-one:
    the indicies start from ``0``, but the boolean variables start from ``1``).
    So we would use the indices to map onto the vars as::

        5 iff (1 and 3) or (2 and 4)

    Then we convert to CNF directly, i.e.::

        toCNF(Iff(5, Or(And(1,3), And(2,4))))

    This is then done for all window-sizes, taking into account strides (which
    are specified only in :class:`DerivedLevels <.DerivedLevel>` specified with
    a general :class:`.Window` rather than :class:`.Transition` or
    :class:`.WithinTrial`). We grab window-sized chunks of the variables that
    represent the trials, map the variables using the indices, and then convert
    to CNF. These chunks look like::

        window1: 1  2  3  4  5  6
        window2: 7  8  9  10 11 12

    So, for the second trial (since the window size in this example is ``1``)
    it would be::

        11 iff (7 and 9) or (8 and 10)

    When a dependent_idx has `BeforeStart`, then it should only apply early
    where the corresponding level is not available.

    90% sure this is the correct way to generalize to derivations involving 2+
    levels & various windowsizes. One test is the experiment::

        color = ["r", "b", "g"];
        text = ["r", "b"];
        conFactor;
        fullycross(color, text) + AtMostKInARow 1 conLevel
    """

    def __init__(self,
                 derived_idx: int,
                 dependent_idxs: List[List[object]],
                 factor: DerivedFactor) -> None:
        self.derived_idx = derived_idx
        self.dependent_idxs = dependent_idxs # sustain count is built into these indices
        self.factor = factor
        # TODO: validation

    def validate(self, block: Block) -> None:
        pass

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        if self.is_complex(block):
            self.__apply_derivation(block, backend_request)
        else:
            # If the index is beyond the grid variables, that means it's a derivation from a complex window.
            # (This is brittle, but I haven't come up with a better way yet.)
            self.__apply_derivation_with_complex_window(block, backend_request)

    def is_complex(self, block: Block):
        return self.derived_idx < block.grid_variables()

    def __apply_derivation(self, block: Block, backend_request: BackendRequest) -> None:
        trial_size = block.variables_per_trial()
        cross_size = block._trials_per_sample()

        iffs = []
        for n in range(cross_size):
            or_clause = Or(list(And(list(map(lambda x: x + (n * trial_size) + 1, l))) for l in self.dependent_idxs))
            iffs.append(Iff(self.derived_idx + (n * trial_size) + 1, or_clause))

        (cnf, new_fresh) = block.cnf_fn(And(iffs), backend_request.fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def __apply_derivation_with_complex_window(self, block: Block, backend_request: BackendRequest) -> None:
        trial_size = block.variables_per_trial()
        trial_count = block._trials_per_sample()
        iffs = []
        f = self.factor
        sustain_count = block.sustain_count(f)
        window = f.levels[0].window
        t = 0
        delta = window.start_delta * sustain_count
        for n in range(0, trial_count, sustain_count):
            if not f.applies_to_trial(n//sustain_count + 1):
                continue
            num_levels = len(f.levels)
            get_trial_size = lambda x: trial_size if x < block.grid_variables() else len(block.decode_variable(x+1)[0].levels)

            # Only keep clauses where all `BeforeStarts` apply and all indices are in range:
            ands = []
            for l in self.dependent_idxs:
                vars = cast(List[int], [])
                ok = True
                for x in l:
                    if isinstance(x, BeforeStart):
                        if x.ready_at <= n:
                            ok = False
                            break
                    else:
                        new_x = x + ((t + delta) * window.stride * get_trial_size(x) + 1)
                        if new_x <= 0:
                            ok = False
                            break
                        vars.append(new_x)
                if ok:
                    ands.append(And(vars))

            or_clause = Or(ands)
            iffs.append(Iff(self.derived_idx + (t * num_levels) + 1, or_clause))
            t += sustain_count
        (cnf, new_fresh) = block.cnf_fn(And(iffs), backend_request.fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def uses_factor(self, f: Factor) -> bool:
        return any(list(map(lambda l: l.uses_factor(f), self.factor.levels)))

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        return True


class _KInARow(Constraint):
    #: How `k` moves to weaken this constraint: +1 raises it, -1 lowers it.
    #: Zero means the solver loop cannot step it.
    weaken_step = 0

    def __init__(self, k, level):
        self.k = k
        self.level = level
        self.within_block = cast(Optional[BlockGeometry], None)
        # Set by `Relax`; None means the constraint is binding.
        self.relaxation = cast(Optional['_Relaxation'], None)
        self.__validate()

    def __validate(self) -> None:
        who = self.__class__.__name__

        if not isinstance(self.k, int):
            raise ValueError(f"{who}: k must be an integer, received {self.k}")

        if self.k <= 0:
            raise ValueError(f"{who}: k must be greater than 0; if you're trying to exclude a particular level, "
                             f"use the 'Exclude' constraint")

        self.level = filter_level(who, self.level, True)

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.level.get_factor(), self.level)

    def init_within_block(self, within_block: BlockGeometry) -> None:
        if self.within_block is None:
            self.within_block = within_block

    def set_within_block(self, within_block: BlockGeometry) -> None:
        self.within_block = within_block

    def sustain_within_block(self, sustain_count: int) -> None:
        self.within_block = self.within_block.sustain(sustain_count)
 
    def uses_factor(self, f: Factor) -> bool:
        if isinstance(self.level, Factor):
            return self.level.uses_factor(f)
        else:
            return self.level.factor.uses_factor(f)

    def desugar(self, replacements: dict) -> List[Constraint]:
        constraints = cast(List[Constraint], [self])

        level = replacements.get(self.level, self.level)

        # Generate the constraint for each level in the factor.
        if isinstance(level, Factor):
            levels = level.levels  # Get the actual levels out of the factor.

            constraints = []
            for l in levels:
                constraint_copy = deepcopy(self)
                constraint_copy.level = l
                constraints.append(constraint_copy)
        elif level != self.level:
            constraint_copy = deepcopy(self)
            constraint_copy.level = level
            constraints = [constraint_copy]

        return constraints

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        # By this point, level should be a level tht has a factor.
        # Block construction is expected to flatten out constraints applied to whole factors so
        # that the constraint is applied to each level of the factor.
        self.apply_to_backend_request(block, (self.level.factor, self.level), backend_request)

    def _build_variable_sublistss(
        self,
        block: Block,
        level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
        sublist_length: int
    ) -> List[List[List[int]]]:
        # If window-scoped, we operate over fixed-size windows; otherwise we
        # use the original (global or repeat-scoped) behavior.

        var_lists = block.build_variable_lists(level, self.within_block)

        sublistss: List[List[List[int]]] = []
        for var_list in var_lists:
            raw = [var_list[i:i + sublist_length] for i in range(0, len(var_list))]
            sublistss.append([sl for sl in raw if len(sl) == sublist_length])

        return sublistss

    @abstractmethod
    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], backend_request: BackendRequest) -> None:
        pass

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        level = self.level
        factor = level.factor
        level_list = sample[factor]

        def check_sequence(start: int, end: int) -> bool:
            counts = []
            count = 0
            for i in range(start, end):
                l = level_list[i]
                if count > 0 and l != level:
                    counts.append(count)
                    count = 0
                elif l == level:
                    count += 1
            if count > 0:
                counts.append(count)
            return self._potential_counts_conform(counts)

        return all(block.map_block_trial_ranges(self.within_block, check_sequence))

    @abstractmethod
    def _potential_counts_conform(self, counts: List[int]) -> bool:
        pass

    def _potential_counts_conform_individually(self, counts: List[int], fn: Callable[[int, int], bool]) -> bool:
        return all(map(lambda n: fn(n, self.k), counts))


class AtMostKInARow(_KInARow):
    """This desugars pretty directly into the llrequests. The only thing to do
    here is to collect all the boolean vars that match the same level & pair
    them up according to k.

    Continuing with the example from :class:`.Consistency`, say we want
    ``AtMostKInARow 1 ("color", "red")``, then we need to grab all the vars
    which indicate color-red::

        [1, 7, 13, 19]

    and then wrap them up so that we're making requests like::

        sum(1, 7)  LT 2
        sum(7, 13)  LT 2
        sum(13, 19) LT 2

    If it had been ``AtMostKInARow 2 ("color", "red")``, the reqs would have
    been::

        sum(1, 7, 13)  LT 3
        sum(7, 13, 19) LT 3
    """
    # Longer runs are the weaker requirement.
    weaken_step = 1

    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], backend_request: BackendRequest) -> None:
        sublistss = self._build_variable_sublistss(block, level, self.k + 1)
        # Build the requests
        for sublists in sublistss:
            backend_request.ll_requests += list(map(lambda l: LowLevelRequest("LT", self.k + 1, l), sublists))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return self._potential_counts_conform_individually(counts, op.le)


class AtLeastKInARow(_KInARow):
    """This is more complicated that AtMostKInARow. We collect all the boolean
    vars that match the same level & pair them up according to k.

    We want ``AtLeastKInARow 2 ("color", "red")``, then we need to grab all the
    vars which indicate color-red::

        [1, 7, 13, 19]

    and then wrap them up in CNF as follows::

        If(1) Then (7)          --------This is a corner case
        If(And(!1, 7)) Then (13)
        If(And(!7, 13)) Then (19)
        If(19) Then (13)   --------This is a corner case

    If it had been ``AtLeastKInARow 3 ("color", "red")``, the CNF would have
    been::

        If(1) Then (7, 13)          --------This is a corner case
        If(And(!1, 7)) Then (13, 19)
        If(19) Then (7, 13)   --------This is a corner case
    """
    # Shorter runs are the weaker requirement.
    weaken_step = -1

    def __init__(self, k, levels):
        super().__init__(k, levels)
        self.max_trials_required = cast(int, None)

    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                    backend_request: BackendRequest) -> None:

        # Request sublists for k+1 to allow us to determine the transition
        var_lists = block.build_variable_lists(level, self.within_block)
        sublistss = self._build_variable_sublistss(block, level, self.k + 1)
        implications = cast(List[FormulaWithIff], [])
        for var_list, sublists in zip(var_lists, sublistss):
            if not sublists:
                # No window of k+1 trials fits, so there is no transition to
                # find: a run of k can only be the whole stretch. The level
                # therefore fills every trial or none of them, and none at all
                # when the stretch is shorter than k.
                if len(var_list) < self.k:
                    implications.extend(Not(v) for v in var_list)
                else:
                    implications.extend(Iff(var_list[0], v) for v in var_list[1:])
                continue
            # Starting corner case
            implications.append(If(sublists[0][0], And(sublists[0][1:-1])))
            for sublist in sublists:
                implications.append(If(And([Not(sublist[0]), sublist[1]]), And(sublist[2:])))
            # Ending corner case
            implications.append(If(Not(sublists[-1][1]), Not(Or(sublists[-1][2:]))))

        (cnf, new_fresh) = block.cnf_fn(And(implications), backend_request.fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return self._potential_counts_conform_individually(counts, op.ge)


class _Relaxation:
    """How far a constraint's `k` may be adjusted, and what it was adjusted to.

    `by` is a budget in the same units as the `k` it accompanies: the value may
    land anywhere in [k - by, k + by]. `original_k` records what the user wrote,
    so that re-sizing a block measures the budget from there rather than from an
    already-widened value --- `_KInARow.desugar` returns the constraint itself
    when its level needs no replacement, so the object a repair mutates is often
    the one the user still holds."""

    def __init__(self, by: int) -> None:
        self.by = by
        self.original_k = cast(Optional[int], None)
        self.applied_k = cast(Optional[int], None)
        # What asked for the change, for the report; None until one applies.
        self.applied_for = cast(Optional[str], None)

    def base_k(self, k: int) -> int:
        """The value the budget is measured from: what the user wrote."""
        return self.original_k if self.original_k is not None else k

    def permits(self, k: int, candidate: int) -> bool:
        return abs(candidate - self.base_k(k)) <= self.by

    def scale(self, sustain_count: int) -> None:
        """Follow `k` when a block sustains it. A budget counts the same
        occurrences `k` does, so whatever multiplies one multiplies the other."""
        self.by *= sustain_count
        if self.original_k is not None:
            self.original_k *= sustain_count
        if self.applied_k is not None:
            self.applied_k *= sustain_count

    def __eq__(self, other):
        return isinstance(other, _Relaxation) and self.__dict__ == other.__dict__

    def __repr__(self):
        return "by={}".format(self.by)


class _CapConflict(Exception):
    """The ExactlyK caps a coverage sizing pass needs widened, each paired with
    its relaxation and the value it must take.

    Raised only for caps that `Relax` authorized, so that the caller can repair
    and re-run the sizing; an unauthorized cap raises `ValueError` where it is
    found instead."""

    def __init__(self, deficits) -> None:
        super().__init__("cap conflict")
        self.deficits = deficits


class ExactlyK(_KInARow):
    """Requires that if the given level exists at all, it must exist in a trial
    exactly ``k`` times.
    """
    def apply_to_backend_request(self,
                                 block: Block,
                                 level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                 backend_request: BackendRequest
                                 ) -> None:
        sublistss = block.build_variable_lists(level, self.within_block)

        for sublists in sublistss:
            backend_request.ll_requests.append(LowLevelRequest("EQ", self.k, sublists))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return sum(counts) == self.k

    def init_within_block(self, within_block: BlockGeometry) -> None:
        super().init_within_block(within_block)

    def sustain_within_block(self, sustain_count: int) -> None:
        super().sustain_within_block(sustain_count)
        self.k *= sustain_count
        if self.relaxation is not None:
            self.relaxation.scale(sustain_count)


def Relax(constraint: Constraint, by: int) -> Constraint:
    """Authorizes `constraint` to be weakened by up to `by`, when it would
    otherwise leave the design with no solution. Returns a copy to use in place
    of the original, which is left unchanged.

    `by` is a budget of steps towards the weaker requirement: a larger `k` for
    :class:`.AtMostKInARow`, a smaller one for :class:`.AtLeastKInARow`, and
    either direction for :class:`.ExactlyK`, where neither is weaker.

    Weakening is never inferred: only a constraint passed through this function
    is eligible, and any adjustment applied is reported as the block is built or
    as trials are synthesized, and again alongside the results. An experiment may
    relax one constraint.

    An :class:`.ExactlyK` is repaired while the block is sized, where
    :class:`.CoverAllCombinations` can compute the value it must take. The
    in-a-row constraints have no such model, so they are stepped only after the
    solver reports the design unsatisfiable.

    Usage::

        CrossBlock(design, crossing, [CoverAllCombinations(color, word),
                                      Relax(ExactlyK(3, (word, 'red')), by=1)])
        CrossBlock(design, crossing, [Relax(AtMostKInARow(2, (color, 'red')), by=1)])
    """
    who = "Relax"
    # Named here rather than at module level because LatinSquare is defined
    # further down. ExactlyK is repaired while the block is sized; the rest are
    # stepped only after the solver reports no solution.
    relaxable = (ExactlyK, AtMostKInARow, AtLeastKInARow, LatinSquare)
    if not isinstance(constraint, relaxable):
        raise ValueError((who,
                          "only {} can be relaxed, received {}"
                          .format(", ".join(c.__name__ for c in relaxable),
                                  type(constraint).__name__)))
    # bool is a subclass of int, and `by=True` is a units mistake, not a budget.
    if not isinstance(by, int) or isinstance(by, bool):
        raise ValueError((who, "by must be an integer, received {}".format(by)))
    if by <= 0:
        raise ValueError((who, "by must be greater than 0"))
    # A copy, so that a constraint the caller holds is not altered by wrapping
    # it. Shallow: a deep copy would clone the level, and with it the factor,
    # leaving the constraint pointing at a factor the design does not contain.
    relaxed = copy(constraint)
    relaxed.relaxation = _Relaxation(by)
    return relaxed


def record_concessions(block) -> None:
    """Restate every concession from the block's own state.

    Derived rather than accumulated, so that a constraint changed over several
    passes is reported at its final value, and so that no kind of concession
    overwrites another's entries."""
    messages = []
    for ct in block.constraints:
        if isinstance(ct, _KInARow) and ct.relaxation is not None \
                and ct.relaxation.applied_k is not None:
            rl = ct.relaxation
            messages.append(
                "{} for '{} {}' relaxed from {} to {}, as {}."
                .format(type(ct).__name__, ct.level.factor.name, ct.level.name,
                        rl.original_k, rl.applied_k, rl.applied_for))
        elif isinstance(ct, LatinSquare) and ct.may_release:
            messages.append(
                "Latin square let up to {} participant(s) leave the pattern, as the "
                "solver found no solution otherwise.".format(ct.may_release))
        elif isinstance(ct, CoverAllCombinations) and ct.dropped:
            given_up = ct.optional[len(ct.optional) - ct.dropped:]
            messages.append(
                "Coverage gave up {}: each of their levels appears at least "
                "once, as the solver found no solution otherwise."
                .format(", ".join(str(f.name) for f in given_up)))
    block.applied_relaxations = messages


def solver_relaxable(block):
    """The block's `Relax`-authorized constraint that the solver loop can step,
    or None. An `ExactlyK` has no step: coverage sizing already repaired it, so
    it never reaches the loop."""
    for c in block.constraints:
        if isinstance(c, _KInARow) and c.relaxation is not None and c.weaken_step:
            return c
    return None


def relax_budget(constraint) -> int:
    """Steps the loop may take. `k` must stay positive, so lowering it stops at
    1 however large the authorized budget is."""
    by = constraint.relaxation.by
    return by if constraint.weaken_step > 0 else min(by, constraint.k - 1)


class ExactlyKInARow(_KInARow):
    """Requires that if the given level exists at all, it must exist in a
    sequence of exactly K.
    """
    def apply_to_backend_request(self,
                                 block: Block,
                                 level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                 backend_request: BackendRequest
                                 ) -> None:
        sublistss = self._build_variable_sublistss(block, level, self.k)
        implications = []

        for sublists in sublistss:
            # Handle the regular cases (1 => 2 ^ ... ^ n ^ ~n+1)
            trim = len(sublists) if self.k > 1 else len(sublists) - 1
            for idx, l in enumerate(sublists[:trim]):
                if idx > 0:
                    p_list = [Not(sublists[idx-1][0]), l[0]]
                    p = And(p_list) if len(p_list) > 1 else p_list[0]
                else:
                    p = l[0]

                if idx < len(sublists) - 1:
                    q_list = cast(List[Any], l[1:]) + [Not(sublists[idx+1][-1])]
                    q = And(q_list) if len(q_list) > 1 else q_list[0]
                else:
                    q = And(l[1:]) if len(l[1:]) > 1 else l[self.k - 1]
                implications.append(If(p, q))

            # Handle the tail: if the last element is ON, the previous one must be ON.
            last_run = sublists[-1]
            if len(last_run) > 1:
                tail = list(reversed(last_run))  # [last, ..., first]
                for i in range(len(tail) - 1):
                    implications.append(If(tail[i], tail[i + 1]))

            (cnf, new_fresh) = block.cnf_fn(And(implications), backend_request.fresh)
            backend_request.cnfs.append(cnf)
            backend_request.fresh = new_fresh

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return self._potential_counts_conform_individually(counts, op.eq)


class ExactlyKMultipleInARow(_KInARow):
    def apply_to_backend_request(
        self,
        block: Block,
        level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
        backend_request: BackendRequest
    ) -> None:
    
        k = self.k
        max_len = block._trials_per_sample()
        implications: List[Any] = [] 
        var_lists = block.build_variable_lists(level, self.within_block)
        all_trial_vars = var_lists[0]  # assume non-blocked design for now

        selector_runs: List[Tuple[int, List[int]]] = []  # (selector_var, covered_indices)

        def encode_segment(segment_vars: List[int]) -> None:
            """Encode 'ON runs must have length ∈ {k, 2k, 3k, ...}' within this segment only."""
            max_len = len(segment_vars)
            if max_len == 0:
                return

            implications: List[Any] = []
            selector_runs: List[Tuple[int, List[int]]] = []  # (selector_var, covered_indices)

            # 1) selectors for all multiples of k within this segment
            for run_len in range(k, max_len + 1, k):
                for start in range(0, max_len - run_len + 1):
                    run_indices = list(range(start, start + run_len))
                    sel_var = backend_request.fresh
                    backend_request.fresh += 1
                    selector_runs.append((sel_var, run_indices))
                    implications.append(If(sel_var, And([all_trial_vars[i] for i in run_indices])))
                    after = start + run_len
                    if after < max_len:
                        implications.append(If(sel_var, Not(all_trial_vars[after])))

            # 2) Ensure every active trial is covered by some selector
            for i in range(max_len):
                covering = [sel for (sel, idxs) in selector_runs if i in idxs]
                if covering:
                    implications.append(If(segment_vars[i], Or(covering)))

            # 3) prevent overlaps
            for i, (sel_a, idxs_a) in enumerate(selector_runs):
                set_a = set(idxs_a)
                for j in range(i + 1, len(selector_runs)):
                    sel_b, idxs_b = selector_runs[j]
                    if set_a.intersection(idxs_b):
                        implications.append(Or([Not(sel_a), Not(sel_b)]))

            if implications:
                cnf, backend_request.fresh = block.cnf_fn(And(implications), backend_request.fresh)
                backend_request.cnfs.append(cnf)

        # Build lists (not repeat-scoped for window behavior)
        base_var_lists = block.build_variable_lists(level, within_block=self.within_block)
        
        for var_list in base_var_lists:
            encode_segment(var_list)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return all(c % self.k == 0 for c in counts)


def filter_level(who, level, factor_ok: bool = False):
    if factor_ok and isinstance(level, Factor):
        return level
    elif isinstance(level, Level):
        if hasattr(level, 'factor'):
            return level
        raise ValueError(f"{who}: level does not belong to a factor: {level}")
    elif isinstance(level, tuple) and len(level) == 2 and isinstance(level[0], Factor):
        if isinstance(level[1], SimpleLevel) or isinstance(level[1], DerivedLevel):
            if level[1] not in level[0]:
                raise ValueError(f"{who}: level {level[0]} is not in factor {level[1]}")
            return level[1]
        else:
            l = level[0].get_level(level[1])
            if not l:
                raise ValueError(f"{who}: not a level in factor {level[0]}: {level[1]}")
            return l
    else:
        if factor_ok:
            raise ValueError(f"{who}: expected either a Factor, Level, or a tuple of Factor and Level, given {level}")
        else:
            raise ValueError(f"{who}: expected either a Level or a tuple of Factor and Level, given {level}")

class Exclude(Constraint):
    def __init__(self, level):
        level = filter_level("Exclude", level)
        self.factor = level.factor
        self.level = level

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.factor, self.level)

        block.exclude.append((self.factor, self.level))
        # Store the basic factor-level combnations resulting in the derived excluded factor in the block
        if isinstance(self.level, DerivedLevel) and not self.factor.has_complex_window:
            block.excluded_derived.extend(self.extract_simplelevel(block, self.level))

    def uses_factor(self, f: Factor) -> bool:
        return self.factor.uses_factor(f)

    def desugar(self, replacements: dict) -> List:
        level = replacements.get(self.level, self.level)
        return [Exclude(level)]

    def extract_simplelevel(self, block: Block, level: DerivedLevel) -> List[Dict[Factor, SimpleLevel]]:
        """Recursively deciphers the excluded level to a list of combinations
        basic levels."""
        excluded_levels = []
        excluded: List[Tuple[Level, ...]] = [cross for cross in level.get_dependent_cross_product()
                                             if level.window.predicate(*[level.name for level in cross])]
        for excluded_level_tuple in excluded:
            combos: List[Dict[Factor, SimpleLevel]] = [{}]
            for excluded_level in excluded_level_tuple:
                if isinstance(excluded_level, DerivedLevel):
                    result = self.extract_simplelevel(block, excluded_level)
                    newcombos = []
                    valid = True
                    for r in result:
                        for c in combos:
                            for f in c:
                                if f in r:
                                    if c[f] != r[f]:
                                        valid = False
                        if valid:
                            newcombos.append({**r, **c})
                    combos = newcombos
                else:
                    if not isinstance(excluded_level, SimpleLevel):
                        raise ValueError(f"Unexpected level type in exclusion: level {level.name} of type "
                                         f"{type(level).__name__}.")
                    for c in combos:
                        if block.factor_in_crossing(excluded_level.factor) and block.require_complete_crossing:
                            block.errors.add("WARNING: Some combinations have been excluded, this crossing may not be complete!")
                        c[excluded_level.factor] = excluded_level
            excluded_levels.extend(combos)
        return excluded_levels

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        var_lists = block.build_variable_lists((self.factor, self.level))
        for var_list in var_lists:
            backend_request.cnfs.append(And(list(map(lambda n: n * -1, var_list))))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def is_complex_for_combinatoric(self) -> bool:
        return False

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        # conformance by construction in combinatoric for simple factors, but
        # we have to check exlcusions based on complex factors
        #if self.factor.has_complex_window:
        levels = sample[self.factor]
        level = self.level
        for l in levels:
            if l == level:
                return False
        return True

class Pin(Constraint):
    def __init__(self, index, level):
        level = filter_level("Pin", level)
        self.index = index
        self.factor = level.factor
        self.level = level
        self.within_block = cast(Optional[BlockGeometry], None)

    def init_within_block(self, within_block: BlockGeometry) -> None:
        if self.within_block is None:
            self.within_block = within_block

    def set_within_block(self, within_block: BlockGeometry) -> None:
        self.within_block = within_block

    def sustain_within_block(self, sustain_count: int) -> None:
        if self.within_block:
            self.within_block = self.within_block.sustain(sustain_count)

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.factor, self.level)
        if not block.get_trial_numbers(self.factor, self.index):
            num_trials = block._trials_per_sample()
            block.errors.add("WARNING: Pin constraint unsatisfiable, because "
                             + str(self.index) + " is out of range for " + str(num_trials) + " trials")

    def uses_factor(self, f: Factor) -> bool:
        return self.factor.uses_factor(f)

    def desugar(self, replacements: dict) -> List:
        level = replacements.get(self.level, self.level)
        p = Pin(self.index, level)
        p.within_block = self.within_block
        return [p]

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        trial_nos = block.get_trial_numbers(self.factor, self.index, self.within_block)
        if trial_nos:
            for trial_no in trial_nos:
                var = block.get_variable(trial_no+1, (self.factor, self.level))
                backend_request.cnfs.append(And([var]))
        else:
            backend_request.cnfs.append(And([1, -1]))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def is_complex_for_combinatoric(self) -> bool:
        return True

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        levels = sample[self.factor]
        trial_nos = block.get_trial_numbers(self.factor, self.index, self.within_block)
        if trial_nos:
            for trial_no in trial_nos:
                if levels[trial_no] != self.level:
                    return False
            return True
        else:
            return False

class Reify(Constraint):
    """The only purpose of this constraint is to make a factor
    non-implied, so that it's exposed to a constraint solver."""
    def __init__(self, factor):
        self.factor = factor

    def validate(self, block: Block) -> None:
        validate_factor(block, self.factor)

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        """Do nothing."""

    def uses_factor(self, f: Factor) -> bool:
        return self.factor.uses_factor(f)

    def is_complex_for_combinatoric(self) -> bool:
        return False

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        return True

    def desugar(self, replacements: dict) -> List:
        factor = replacements.get(self.factor, [self.factor, self.factor])[1]
        return [Reify(factor)]


class MinimumTrials(Constraint):
    def __init__(self, trials):
        self.trials = trials
        who = "MinimumTrials"
        argcheck(who, trials, int, "an integer")
        # TODO: validation

    def is_complex_for_combinatoric(self) -> bool:
        return False

    def validate(self, block: Block) -> None:
        if self.trials <= 0 and not isinstance(self.trials, int):
            raise ValueError("Minimum trials must be a positive integer.")

    def apply(self, block: Block, backend_request: Union[BackendRequest, None]) -> None:
        if block.min_trials:
            block.min_trials = max([block.min_trials, self.trials])
        else:
            block.min_trials = self.trials

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        return True

    def sustain_within_block(self, sustain_count: int) -> None:
        self.trials *= sustain_count


class ContinuousConstraint(Constraint):
    """This is the class for continuous constraint. 
    Users need to define the continuous factor and the required constraint function for those factors when initializing
    continuous constraints. This is only used to check continuous sampling. 
    """
    def __init__(self, factors, constraint_function):
        self.factors = factors
        self.constraint_function = constraint_function
        who = "ContinuousConstraint"
        # argcheck(who, factors, List[ContinuousFactor], "continuous factors")
        for f in self.factors: 
            if not isinstance(f, ContinuousFactor):
                raise ValueError(f"{who}: expected continuous factor, given {f}")
        #argcheck(who, constraint_function, Callable, "constraint function")
        if not isinstance(constraint_function, Callable):
            raise ValueError(f"{who}: expected constraint function, given {constraint_function}")
        # TODO: validation

    def validate(self, block: Block) -> None:
        sig = inspect.signature(self.constraint_function)
        num_params = len(sig.parameters)
        if len(self.factors ) != num_params:
            raise RuntimeError("The number of factors in the continuous constraint does not match the function for the constraint")
        for f in self.factors:
            if f not in block.continuous_factors:
                raise RuntimeError("Continuous factor {} not defined in the design".format(f))


    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
    # def validate(self, block: Block) -> None:
    #     if self.trials <= 0 and not isinstance(self.trials, int):
    #         raise ValueError("Minimum trials must be a positive integer.")

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        return True

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        """Do nothing."""

class LatinSquare(Constraint):
    """
    Given a permutation factor and an inner single-crossing block, pin each window
    (length = preamble + crossing_size) to the permutation chosen by the factor.
    """
    def __init__(self,
                 factors: List[Factor],
                 name: Optional[str] = None):
        who = "LatinSquare"
        if factors == []:
            raise ValueError(who, "factor list must be non-empty")
        argcheck(who, factors, make_islistof(Factor), "factors")
        self.factors = factors
        self.within_block = cast(Optional[BlockGeometry], None)
        self.name = name
        # Set by `Relax`; None means every participant is held to the pattern.
        self.relaxation = cast(Optional[_Relaxation], None)
        # How many participants may leave the pattern. Which ones is the
        # solver's choice: releasing by position would have to give up every
        # participant after a conflict in order to reach it.
        self.may_release = 0

    def can_release(self) -> bool:
        return self.relaxation is not None and self.may_release < self.relaxation.by

    def release_one(self) -> int:
        """Allow one more participant out of the pattern."""
        self.may_release += 1
        return self.may_release

    def validate(self, block: Block) -> None:
        who = "LatinSquare"
        for f in self.factors:
            validate_factor(block, f)
        sustain_count = block.sustain_count(self.factors[0])
        preamble_size = block.factor_preamble_size(self.factors[0])
        for f in self.factors:
            if block.sustain_count(f) != sustain_count:
                raise ValueError(who, "inconsistent sustain counts for factors")
            if block.factor_preamble_size(f) != preamble_size:
                raise ValueError(who, "inconsistent preamble sizes for factor")
            if f.level_weight_sum() != len(f.levels):
                raise ValueError(who, "weighted levels not currently supported")

    def uses_factor(self, f: Factor) -> bool:
        for factor in self.factors:
            if factor.uses_factor(f):
                return True
        return False

    def desugar(self, replacements: dict) -> List:
        c = LatinSquare([replacements.get(f, [f, f])[1] for f in self.factors],
                        self.name)
        # The copy is what the block holds and what a release mutates, so the
        # authorization has to travel with it.
        c.relaxation = self.relaxation
        c.may_release = self.may_release
        return [c]

    def _make_rotations(self):
        return [0 for f in self.factors]

    def _step_rotations(self, rotations, main_factor_idx):
        k = len(self.factors) - 1
        while k >= 0:
            if k != main_factor_idx:
                rotations[k] += 1
                if rotations[k] < len(self.factors[k].levels):
                    break
                else:
                    rotations[k] = 0
            k = k - 1

    def diagonal_length(self):
        return max([len(f.levels) for f in self.factors])
                
    def _get_shape(self):
        diagonal_length = self.diagonal_length()
        main_factor_idx = 0
        for idx, f in enumerate(self.factors):
            if len(f.levels) == diagonal_length:
                main_factor_idx = idx
        return (diagonal_length, main_factor_idx)

    def _rotation_cycle(self):
        """Every rotation the odometer visits before it repeats, in order. Its
        length is how many participants a whole pattern takes."""
        (_, main_factor_idx) = self._get_shape()
        start = self._make_rotations()
        rotations = self._make_rotations()
        cycle = []
        while True:
            cycle.append(list(rotations))
            self._step_rotations(rotations, main_factor_idx)
            if rotations == start:
                return cycle

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        if len(self.factors) == 1:
            return

        (diagonal_length, main_factor_idx) = self._get_shape()

        level_lists = [list(f.levels) for f in self.factors]
        sustain_count = block.sustain_count(self.factors[0])
        preamble_size = block.factor_preamble_size(self.factors[0])
        num_trials = block._trials_per_sample()
        main_factor = self.factors[main_factor_idx]

        cycle = self._rotation_cycle()

        # One shift for the whole experiment: participant s takes rotation
        # s + shift of the cycle. Participants still take consecutive rotations
        # and still exhaust the cycle before it repeats; only where the cycle
        # starts is left open, which is otherwise settled by the order the
        # levels happen to be declared in.
        shifts = []
        for _ in cycle:
            shifts.append(backend_request.fresh)
            backend_request.fresh += 1
        backend_request.ll_requests.append(LowLevelRequest("EQ", 1, shifts))

        ands = cast(List[FormulaWithIff], [])
        # One per participant: true when it is let out of the pattern.
        released = []
        i = preamble_size
        segment = 0
        while i < num_trials:
            out = backend_request.fresh
            backend_request.fresh += 1
            released.append(out)
            for shift, shift_var in enumerate(shifts):
                rotations = cycle[(segment + shift) % len(cycle)]
                # For each trial in the segment:
                for j in range(0, diagonal_length):
                    if i+j < num_trials:
                        # Each possible choice of the main factor determines
                        # the other factors
                        for k in range(0, diagonal_length):
                            l = main_factor.levels[(k + rotations[main_factor_idx]) % len(main_factor.levels)]
                            main_var = block.get_variable(i+j+1, (main_factor, l))
                            for idx, f in enumerate(self.factors):
                                if idx != main_factor_idx:
                                    l = f.levels[(k + rotations[idx]) % len(f.levels)]
                                    var = block.get_variable(i+j+1, (f, l))
                                    ands.append(If(And([shift_var, main_var]), Or([out, var])))

            # Each main-factor level at most once in each segment that is held.
            # Pairwise rather than a cardinality request, which cannot be made
            # to depend on `out`.
            for l in main_factor.levels:
                vars = []
                for j in range(0, diagonal_length):
                    if i+j < num_trials:
                        var = block.get_variable(i+j+1, (main_factor, l))
                        vars.append(var)
                for a, b in combinations(vars, 2):
                    ands.append(Or([out, Not(a), Not(b)]))

            segment += 1

            i += diagonal_length * sustain_count

        if released:
            backend_request.ll_requests.append(
                LowLevelRequest("LT", self.may_release + 1, released))

        (cnf, new_fresh) = block.cnf_fn(And(ands), backend_request.fresh)
        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        if len(self.factors) == 1:
            return True
        cycle = self._rotation_cycle()
        return any(len(self._strays(lambda f, t: sample[f][t].name, block, cycle, shift))
                   <= self.may_release for shift in range(len(cycle)))

    def released_participants(self, experiment: dict, block: Block) -> List[int]:
        """The participants in a synthesized experiment whose trials do not
        follow the pattern. A released participant that happens to land on its
        diagonal anyway did follow it, so it is not listed."""
        if len(self.factors) == 1:
            return []
        cycle = self._rotation_cycle()
        return min((self._strays(lambda f, t: experiment[f.name][t], block, cycle, shift)
                    for shift in range(len(cycle))), key=len)

    def _strays(self, level_name, block: Block, cycle, shift) -> List[int]:
        """Participants that break the pattern when the cycle starts at `shift`.
        `level_name(factor, trial)` reads a sample in whichever form it comes."""
        (diagonal_length, main_factor_idx) = self._get_shape()
        sustain_count = block.sustain_count(self.factors[0])
        num_trials = block._trials_per_sample()
        main_factor = self.factors[main_factor_idx]
        names = [l.name for l in main_factor.levels]

        strays = []
        i = block.factor_preamble_size(self.factors[0])
        segment = 0
        while i < num_trials:
            rotations = cycle[(segment + shift) % len(cycle)]
            trials = [i + j for j in range(diagonal_length) if i + j < num_trials]
            mains = [level_name(main_factor, t) for t in trials]
            follows = len(set(mains)) == len(mains) and all(
                level_name(f, t) == f.levels[(names.index(m) + rotations[idx]) % len(f.levels)].name
                for t, m in zip(trials, mains)
                for idx, f in enumerate(self.factors))
            if not follows:
                strays.append(segment)
            segment += 1
            i += diagonal_length * sustain_count
        return strays

    def derivable_factors(self, block: Block) -> Tuple[List[Factor], List[Factor]]:
        (diagonal_length, main_factor_idx) = self._get_shape()
        return (self.factors[:main_factor_idx] + self.factors[main_factor_idx+1:],
                [self.factors[main_factor_idx]])

class Sequential(Constraint):
    """Constraint that ensures that the levels of a trial are used by trails in order.

    Usage::

        Sequential(factor)
    """

    def __init__(self, factor: Factor):
        who = "Sequential"
        argcheck(who, factor, Factor, "factor")
        self.factor = factor

        # We could allow the levels to be specified, but then we have to check and
        # deal with weights on levels. Let's leave that until it seems to be needed,
        # since we can otherwise deal with desugared factors

    def validate(self, block: Block) -> None:
        who = "Sequential"
        validate_factor(block, self.factor)
        if self.factor.level_weight_sum() != len(self.factor.levels):
            raise ValueError(who, "weighted levels not currently supported")

    def uses_factor(self, f: Factor) -> bool:
        return self.factor.uses_factor(f)

    def desugar(self, replacements: dict) -> List[Constraint]:
        factor = replacements.get(self.factor, [self.factor, self.factor])[1]
        return [Sequential(factor)]

    def is_complex_for_combinatoric(self) -> bool:
        return True

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        sustain_count = block.sustain_count(self.factor)
        preamble_size = block.factor_preamble_size(self.factor)
        num_trials = block._trials_per_sample()
        f = self.factor
        
        i = preamble_size
        ands = cast(List[Formula], [])
        while i < num_trials:
            # For each trial in the segment:
            use_l = f.levels[((i - preamble_size) //sustain_count) % len(f.levels)]
            for l in f.levels:
                var = block.get_variable(i+1, (f, l))
                if l is use_l:
                    ands.append(var)
                else:
                    ands.append(Not(var))
            i += sustain_count
        (cnf, new_fresh) = block.cnf_fn(And(ands), backend_request.fresh)
        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        sustain_count = block.sustain_count(self.factor)
        preamble_size = block.factor_preamble_size(self.factor)
        num_trials = block._trials_per_sample()
        f = self.factor

        i = preamble_size
        while i < num_trials:
            # For each trial in the segment:
            use_l = f.levels[(i - preamble_size) % len(f.levels)]
            if not sample[self.factor][i] is use_l:
                return False
            i += sustain_count

        return True

    def __eq__(self, other):
        return (isinstance(other, Sequential) and
                self.factor == other.factor)

    def __repr__(self):
        return f"Sequential({self.factor.name})"

    def derivable_factors(self, block: Block) -> Tuple[List[Factor], List[Factor]]:
        return ([self.factor], [])

def _val_name(x):
    # Works for Level objects or plain strings
    return getattr(x, "name", x)


class CoverAllCombinations(Constraint):
    """Requires that the trials of an experiment collectively include every realizable
    combination of `factors` at least once, plus a weaker requirement for each
    factor named in `optional`.

    Factors left out of a crossing are otherwise assigned freely by the solver; this
    constraint coordinates those free choices so that the union of all trials covers
    every combination. The number of trials needed is computed automatically and the
    block is grown to fit (see the auto-sizing notes on the block constructors).

    The two groups carry different guarantees. The positional `factors` must
    appear in combination with one another---every combination of their levels.
    A factor named in `optional` needs only each of its own levels to appear
    somewhere, in no particular combination, which trades coverage for a shorter
    experiment. A factor may not be in both groups.

    Usage::

        Nest(outer, inner, [CoverAllCombinations(color, word)])
        CrossBlock(design, crossing, [CoverAllCombinations(color, word)])
        CrossBlock(design, crossing, [CoverAllCombinations(color, word,
                                                           optional=[cue])])
    """

    def __init__(self, *factors, optional=[]):
        who = "CoverAllCombinations"
        required = list(factors)
        argcheck(who, required, make_islistof(Factor), "factors")
        # Checked before list(), so that a non-iterable (e.g. a stray boolean)
        # reports the parameter by name instead of raising from the conversion.
        argcheck(who, optional, make_islistof(Factor), "optional")
        self.required = required
        self.optional = cast(List[Factor], [])
        for f in optional:
            if f in required:
                raise ValueError((who,
                                  "'{}' is both required and optional; a factor belongs "
                                  "to one group or the other".format(f.name)))
            if f not in self.optional:
                self.optional.append(f)
        # Every factor the constraint governs, whichever guarantee it carries.
        self.factors = self.required + self.optional
        if self.factors == []:
            raise ValueError(who, "factor list must be non-empty")
        # How many optional factors have been given up so far.
        self.dropped = 0
        self.groups = self._grouping_after(0)
        # Set by Nest during construction: the inner block whose crossing determines
        # which listed factors are pinned vs. free. None for other block types, in
        # which case the attached block itself is analyzed.
        self._inner_block = cast(Optional[MultiCrossBlockRepeat], None)

    def _grouping_after(self, dropped: int) -> List[List[Factor]]:
        """Coverage requirements once `dropped` optional factors have been given
        up, last in the list first.

        A factor still kept is crossed with the others, so their combinations
        must all appear. A factor given up forms a group of its own, which asks
        only that each of its own levels appears somewhere."""
        keep_count = len(self.optional) - dropped
        kept = self.required + self.optional[:keep_count]
        return (cast(List[List[Factor]], [kept] if kept else [])
                + [[f] for f in self.optional[keep_count:]])

    def drop_one(self) -> Factor:
        """Give up the last optional factor still kept, and report it."""
        self.dropped += 1
        self.groups = self._grouping_after(self.dropped)
        return self.optional[len(self.optional) - self.dropped]

    def can_drop(self) -> bool:
        return self.dropped < len(self.optional)

    # ~~~~~~~~~~~~~~ Coverage analysis (the "K" computation) ~~~~~~~~~~~~~~

    def _analysis_block(self, block):
        """The block whose crossing structure determines pinned vs. free listed
        factors: the inner block for a Nest, otherwise the attached block itself."""
        return self._inner_block if self._inner_block is not None else block

    def _cell_crossing(self, block):
        """The crossing whose cells form one instance "pass": the first crossing
        that pins a listed factor, or the largest crossing when none does."""
        for c in block.crossings:
            if any(f in c for f in self.factors):
                return c
        if block.crossings:
            return max(block.crossings, key=len)
        return None

    def _cell_factors(self, block):
        c = self._cell_crossing(block)
        return list(c) if c is not None else []

    def _combo_is_impossible(self, block, di) -> bool:
        """Whether a combination is unrealizable: excluded, or inconsistent with
        the definition of a derived factor in the combination. (Unlike
        ``Block.is_excluded_or_inconsistent_combination``, checks every derived
        factor present, not just those in the block's first crossing.)"""
        if block.is_excluded_combination(di):
            return True
        for f in di:
            if isinstance(f, DerivedFactor) and not f.has_complex_window:
                l = di[f]
                if isinstance(l, DerivedLevel) and all(wf in di for wf in l.window.factors):
                    args = [di[wf].name for wf in l.window.factors]
                    if not l.window.predicate(*args):
                        return True
        return False

    def _coverage_analysis(self, block, factors, exclusion_block=None):
        """Structural analysis over `factors` (one coverage group) for the given
        analysis block. When `exclusion_block` is given (e.g. the merged block of
        a Nest), its exclusions are folded into realizability as well, so that an
        Exclude at any level simply removes combinations from the required set.

        Returns ``(R, forced, R_free, slots, combo_levels, slot_weights,
        forced_weights)`` where:

        - ``R``: realizable listed-factor combos, each a tuple of
          ``(factor_name, level_name)`` pairs in `self.factors` order;
        - ``forced``: combos guaranteed in *every* instance by the crossing
          (cells where the listed factors are fully pinned);
        - ``R_free``: ``R - forced``, the combos that must be placed in free slots;
        - ``slots``: for each free crossing cell, the set of ``R_free`` combos it
          can instantiate (a "slot-type");
        - ``combo_levels``: maps each combo to its ``{factor: level}`` dict (for CNF);
        - ``slot_weights``: parallel to ``slots``, each cell's combination weight —
          a weight-w cell appears w times per instance, giving w picks;
        - ``forced_weights``: per forced combo, its occurrences per instance
          (sum of the combination weights of the cells that force it).
        """
        listed = factors
        crossing_factors = self._cell_factors(block)
        if not crossing_factors:
            return (set(), set(), set(), [], {}, [], {})
        listed_free = [f for f in listed if f not in crossing_factors]
        crossing_level_lists = [list(f.levels) for f in crossing_factors]
        free_level_lists = [list(f.levels) for f in listed_free]
        free_assignments = list(product(*free_level_lists)) if listed_free else [()]

        R = set()                      # type: set
        forced = set()                 # type: set
        forced_weights = {}            # type: Dict[tuple, int]
        slot_sets = []                 # type: List[set]
        slot_set_weights = []          # type: List[int]
        combo_levels = {}              # type: Dict[tuple, Dict[Factor, Any]]
        for cell in product(*crossing_level_lists):
            di_cell = {crossing_factors[i]: cell[i] for i in range(len(crossing_factors))}
            cand = set()
            for fa in free_assignments:
                di = dict(di_cell)
                for j, f in enumerate(listed_free):
                    di[f] = fa[j]
                if self._combo_is_impossible(block, di):
                    continue
                if (exclusion_block is not None and exclusion_block is not block
                        and exclusion_block.is_excluded_combination(di)):
                    continue
                combo = tuple((f.name, di[f].name) for f in listed)
                cand.add(combo)
                if combo not in combo_levels:
                    combo_levels[combo] = {f: di[f] for f in listed}
            if not cand:
                continue
            R |= cand
            if len(cand) == 1:
                combo = next(iter(cand))
                forced.add(combo)
                forced_weights[combo] = forced_weights.get(combo, 0) + combination_weight(cell)
            else:
                slot_sets.append(cand)
                slot_set_weights.append(combination_weight(cell))
        R_free = R - forced
        slots = []                     # type: List[set]
        slot_weights = []              # type: List[int]
        for s, w in zip(slot_sets, slot_set_weights):
            s2 = s & R_free
            if s2:
                slots.append(s2)
                slot_weights.append(w)
        return (R, forced, R_free, slots, combo_levels, slot_weights, forced_weights)

    def required_instances(self, block=None):
        """Minimum number of instances (K) needed to cover ``R_free``, over the
        largest of the coverage groups."""
        if block is None:
            block = self._inner_block
        k = 1
        for group in self.groups:
            (_, _, R_free, slots, _, slot_weights, _) = \
                self._coverage_analysis(block, group)
            k = max(k, self._min_instances(R_free, slots, slot_weights))
        return k

    def _relevant_constraints(self, sizing_block):
        """The sizing block's constraints that are statically reconciled into the
        coverage model: Pins and (global) ExactlyK / Sequential on listed factors.
        Ordering constraints (the in-a-row family) and LatinSquare are left to the
        SAT solver, which remains the final arbiter."""
        listed = set(self.factors)
        pins = []          # type: List[Pin]
        caps = []          # type: List[ExactlyK]
        seqs = []          # type: List[Sequential]
        for ct in sizing_block.constraints:
            if isinstance(ct, Pin) and ct.factor in listed:
                pins.append(ct)
            elif isinstance(ct, ExactlyK) and not isinstance(ct.level, Factor) \
                    and ct.level.factor in listed:
                caps.append(ct)
            elif isinstance(ct, Sequential) and ct.factor in listed:
                seqs.append(ct)
        return (pins, caps, seqs)

    @staticmethod
    def _cap_demand(ct, k, R_free, forced, forced_weights) -> int:
        """The occurrences an ExactlyK's level is driven to at `k` instances:
        each forced combination at its per-instance weight, plus one for each
        free combination that contains the level.

        Only the forced term grows with `k`, so `k` = 1 gives the floor across
        every instance count, and a larger `k` always demands at least as much."""
        fname, lname = ct.level.factor.name, ct.level.name
        forced_l = sum(forced_weights.get(c, 1) for c in forced if (fname, lname) in c)
        free_l = sum(1 for c in R_free if (fname, lname) in c)
        return k * forced_l + free_l

    def _feasible_at(self, k, instance_len, R_free, forced, slots, pins, caps,
                     seq_free, sizing_block, slot_weights=None, forced_weights={}):
        """Whether coverage is achievable with `k` instances, once the statically
        modeled constraint effects are folded in jointly."""
        # A cap's demand grows with k, so feasibility is NOT monotone in k —
        # which is why the caller scans k linearly instead of binary-searching.
        # `caps` carries only the binding caps; ones that `Relax` authorized are
        # reconciled by the caller against the K the scan settles on.
        for ct in caps:
            if self._cap_demand(ct, k, R_free, forced, forced_weights) > ct.k:
                return False
        if seq_free:
            return self._positional_feasible(k, instance_len, R_free, seq_free,
                                             sizing_block)
        # Pins on listed factors conservatively consume one free pick each:
        # modeled as dummy combos that any slot can serve.
        dummies = ["_pin{}".format(i) for i in range(len(pins))]
        combos = list(R_free) + dummies
        slots_ext = [s | set(dummies) for s in slots]
        return self._feasible(combos, slots_ext, k, slot_weights)

    def _positional_feasible(self, k, instance_len, R_free, seq_free, sizing_block):
        """Coverage feasibility when a Sequential pins a listed free factor to a
        value per trial position. Each post-preamble position can host at most
        one required combo, and only combos whose sequential-factor values match
        that position. (Cell-per-position exclusivity is relaxed; the solver
        arbitrates residual conflicts.)"""
        T = k * instance_len
        pos_sets = []
        for pos in range(T):
            allowed = {}
            for ct in seq_free:
                # Sequential holds each level for `sus` trials then advances,
                # wrapping around — so the level at `pos` is fully determined.
                f = ct.factor
                sus = sizing_block.factor_to_sustain_count.get(f, 1)
                allowed[f.name] = f.levels[(pos // sus) % len(f.levels)].name
            s = set(c for c in R_free
                    if all(dict(c).get(fn) == ln for fn, ln in allowed.items()))
            pos_sets.append(s)
        return self._feasible(list(R_free), pos_sets, 1)

    def autosize_trials(self, block) -> int:
        """Total trials `block` needs for coverage, or 0 when no static sizing
        applies (the block then keeps its user-specified size and the SAT solver
        arbitrates).

        Runs the K-search over the joint model: propose an instance count K,
        fold in the statically modeled effects of the block's other constraints,
        grow K until the capacitated matching covers the required set (or a cap
        is hit). Provably-impossible coverage raises a construction-time error
        naming the conflict. The resulting trial count is rounded up so that
        every crossing of `block` keeps complete passes (e.g. a Nest's outer
        crossing stays balanced when K is not a multiple of its size).
        """
        who = "CoverAllCombinations"
        analysis = self._analysis_block(block)
        if analysis is not block and not all(analysis.has_factor(f) for f in self.factors):
            # Nest with a listed factor outside the inner block: not statically modeled.
            return 0
        cell_crossing = self._cell_crossing(analysis)
        if cell_crossing is None:
            return 0
        # Listed factors crossed outside the cell crossing aren't statically modeled.
        for c in analysis.crossings:
            if c is not cell_crossing and any(f in c for f in self.factors):
                return 0
        (pins, caps, seqs) = self._relevant_constraints(block)
        if analysis is not block:
            # Nest: one instance = one inner-block pass.
            instance_len = analysis._trials_per_sample() - analysis.common_preamble_size()
        else:
            # crossing_size already folds in the crossing's sustain count.
            instance_len = block.crossing_size(cell_crossing)
        if instance_len <= 0:
            return 0
        # Sequential enrichment applies to listed factors the cells leave free.
        cell_factors = self._cell_factors(analysis)
        seq_free = [ct for ct in seqs if ct.factor not in cell_factors]
        # Each group is sized on its own and the block takes the largest K: one
        # trial serves one combination from every group at once, so the groups
        # do not add up. A priority list only ever produces groups that are
        # disjoint in the factors the cells leave free, so the per-group counts
        # are independent and the largest is exact rather than a lower bound.
        k = 1
        for group in self.groups:
            k = max(k, self._instances_for_group(block, analysis, group, instance_len,
                                                 pins, caps, seq_free, who))
        total = k * instance_len
        # Round up to complete passes of every crossing. Iterating settles on a
        # common multiple; the iteration bound avoids chasing a large LCM when
        # pass lengths are co-prime. crossing_size already folds in sustain.
        passes = [block.crossing_size(c) for c in block.crossings]
        for _ in range(4):
            rounded = total
            for p in passes:
                if p > 0 and rounded % p != 0:
                    rounded = ((rounded // p) + 1) * p
            if rounded == total:
                break
            total = rounded
        return total

    def _instances_for_group(self, block, analysis, group, instance_len,
                             pins, caps, seq_free, who) -> int:
        """Instances (K) needed for one coverage group, with the statically
        modeled effects of the block's other constraints folded in.

        The ExactlyK arithmetic here counts one group's requirements. Across
        several groups it therefore under-counts a level's total demand; the
        residual is left to the solver, as the in-a-row family and LatinSquare
        already are."""
        (R, forced, R_free, slots, _, slot_weights, forced_weights) = \
            self._coverage_analysis(analysis, group, exclusion_block=block)
        binding = []
        relaxable = []
        for ct in caps:
            rl = ct.relaxation
            if rl is None:
                binding.append(ct)
            else:
                relaxable.append((ct, rl))
        # Definitive check: a cap below the K=1 demand (see _cap_demand) can be
        # reconciled at no instance count at all, so it fails here rather than
        # after a scan that cannot succeed.
        for ct in binding:
            required = self._cap_demand(ct, 1, R_free, forced, forced_weights)
            if required > ct.k:
                raise ValueError((who,
                                  "covering all combinations requires at least {} trials "
                                  "with '{} {}' but an ExactlyK constraint allows exactly "
                                  "{}".format(required, ct.level.factor.name,
                                              ct.level.name, ct.k)))
        k_opt = self._min_instances(R_free, slots, slot_weights)
        # Scan ceiling: |R_free| instances provably suffice for the plain model
        # (see _min_instances), so twice that (or twice k_opt) leaves headroom
        # for what constraints consume; exhausting it => irreconcilable.
        cap = max(len(R), k_opt) * 2
        k = k_opt
        while k <= cap:
            if self._feasible_at(k, instance_len, R_free, forced, slots, pins, binding,
                                 seq_free, block, slot_weights, forced_weights):
                # The scan rises from the floor, so this is the smallest feasible
                # K, and since demand grows with K it is also the K that asks the
                # least of the relaxable caps.
                deficits = []
                for (ct, rl) in relaxable:
                    demand = self._cap_demand(ct, k, R_free, forced, forced_weights)
                    # Demand under the cap is no conflict: the model counts a
                    # minimum, and the solver can reach the equality using the
                    # occurrences the crossing leaves free.
                    if demand > ct.k:
                        deficits.append((ct, rl, demand))
                if deficits:
                    raise _CapConflict(deficits)
                return k
            k += 1
        conflicting = [repr(ct) for ct in (pins + caps + seq_free)]
        raise ValueError((who,
                          "no trial count up to {} instances reconciles coverage with "
                          "the other constraints ({})".format(cap, ", ".join(conflicting))))

    def reconcile_trials(self, block) -> int:
        """`autosize_trials`, plus the widening that `Relax` authorizes.

        `autosize_trials` stays a pure computation so that this can re-run it
        after each repair: a widened cap changes the coverage model, so sizing
        is recomputed rather than patched.

        Every pass either returns or raises some cap by at least one, and every
        budget is finite, so the authorized slack bounds the number of passes."""
        who = "CoverAllCombinations"
        for _ in range(self._relaxation_budget(block) + 1):
            try:
                total = self.autosize_trials(block)
            except _CapConflict as conflict:
                for (ct, rl, needed) in conflict.deficits:
                    if not rl.permits(ct.k, needed):
                        raise ValueError((who,
                                          "covering all combinations requires {} trials "
                                          "with '{} {}', but the ExactlyK constraint allows "
                                          "{} and Relax authorizes a change of only {}"
                                          .format(needed, ct.level.factor.name,
                                                  ct.level.name, rl.base_k(ct.k), rl.by)))
                    if rl.original_k is None:
                        rl.original_k = ct.k
                    rl.applied_k = needed
                    rl.applied_for = "{} requires".format(repr(self))
                    ct.k = needed
                continue
            self._record_relaxations(block)
            return total
        raise ValueError((who,
                          "coverage sizing did not settle after applying every "
                          "authorized relaxation"))

    @staticmethod
    def _relaxation_budget(block) -> int:
        """Total slack `Relax` authorized across the block's ExactlyK caps."""
        total = 0
        for ct in block.constraints:
            if isinstance(ct, ExactlyK) and ct.relaxation is not None:
                total += ct.relaxation.by
        return total

    @staticmethod
    def _record_relaxations(block) -> None:
        record_concessions(block)

    def sizing_message(self, total) -> str:
        """The line a block reports as it sizes itself for coverage. Named
        factors are the ones already given up, so nothing is listed until a drop
        has happened."""
        msg = "{} requires {} trials.".format(repr(self), total)
        given_up = self.optional[len(self.optional) - self.dropped:] if self.dropped else []
        if given_up:
            msg += " ({}: each level appears at least once)".format(
                ", ".join(str(f.name) for f in given_up))
        return msg

    def optional_hint(self) -> Optional[str]:
        """What could still be moved to `optional`, or None when there is
        nothing worth suggesting: with one factor, giving it up leaves coverage
        asking almost nothing.

        Worded as a condition because a factor in `optional` is given up only
        when the design has no solution, so this cannot promise fewer trials."""
        if not self.required or len(self.factors) < 2:
            return None
        return ("Any of {} can be moved to `optional`, to be given up for a "
                "shorter experiment if no solution is found."
                .format(", ".join(str(f.name) for f in self.required)))

    @staticmethod
    def _k_lower_bound(R_free, slots, slot_weights=None):
        """Analytic floor for the instance count, letting the matching scan start
        near the answer:

        - global capacity: ceil(|R_free| / total picks per instance);
        - Hall-style signature bounds: combos grouped by the exact set of slots
          that can serve them; each group needs ceil(demand / group picks).

        Sound but not always tight (unions of overlapping signatures are not
        enumerated), so the matching scan remains the ground truth."""
        if slot_weights is None:
            slot_weights = [1] * len(slots)
        total_picks = sum(slot_weights)
        if total_picks <= 0:
            return 1
        bound = -(-len(R_free) // total_picks)  # ceil
        demands = {}  # type: Dict[frozenset, int]
        for c in R_free:
            sig = frozenset(si for si, s in enumerate(slots) if c in s)
            demands[sig] = demands.get(sig, 0) + 1
        for sig, demand in demands.items():
            picks = sum(slot_weights[si] for si in sig)
            if picks > 0:
                bound = max(bound, -(-demand // picks))  # ceil
        return max(bound, 1)

    @staticmethod
    def _min_instances(R_free, slots, slot_weights=None):
        who = "CoverAllCombinations"
        if not R_free:
            return 1
        combos = list(R_free)
        for c in combos:
            if not any(c in s for s in slots):
                raise ValueError((who, "combination {} cannot be produced in any free "
                                       "trial; coverage is impossible".format(c)))
        # upper = |R_free| provably suffices: at that k, each slot's capacity
        # already covers every combo it serves. start = the analytic floor, so
        # the scan is guaranteed to succeed within [start, upper].
        upper = len(combos)
        start = CoverAllCombinations._k_lower_bound(R_free, slots, slot_weights)
        for k in range(start, upper + 1):
            if CoverAllCombinations._feasible(combos, slots, k, slot_weights):
                return k
        return upper

    @staticmethod
    def _feasible(combos, slots, k, slot_weights=None):
        """Can `combos` be covered with each slot-type covering at most
        `k * weight` combos? (A weight-w cell appears w times per instance.)

        Bipartite matching where each slot-type has capacity-many copies, via
        Kuhn's augmenting-path algorithm. Sizes are small for experimental designs.
        """
        if slot_weights is None:
            slot_weights = [1] * len(slots)
        adj = [[si for si, s in enumerate(slots) if c in s] for c in combos]
        slot_copy_match = {}  # type: Dict[tuple, int]

        def augment(ci, visited):
            for si in adj[ci]:
                for copy in range(k * slot_weights[si]):
                    key = (si, copy)
                    if key in visited:
                        continue
                    visited.add(key)
                    if key not in slot_copy_match or augment(slot_copy_match[key], visited):
                        slot_copy_match[key] = ci
                        return True
            return False

        matched = 0
        for ci in range(len(combos)):
            if augment(ci, set()):
                matched += 1
        return matched == len(combos)

    # ~~~~~~~~~~~~~~ Constraint interface ~~~~~~~~~~~~~~

    def uses_factor(self, f: Factor) -> bool:
        return any(factor.uses_factor(f) for factor in self.factors)

    def desugar(self, replacements: dict) -> List[Constraint]:
        def replace(fs):
            return [replacements.get(f, [f, f])[1] for f in fs]
        # Rebuilding through the constructor re-derives the groups from the
        # mapped factors, so no group can keep a pre-desugar factor that the
        # block no longer has.
        c = CoverAllCombinations(*replace(self.required),
                                 optional=replace(self.optional))
        c._inner_block = self._inner_block
        c.dropped = self.dropped
        c.groups = c._grouping_after(c.dropped)
        return [c]

    def validate(self, block: Block) -> None:
        who = "CoverAllCombinations"
        # The weight check must precede validate_factor: desugaring replaces
        # weighted factors, so validate_factor would report a misleading
        # "not found" instead.
        for f in self.factors:
            if f.level_weight_sum() != len(f.levels):
                raise ValueError((who, "weighted levels not currently supported"))
        for f in self.factors:
            validate_factor(block, f)

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        preamble = block.common_preamble_size()
        num_trials = block._trials_per_sample()
        trials = list(range(1 + preamble, num_trials + 1))

        fresh = backend_request.fresh
        formula_parts = cast(List[FormulaWithIff], [])
        analysis = self._analysis_block(block)
        for group in self.groups:
            (_, _, R_free, _, combo_levels, _, _) = self._coverage_analysis(
                analysis, group, exclusion_block=block)
            # A group's combinations name only its own factors, so a demoted
            # singleton asks for its level alone; encode_combination takes the
            # partial assignment as-is.
            for combo in R_free:
                levels = combo_levels[combo]
                state_vars = []
                for t in trials:
                    sv = fresh
                    fresh += 1
                    state_vars.append(sv)
                    formula_parts.append(Iff(sv, And(list(block.encode_combination(levels, t)))))
                # At least one trial must instantiate this combination.
                formula_parts.append(Or(state_vars))
        if not formula_parts:
            return

        (cnf, new_fresh) = block.cnf_fn(And(formula_parts), fresh)
        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def potential_sample_conforms(self, sample: dict, block: Block) -> bool:
        num_trials = block._trials_per_sample()
        analysis = self._analysis_block(block)
        for group in self.groups:
            (_, _, R_free, _, _, _, _) = self._coverage_analysis(
                analysis, group, exclusion_block=block)
            for combo in R_free:
                need = dict(combo)  # factor_name -> level_name
                found = False
                for t in range(num_trials):
                    if all(sample[f][t].name == need[f.name] for f in group):
                        found = True
                        break
                if not found:
                    return False
        return True

    def __repr__(self):
        args = [f.name for f in self.required]
        if self.optional:
            args.append("optional=[{}]".format(
                ", ".join(f.name for f in self.optional)))
        return "CoverAllCombinations({})".format(", ".join(args))
