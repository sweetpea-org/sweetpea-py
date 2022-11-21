"""This module provides constraints for CNF generation."""

import operator as op
from abc import abstractmethod
from copy import deepcopy
from typing import List, Tuple, Any, Union, cast, Dict, Callable
from itertools import chain, product
from math import ceil

from sweetpea.base_constraint import Constraint
from sweetpea.internal.iter import chunk, chunk_list
from sweetpea.blocks import Block, FullyCrossBlock, MultipleCrossBlock
from sweetpea.backend import LowLevelRequest, BackendRequest
from sweetpea.logic import If, Iff, And, Or, Not
from sweetpea.primitives import DerivedFactor, DerivedLevel, Factor, Level, SimpleLevel
from sweetpea.internal.argcheck import argcheck, make_istuple
from sweetpea.internal.weight import combination_weight
from sweetpea.internal.beforestart import BeforeStart


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
        for _ in range(block.trials_per_sample()):
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

    def potential_sample_conforms(self, sample: dict) -> bool:
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
    def apply(block: MultipleCrossBlock, backend_request: BackendRequest) -> None:
        # Treat each crossing seperately, but they're related by shared variables, which
        # are the per-trial, per-level variables of factors used in multiple crossings
        for c in block.crossings:
            fresh = backend_request.fresh

            # Step 1a: Get a list of the trials that are involved in the crossing. That list
            # omits leading trials that will be present to initialize transitions, and the
            # number of trials may have been reduced by exclusions.
            crossing_size = block.crossing_size(c);
            trial_count = max(block.min_trials, crossing_size)
            crossing_trials = list(filter(lambda t: all(map(lambda f: f.applies_to_trial(t), c)),
                                          range(1, block.trials_per_sample() + 1)))
            crossing_trials = crossing_trials[:trial_count]

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
            num_state_vars = len(crossing_combinations) * len(crossing_combinations[0])
            state_vars = list(range(fresh, fresh + num_state_vars))
            fresh += num_state_vars

            # Step 2b: Associate each state variable with its combination in each trial.
            flattened_combinations = list(chain.from_iterable(crossing_combinations))
            iffs = list(map(lambda n: Iff(state_vars[n], And([*flattened_combinations[n]])), range(len(state_vars))))

            # Step 2c: Get weight associated with each combination.
            combination_weights = [combination_weight(tuple(c.values())) for c in trial_combinations]

            # Step 3: Constrain each crossing to occur exactly according to its weight in each `crossing_size`
            # set of trials, or at most that much in a last set of trials that is less than
            # `crossing_size` in length.
            states = list(chunk(state_vars, len(trial_combinations)))
            transposed = cast(List[List[int]], list(map(list, zip(*states))))
            reqss = map(lambda l, w: Cross.__add_weight_constraint(l, w, crossing_size), transposed, combination_weights)
            backend_request.ll_requests += list(chain.from_iterable(reqss))

            (cnf, new_fresh) = block.cnf_fn(And(iffs), fresh)

            backend_request.cnfs.append(cnf)
            backend_request.fresh = new_fresh

    @staticmethod
    def __add_weight_constraint(variables: List[int], weight: int, crossing_size: int) -> List[LowLevelRequest]:
        """Constrain to a weight of each `crossing_size` sequence of variables, and at
        at most one for an ending sequence that is less than `crossing_size` in length.
        """
        to_add = len(variables)
        reqs = cast(List[LowLevelRequest], [])
        while to_add > 0:
            if (to_add >= crossing_size):
                reqs.append(LowLevelRequest("EQ", weight, variables[:crossing_size]))
            else:
                reqs.append(LowLevelRequest("LT", weight+1, variables))
            variables = variables[crossing_size:]
            to_add -= crossing_size
        return reqs

    def potential_sample_conforms(self, sample: dict) -> bool:
        # conformance by construction in combinatoric
        return True
            
class FullyCross(Cross):
    """Covered by Cross"""

