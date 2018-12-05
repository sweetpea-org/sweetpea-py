from typing import List, Tuple, cast
from itertools import product, chain, accumulate, repeat
from functools import reduce

from sweetpea.base_constraint import Constraint
from sweetpea.internal import chunk, chunk_list, pairwise, get_all_level_names
from sweetpea.blocks import Block
from sweetpea.backend import LowLevelRequest, BackendRequest
from sweetpea.logic import Iff, And, Or
from sweetpea.primitives import Factor, get_level_name


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
    @staticmethod
    def apply(block: Block, backend_request: BackendRequest) -> None:
        fresh = backend_request.fresh

        num_states = block.trials_per_sample() # same as number of trials in fully crossing
        simple_design = list(filter(lambda f: not f.has_complex_window(), block.design))

        # Step 1:
        num_state_vars = num_states * num_states
        stateVars = list(range(fresh, fresh + num_state_vars))

        fresh += num_state_vars

        # Step 2:
        states = list(chunk(stateVars, num_states))
        transposed = cast(List[List[int]], list(map(list, zip(*states))))
        chunked_trials = list(chunk(list(range(1, block.grid_variables() + 1)), block.variables_per_trial()))

        # 1. group chunked_trials into factor shaped subchunks
        # ie, [[1, 2], [3, 4], [5, 6]], [[7, 8], ...
        delimiters = list(accumulate([0] + list(map(lambda i: len(simple_design[i].levels), range(len(simple_design))))))
        slices = list(pairwise(delimiters))
        subchunked_trials = [[list(l[s[0]:s[1]]) for s in slices] for l in chunked_trials]

        # 2. grab the subchunks which correspond to levels in the crossing
        # ie, [[1, 2], [3, 4]], [[7, 8], [9, 10]], [[...
        factor_dict = {factor.name: factor_index for factor_index, factor in enumerate(simple_design)}
        keep_factor_indices = [factor_dict[factor.name] for factor in block.crossing]
        subchunk_levels = [[chunked_trial[idx] for idx in keep_factor_indices] for chunked_trial in subchunked_trials]

        # 3. for each trial, take the itertools product of all the subchunks
        # ie, [[1, 3], [1, 4], [2, 3], [2, 4]], ...
        products = [list(product(*subchunks)) for subchunks in subchunk_levels]
        flattened_products = list(chain(*products))

        # 4. get those into an Iff w/ the state variables; ie Iff(25, And([1,3])) & then toCNF that & stash it on the queue.
        iffs = [Iff(stateVars[n], And(list(flattened_products[n]))) for n in range(len(stateVars))]

        # Step 3:
        # 5. make Requests for each transposed list that add up to k=1.
        backend_request.ll_requests += list(map(lambda l: LowLevelRequest("EQ", 1, l), transposed))

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
    fullycross(color, text) + noMoreThanKInARow 1 conLevel

"""
class Derivation(Constraint):
    def __init__(self, derived_idx, dependent_idxs):
        self.derived_idx = derived_idx
        self.dependent_idxs = dependent_idxs
        # TODO: validation

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
        # The number of constraints that a complex derivation generates is dependent on its stride....
        # TODO: I'll have to do something about this when we implement general windows. Transition still
        # Works because it can assume a stride of 1.
        trial_size = block.variables_per_trial()
        trial_count = block.trials_per_sample()

        iffs = []
        for n in range(trial_count - 1):
            or_clause = Or(list(And(list(map(lambda x: x + (n * trial_size) + 1, l))) for l in self.dependent_idxs))
            iffs.append(Iff(self.derived_idx + (n * 2) + 1, or_clause))

        (cnf, new_fresh) = block.cnf_fn(And(iffs), backend_request.fresh)

        backend_request.cnfs.append(cnf)
        backend_request.fresh = new_fresh

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


"""
This desugars pretty directly into the llrequests.
The only thing to do here is to collect all the boolean vars that match the same
level & pair them up according to k.

