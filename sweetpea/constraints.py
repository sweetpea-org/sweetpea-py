from abc import abstractmethod
from copy import deepcopy
from typing import List, Tuple, Any, Union, cast
from itertools import product, chain, accumulate, repeat
from functools import reduce

from sweetpea.base_constraint import Constraint
from sweetpea.internal import chunk, chunk_list, pairwise, get_all_level_names
from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.backend import LowLevelRequest, BackendRequest
from sweetpea.logic import If, Iff, And, Or, Not, FormulaWithIff
from sweetpea.primitives import Factor, get_level_name


def validate_factor_and_level(block: Block, factor_name: str, level_name: str) -> None:
    if not block.get_factor(factor_name):
        raise ValueError(("A factor with name '{}' wasn't found in the design. " +\
            "Are you sure the factor was included, and that the name is spelled " +\
            "correctly?").format(factor_name))

    if not block.get_factor(factor_name).get_level(level_name):
        raise ValueError(("A level with name '{}' wasn't found in the '{}' factor, " +\
            "Are you sure the level name is spelled correctly?").format(level_name, factor_name))


"""
This constraint ensures that only one level of each factor is 'on' at a time.
So for instance in the experiment:

    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    design = crossing = [color, text, conFactor]
    experiment   = fully_cross_block(design, crossing, [])

The first trial is represented by the boolean vars [1, 2, 3, 4]

    0 is true iff the trial is color:red
    1 is true iff the trial is color:blue
    2 is true iff the trial is text:red
    3 is true iff the trial is text:blue

The second trial is represented by the boolean vars [5-8], the third by [9-12],
the fourth by [13-16]. So this desugaring applies the following constraints:

    sum(1, 2) EQ 1
    sum(3, 4) EQ 1
    sum(5, 6) EQ 1
    ...
    sum(15, 16) EQ 1
"""
class Consistency(Constraint):
    def validate(self, block: Block) -> None:
        pass

    @staticmethod
    def apply(block: Block, backend_request: BackendRequest) -> None:
        next_var = 1
        for _ in range(block.trials_per_sample()):
            for f in filter(lambda f: not f.has_complex_window(), block.design):
                number_of_levels = len(f.levels)
                new_request = LowLevelRequest("EQ", 1, list(range(next_var, next_var + number_of_levels)))
                backend_request.ll_requests.append(new_request)
                next_var += number_of_levels

        for f in filter(lambda f: f.has_complex_window(), block.design):
            variables_for_factor = block.variables_for_factor(f)
            var_list = list(map(lambda n: n + next_var, range(variables_for_factor)))
            chunks = list(chunk_list(var_list, len(f.levels)))
            backend_request.ll_requests += list(map(lambda v: LowLevelRequest("EQ", 1, v), chunks))
            next_var += variables_for_factor