class MultipleCross(Cross):
    """Covered by Cross"""

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
        self.dependent_idxs = dependent_idxs
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
        cross_size = block.trials_per_sample()

        iffs = []
        for n in range(cross_size):
            or_clause = Or(list(And(list(map(lambda x: x + (n * trial_size) + 1, l))) for l in self.dependent_idxs))
            iffs.append(Iff(self.derived_idx + (n * trial_size) + 1, or_clause))

        (cnf, new_fresh) = block.cnf_fn(And(iffs), backend_request.fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def __apply_derivation_with_complex_window(self, block: Block, backend_request: BackendRequest) -> None:
        trial_size = block.variables_per_trial()
        trial_count = block.trials_per_sample()
        iffs = []
        f = self.factor
        window = f.levels[0].window
        t = 0
        delta = window.start_delta
        for n in range(trial_count):
            if not f.applies_to_trial(n + 1):
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
                        if new_x < 0:
                            ok = False
                            break
                        vars.append(new_x)
                if ok:
                    ands.append(And(vars))

            or_clause = Or(ands)
            iffs.append(Iff(self.derived_idx + (t * num_levels) + 1, or_clause))
            t += 1
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

    def potential_sample_conforms(self, sample: dict) -> bool:
        return True


class _KInARow(Constraint):
    def __init__(self, k, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]]):
        self.k = k
        self.level = level
        self.__validate()

    def __validate(self) -> None:
        who = self.__class__.__name__

        if not isinstance(self.k, int):
            raise ValueError(f"{who}: k must be an integer, received {self.k}")

        if self.k <= 0:
            raise ValueError(f"{who}: k must be greater than 0; if you're trying to exclude a particular level, "
                             f"use the 'Exclude' constraint")

        if isinstance(self.level, Factor):
            pass
        elif isinstance(self.level, tuple) and len(self.level) == 2:
            if not (isinstance(self.level[1], SimpleLevel) or isinstance(self.level[1], DerivedLevel)):
                l = self.level[0].get_level(self.level[1])
                if not l:
                    raise ValueError(f"{who}: not a level in factor {self.level[0]}: {self.level[1]}")
                self.level = (self.level[0], l)
        else:
            raise ValueError(f"{who}: expected either a Factor or a tuple of Factor and Level, given {self.level}")

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.level[0], self.level[1])

    def uses_factor(self, f: Factor) -> bool:
        if isinstance(self.level, Factor):
            return self.level.uses_factor(f)
        else:
            return self.level[0].uses_factor(f)

    def desugar(self, replacements: dict) -> List[Constraint]:
        constraints = cast(List[Constraint], [self])

        if isinstance(self.level, Factor):
            level = replacements.get(self.level, self.level)
        else:
            level = (replacements.get(self.level[0], self.level[0]),
                     replacements.get(self.level[0], self.level[1]))

        # Generate the constraint for each level in the factor.
        if isinstance(level, Factor):
            levels = level.levels  # Get the actual levels out of the factor.
            level_tuples = list(map(lambda level: (self.level, level), levels))

            constraints = []
            for t in level_tuples:
                constraint_copy = deepcopy(self)
                constraint_copy.level = t
                constraints.append(constraint_copy)
        elif level != self.level:
            constraint_copy = deepcopy(self)
            constraint_copy.level = level
            constraints = [constraint_copy]

        return constraints

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        # By this point, level should be a Tuple containing the factor and the level.
        # Block construction is expected to flatten out constraints applied to whole factors so
        # that the constraint is applied to each level of the factor.
        if isinstance(self.level, tuple) and len(self.level) == 2:
            self.apply_to_backend_request(block, self.level, backend_request)
        else:
            raise ValueError("Unrecognized levels specification in AtMostKInARow constraint: " + str(self.level))

    def _build_variable_sublists(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], sublist_length: int) -> List[List[int]]:
        var_list = block.build_variable_list(level)
        raw_sublists = [var_list[i:i+sublist_length] for i in range(0, len(var_list))]
        return list(filter(lambda l: len(l) == sublist_length, raw_sublists))

    @abstractmethod
    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], backend_request: BackendRequest) -> None:
        pass

    def potential_sample_conforms(self, sample: dict) -> bool:
        factor = self.level[0]
        level = self.level[1]

        level_list = sample[factor]
        counts = []
        count = 0
        for l in level_list:
            if count > 0 and l != level:
                counts.append(count)
                count = 0
            elif l == level:
                count += 1

        if count > 0:
            counts.append(count)

        return self._potential_counts_conform(counts)

    @abstractmethod
    def _potential_counts_conform(self, counts: List[int]) -> bool:
        pass

    def _potential_counts_conform_individually(self, counts: List[int], fn: Callable[[int, int], bool]) -> bool:
        return all(map(lambda n: fn(n, self.k), counts))


def at_most_k_in_a_row(k, levels):
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
    return AtMostKInARow(k, levels)


class AtMostKInARow(_KInARow):
    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]], backend_request: BackendRequest) -> None:
        sublists = self._build_variable_sublists(block, level, self.k + 1)

        # Build the requests
        backend_request.ll_requests += list(map(lambda l: LowLevelRequest("LT", self.k + 1, l), sublists))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return self._potential_counts_conform_individually(counts, op.le)


def at_least_k_in_a_row(k, levels):
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
    return AtLeastKInARow(k, levels)