Continuing with the example from __desugar_consistency, say we want
NoMoreThanKInARow 1 ("color", "red"), then we need to grab all the vars which
indicate color-red:

    [1, 7, 13, 19]

and then wrap them up so that we're making requests like:

    sum(1, 7)  LT 2
    sum(7, 13)  LT 2
    sum(13, 19) LT 2

If it had been NoMoreThanKInARow 2 ("color", "red"), the reqs would have been:

    sum(1, 7, 13)  LT 3
    sum(7, 13, 19) LT 3
"""
class NoMoreThanKInARow(Constraint):
    def __init__(self, k, levels):
        self.k = k
        self.levels = levels
        self.__validate()

    def __validate(self) -> None:
        if not isinstance(self.k, int):
            raise ValueError("NoMoreThanKInARow.k must be an integer.")

        if not (isinstance(self.levels, Factor) or \
                (isinstance(self.levels, tuple) and \
                 len(self.levels) == 2 and \
                 isinstance(self.levels[0], str) and \
                 isinstance(self.levels[1], str))):
            raise ValueError("NoMoreThanKInARow.levels must be either a Factor or a Tuple[str, str].")

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        # Apply the constraint to each level in the factor.
        if isinstance(self.levels, Factor):
            levels = self.levels.levels  # Get the actual levels out of the factor.
            level_names = list(map(lambda l: get_level_name(l), levels))
            level_tuples = list(map(lambda l_name: (self.levels.name, l_name), level_names))
            requests = list(map(lambda t: self.__generate_requests(t, block), level_tuples))
            backend_request.ll_requests += list(chain(*requests))

        # Should be a Tuple containing the factor name, and the level name.
        elif isinstance(self.levels, tuple) and len(self.levels) == 2:
            backend_request.ll_requests += self.__generate_requests(cast(Tuple[str, str], self.levels), block)

        else:
            raise("Unrecognized levels specification in NoMoreThanKInARow constraint: " + self.levels)

    def __generate_requests(self, level:Tuple[str, str], block: Block) -> List[LowLevelRequest]:
        first_variable = block.first_variable_for_level(level[0], level[1]) + 1

        # Build the variable list
        if first_variable <= block.variables_per_trial():
            var_list = self.__build_variable_list(block, first_variable)
        else:
            var_list = self.__build_complex_variable_list(block, level)

        # Break up the var list into overlapping lists where len == k.
        raw_sublists = [var_list[i:i+self.k+1] for i in range(0, len(var_list))]
        sublists = list(filter(lambda l: len(l) == self.k + 1, raw_sublists))

        # Build the requests
        return list(map(lambda l: LowLevelRequest("LT", self.k + 1, l), sublists))

    def __build_variable_list(self, block: Block, first_variable: int) -> List[int]:
        design_var_count = block.variables_per_trial()
        num_trials = block.trials_per_sample()
        return list(accumulate(repeat(first_variable, num_trials), lambda acc, _: acc + design_var_count))

    def __build_complex_variable_list(self, block: Block, level: Tuple[str, str]) -> List[int]:
        factor = block.get_factor(level[0])
        n = int(block.variables_for_factor(factor) / 2)
        start = block.first_variable_for_level(level[0], level[1]) + 1
        return reduce(lambda l, v: l + [start + (v * 2)], range(n), [])

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class Forbid(Constraint):
    def __init__(self, level):
        self.level = level
        # TODO: validation

    def apply(self, block: Block, backend_request: BackendRequest) -> None:
        # Generate a list of (factor name, level name) tuples from the block
        level_tuples = get_all_level_names(block.design)

        # Locate the specified level in the list
        first_variable = level_tuples.index(self.level) + 1

        # Build the variable list
        design_var_count = block.variables_per_trial()
        num_trials = block.trials_per_sample()
        var_list = list(accumulate(repeat(first_variable, num_trials), lambda acc, _: acc + design_var_count))

        backend_request.cnfs.append(And(list(map(lambda n: n * -1, var_list))))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