"""
We represent the fully crossed constraint by allocating additional boolean
variables to represent each unique state. Only factors in crossing will
contribute to the number of states (there may be factors in the design that
aren't in the crossing).

Continuing with example from __desugar_consistency we will represent the states:

    (color:red, text:red)
    (color:red, text:blue)
    (color:blue, text:red)
    (color:blue, text:blue)

-- 1. Generate Intermediate Vars:
      Using the fresh var counter, allocate numTrials * num_states new vars
-- 2. Entangle them w/ block vars
      Add to the CNF queue: toCNF(Iff(newVar, And(levels)))
      ie, if the variable 1 indicates color:red, the var 3 indicates text:red,
      and the var 25 represents (color:red, text:red):
        toCNF(Iff(25, And([1, 3])))
-- 3. 1 hot the *states* ie, 1 red circle, etc
      same as __desugar_consistency above, collect all the state vars that
      represent each state & enforce that only one of those states is true, ie
      sum(25, 29, 33, 37) EQ 1
      (and 3 more of these for each of the other states).
"""
class FullyCross(Constraint):
    def validate(self, block: Block) -> None:
        pass

    @staticmethod
    def apply(block: FullyCrossBlock, backend_request: BackendRequest) -> None:
        fresh = backend_request.fresh

        # Step 1: Get a list of the trials that are involved in the crossing.
        crossing_trials = list(filter(lambda t: all(map(lambda f: f.applies_to_trial(t), block.crossing)), range(1, block.trials_per_sample() + 1)))

        # Step 2: For each trial, cross all levels of all factors in the crossing.
        crossings = []
        for t in crossing_trials:
            crossings.extend(list(product(*[block.factor_variables_for_trial(f, t) for f in block.crossing])))

        # Step 3: Allocate additional variables to represent each crossing.
        num_state_vars = len(crossings)
        state_vars = list(range(fresh, fresh + num_state_vars))
        fresh += num_state_vars

        # Step 4: Associate each state variable with its crossing.
        iffs = [Iff(state_vars[n], And(list(crossings[n]))) for n in range(len(state_vars))]

        # Step 5: Constrain each crossing to occur in only one trial.
        states = list(chunk(state_vars, block.crossing_size_without_exclusions()))
        transposed = cast(List[List[int]], list(map(list, zip(*states))))

        # We Use n < 2 rather than n = 1 here because they may exclude some levels from the crossing.
        # This ensures that there won't be duplicates, while still allowing some to be missing.
        backend_request.ll_requests += list(map(lambda l: LowLevelRequest("LT", 2, l), transposed))

        (cnf, new_fresh) = block.cnf_fn(And(iffs), fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh


"""
The derivations come in looking likeL:

    Derivation(4, [[0, 2], [1, 3]])
    (derivedLevel index; list of indicies that are dependent)

This represents:

    4 iff (0 and 2) or (1 and 3)

These indicies are used the get the corresponding trial variables. Continuing
from the example in of processDerivations, the first trial is represented by
variables [1-6] (notice this feels like an off-by-one: the indicies start from
0, but the boolean variables start from 1). So we would use the idxs to map onto
the vars as:

    5 iff (1 and 3) or (2 and 4)

Then we convert to CNF directly, ie

    toCNF(Iff(5, Or(And(1,3), And(2,4))))

This is then done for all window-sizes, taking into account strides (which are
specified only in DerivedLevels specified with a general Window rather than
Transition or WithinTrial). We grab window-sized chunks of the variables that
represent the trials, map the variables using the indices, and then convert to
CNF. These chunks look like:

    window1: 1  2  3  4  5  6
    window2: 7  8  9  10 11 12

So, for the second trial (since the window size in this example is 1) it would
be:

    11 iff (7 and 9) or (8 and 10)

90% sure this is the correct way to generalize to derivations involving 2+
levels & various windowsizes. One test is the experiment:

    color = ["r", "b", "g"];
    text = ["r", "b"];
    conFactor;
    fullycross(color, text) + AtMostKInARow 1 conLevel

"""
class Derivation(Constraint):
    def __init__(self,
                 derived_idx: int,
                 dependent_idxs: List[List[int]],
                 factor: Factor) -> None:
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
        t = 0
        for n in range(trial_count):
            if not f.applies_to_trial(n + 1):
                continue

            num_levels = len(f.levels)
            starting_trial = n - (f.levels[0].window.width - 1)
            or_clause = Or(list(And(list(map(lambda x: x + (starting_trial * trial_size) + 1, l))) for l in self.dependent_idxs))
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


class _KInARow(Constraint):
    def __init__(self, k, level):
        self.k = k
        self.level = level
        self.__validate()

    def __validate(self) -> None:
        if not isinstance(self.k, int):
            raise ValueError("k must be an integer.")

        if self.k <= 0:
            raise ValueError("k must be greater than 0. If you're trying to exclude a particular level, please use the 'Exclude' constraint.")

        if not (isinstance(self.level, Factor) or \
                (isinstance(self.level, tuple) and \
                 len(self.level) == 2 and \
                 isinstance(self.level[0], str) and \
                 isinstance(self.level[1], str))):
            raise ValueError("level must be either a Factor or a Tuple[str, str].")

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.level[0], self.level[1])

    def desugar(self) -> List[Constraint]:
        constraints = cast(List[Constraint], [self])

        # Generate the constraint for each level in the factor.
        if isinstance(self.level, Factor):
            levels = self.level.levels  # Get the actual levels out of the factor.
            level_names = list(map(lambda l: get_level_name(l), levels))
            level_tuples = list(map(lambda l_name: (self.level.name, l_name), level_names))

            constraints = []
            for t in level_tuples:
                constraint_copy = deepcopy(self)
                constraint_copy.level = t
                constraints.append(constraint_copy)

        return constraints

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        # By this point, level should be a Tuple containing the factor name, and the level name.
        # Block construction is expected to flatten out constraints applied to whole factors so
        # that the constraint is applied to each level of the factor.
        if isinstance(self.level, tuple) and len(self.level) == 2:
            self.apply_to_backend_request(block, cast(Tuple[str, str], self.level), backend_request)
        else:
            raise ValueError("Unrecognized levels specification in AtMostKInARow constraint: " + str(self.level))

    def _build_variable_sublists(self, block: Block, level: Tuple[str, str], sublist_length: int) -> List[List[int]]:
        var_list = block.build_variable_list(level)
        raw_sublists = [var_list[i:i+sublist_length] for i in range(0, len(var_list))]
        return list(filter(lambda l: len(l) == sublist_length, raw_sublists))

    @abstractmethod
    def apply_to_backend_request(self, block: Block, level: Tuple[str, str], backend_request: BackendRequest) -> None:
        pass


"""
This desugars pretty directly into the llrequests.
The only thing to do here is to collect all the boolean vars that match the same
level & pair them up according to k.

Continuing with the example from __desugar_consistency, say we want
AtMostKInARow 1 ("color", "red"), then we need to grab all the vars which
indicate color-red:

    [1, 7, 13, 19]

and then wrap them up so that we're making requests like:

    sum(1, 7)  LT 2
    sum(7, 13)  LT 2
    sum(13, 19) LT 2

If it had been AtMostKInARow 2 ("color", "red"), the reqs would have been:

    sum(1, 7, 13)  LT 3
    sum(7, 13, 19) LT 3
"""
class AtMostKInARow(_KInARow):
    def apply_to_backend_request(self, block: Block, level: Tuple[str, str], backend_request: BackendRequest) -> None:
        sublists = self._build_variable_sublists(block, level, self.k + 1)

        # Build the requests
        backend_request.ll_requests += list(map(lambda l: LowLevelRequest("LT", self.k + 1, l), sublists))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


"""
Equivalent to AtMostKInARow.
"""
class NoMoreThanKInARow(Constraint):
    def __new__(self, k, levels):
        return AtMostKInARow(k, levels)


"""
Requires that if the given level exists at all, it must exist in a sequence of exactly K.
"""
class ExactlyKInARow(_KInARow):
    def apply_to_backend_request(self, block: Block, level: Tuple[str, str], backend_request: BackendRequest) -> None:
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


class Exclude(Constraint):
    def __init__(self, factor_name, level_name):
        self.factor_name = factor_name
        self.level_name = level_name
        # TODO: validation

    def validate(self, block: Block) -> None:
        validate_factor_and_level(block, self.factor_name, self.level_name)

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        var_list = block.build_variable_list((self.factor_name, self.level_name))
        backend_request.cnfs.append(And(list(map(lambda n: n * -1, var_list))))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