class AtLeastKInARow(_KInARow):
    def __init__(self, k, levels):
        super().__init__(k, levels)
        self.max_trials_required = cast(int, None)

    def apply_to_backend_request(self, block: Block, level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                    backend_request: BackendRequest) -> None:

        # Request sublists for k+1 to allow us to determine the transition
        sublists = self._build_variable_sublists(block, level, self.k + 1)
        implications = []
        if sublists:
            # Starting corner case
            implications.append(If(sublists[0][0], And(sublists[0][1:-1])))
            for sublist in sublists:
                implications.append(If(And([Not(sublist[0]), sublist[1]]), And(sublist[2:])))
            # Ending corner case
            implications.append(If(sublists[-1][-1], And(sublists[-1][1:-1])))

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


def exactly_k(k ,levels):
    """Requires that if the given level exists at all, it must exist in a trial
    exactly ``k`` times.
    """
    return ExactlyK(k, levels)


class ExactlyK(_KInARow):
    def apply_to_backend_request(self,
                                 block: Block,
                                 level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                 backend_request: BackendRequest
                                 ) -> None:
        sublists = block.build_variable_list(level)
        backend_request.ll_requests.append(LowLevelRequest("EQ", self.k, sublists))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _potential_counts_conform(self, counts: List[int]) -> bool:
        return sum(counts) == self.k


def exactly_k_in_a_row(k, levels):
    """Requires that if the given level exists at all, it must exist in a
    sequence of exactly K.
    """
    return ExactlyKInARow(k, levels)


class ExactlyKInARow(_KInARow):
    def apply_to_backend_request(self,
                                 block: Block,
                                 level: Tuple[Factor, Union[SimpleLevel, DerivedLevel]],
                                 backend_request: BackendRequest
                                 ) -> None:
        sublists = self._build_variable_sublists(block, level, self.k)
        implications = []

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

        # Handle the tail
        if len(sublists[-1]) > 1:
            tail = sublists[-1]
            tail.reverse()
            for idx in range(len(tail) - 1):
                implications.append(If(l[idx], l[idx + 1]))

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

def filter_factor_and_level(who, factor, level):
    argcheck(who, factor, Factor, "a Factor")
    if not isinstance(level, Level):
        l = factor.get_level(level)
        if not l:
            raise ValueError(f"{who}: not a level in factor {factor}: {level}")
        level = l
    elif level not in factor.levels:
        raise RuntimeError(f"{who}: given level is not in given factor: {level} not in {factor}")
    return (factor, level)

def exclude(factor, levels):
    return Exclude(factor, levels)

class Exclude(Constraint):
    def __init__(self, factor, level):
        factor, level = filter_factor_and_level("Exclude", factor, level)
        self.factor = factor
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
        factor = replacements.get(self.factor, self.factor)
        level = replacements.get(self.level, self.level)
        return [Exclude(factor, level)]

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
        var_list = block.build_variable_list((self.factor, self.level))
        backend_request.cnfs.append(And(list(map(lambda n: n * -1, var_list))))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def is_complex_for_combinatoric(self) -> bool:
        return False

    def potential_sample_conforms(self, sample: dict) -> bool:
        # conformance by construction in combinatoric for simple factors, but
        # we have to check exlcusions based on complex factors
        if self.factor.has_complex_window:
            levels = sample[self.factor]
            level = self.level
            for l in levels:
                if l == level:
                    return False
        return True

class Pin(Constraint):
    def __init__(self, index, factor, level):
        factor, level = filter_factor_and_level("Pin", factor, level)
        self.index = index
        self.factor = factor
        self.level = level

    def _get_trial_number(self, block) -> int:
        num_trials = block.trials_per_sample()
        if self.index < 0:
            trial_no = num_trials + self.index
        else:
            trial_no = self.index
        if (trial_no >= 0) and (trial_no < num_trials):
            return trial_no
        else:
            return -1

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.factor, self.level)
        if self._get_trial_number(block) < 0:
            num_trials = block.trials_per_sample()
            block.errors.add("WARNING: Pin constraint unsatisfiable, because "
                             + str(self.index) + " is out of range for " + str(num_trials) + " trials")

    def uses_factor(self, f: Factor) -> bool:
        return self.factor.uses_factor(f)

    def desugar(self, replacements: dict) -> List:
        factor = replacements.get(self.factor, self.factor)
        level = replacements.get(self.level, self.level)
        return [Pin(self.index, factor, level)]

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        trial_no = self._get_trial_number(block)
        if trial_no >= 0:
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

    def potential_sample_conforms(self, sample: dict) -> bool:
        levels = sample[self.factor]
        num_trials = len(levels)
        if self.index < 0:
            trial_no = num_trials + self.index
        else:
            trial_no = self.index

        if (trial_no >= 0) and (trial_no < num_trials):
            return levels[trial_no] == self.level
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

    def potential_sample_conforms(self, sample: dict) -> bool:
        return True

    def desugar(self, replacements: dict) -> List:
        factor = replacements.get(self.factor, self.factor)
        return [Reify(factor)]


def minimum_trials(trials):
    return MinimumTrials(trials)


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

    def potential_sample_conforms(self, sample: dict) -> bool:
        return True
