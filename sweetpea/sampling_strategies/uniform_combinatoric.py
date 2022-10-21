import operator as op
import random
import numpy as np

from functools import reduce
from itertools import product
from math import factorial, ceil
from typing import List, cast, Tuple, Dict, Optional, Union, Any

from sweetpea.blocks import Block, CrossBlock
from sweetpea.combinatorics import (
    n_choose_m,
    extract_components, compute_jth_permutation_prefix, compute_jth_combination,
    count_prefixes_of_permutations_with_copies, compute_jth_prefix_of_permutations_with_copies,
    PermutationMemo
)
from sweetpea.design_partitions import DesignPartitions
from sweetpea.logic import And
from sweetpea.primitives import SimpleLevel, Factor, DerivedFactor, Level
from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.constraints import Exclude, _KInARow, ExactlyKInARow, AtMostKInARow
from sweetpea.internal.iter import chunk
from sweetpea.internal.weight import combination_weight

class RandomGen(SamplingStrategy):
    """This strategy represents the ideal. Valid sequences are uniformly
    sampled via a bijection from natural numbers to valid trial sequences.

    Complex windows and counting constrants are handled by rejection sampling.
    """

    def __str__(self):
        return UniformCombinatoricSamplingStrategy.class_name()

    @staticmethod
    def class_name():
        return 'RandomGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        return UniformCombinatoricSamplingStrategy.__sample(block, sample_count, 0)

    def __init__(self, acceptable_error):
        self.acceptable_error = acceptable_error

    def sample_object(self, block: Block, sample_count: int) -> SamplingResult:
        return UniformCombinatoricSamplingStrategy.__sample(block, sample_count, self.acceptable_error)

    @staticmethod
    def __sample(block: Block, sample_count: int, acceptable_error: int) -> SamplingResult:
        # 1. Validate the block.
        UniformCombinatoricSamplingStrategy.__validate(block)
        metrics = {}

        if block.show_errors():
            return SamplingResult([], {})

        # 2. Count how many solutions there are. The enumerator will note
        # the crossing size and minimum-trial request, and it will be prepared
        # to generate runs of a crossing-size length or "leftover" length.
        print("Counting possible configurations...")
        enumerator = UCSolutionEnumerator(cast(CrossBlock, block))
        metrics['solution_count'] = enumerator.solution_count()

        if (enumerator.solution_count() == 0):
            return SamplingResult([], metrics)

        crossing_size = enumerator.crossing_size

        # 3. Generate samples.
        print("Generating samples...")
        metrics['rejections'] = []
        sampled = 0
        rejected = 0
        total_rejected = 0
        trials_per_run = block.trials_per_sample()
        rounds_per_run = (trials_per_run - enumerator._preamble_size) // crossing_size
        leftover = (trials_per_run - enumerator._preamble_size) % crossing_size
        samples = cast(List[dict], [])
        used_keys = cast(Dict[Tuple[int, ...], bool], {})
        possible_keys = (enumerator.preamble_solution_count()
                         * pow(enumerator.solution_count(), rounds_per_run)
                         * enumerator.leftover_solution_count())
        while sampled < sample_count:
            if len(used_keys) == possible_keys:
                break

            solution_variabless = enumerator.generate_random_samples(rounds_per_run, leftover, used_keys)
            used_keys[enumerator.extract_sequence_key(solution_variabless)] = True

            # Combine randomly selected crossing-sized runs plus a leftover-sized run
            # into one complete run with the requested number of trials.
            run = solution_variabless[0][1] # the preamble solution, possibly empty
            for round in range(0, rounds_per_run + (1 if leftover > 0 else 0)):
                run = UniformCombinatoricSamplingStrategy.__combine_round(run, solution_variabless[round+1][1])

            run = enumerator.fill_in_nonpreamble_uncrossed_derived(run, trials_per_run)

            if UniformCombinatoricSamplingStrategy.__are_constraints_violated(cast(CrossBlock, block), run, enumerator,
                                                                              rounds_per_run, leftover,
                                                                              acceptable_error):
                rejected += 1
                if rejected % 10000 == 0:
                    if len(samples) > 0:
                        accepts = f", accepted {len(samples)}"
                    else:
                        accepts = ""
                    print(f"Rejected {total_rejected+rejected} candidates so far (out of {possible_keys} choices){accepts}")
                continue

            metrics['rejections'].append(rejected)
            total_rejected += rejected
            rejected = 0
            sampled += 1

            samples.append(enumerator.factors_and_levels_to_names(run))

        metrics['sample_count'] = sample_count
        metrics['total_rejected'] = total_rejected
        metrics['avg_rejected'] = total_rejected / sample_count
        if (total_rejected > 10000):
            print("")

        return SamplingResult(samples, metrics)

    @staticmethod
    def __are_constraints_violated(block: CrossBlock, sample: dict, enumerator: 'UCSolutionEnumerator',
                                   rounds_per_run: int, leftover: int,
                                   acceptable_error: int) -> bool:
        for ct in block.constraints:
            if not ct.potential_sample_conforms(sample):
                return True
        if enumerator.has_crossed_complex_derived_factors or len(block.crossings) > 1:
            # Check whether the sample achieves each crossing in the run
            bad = 0
            run_length = enumerator._preamble_size + (rounds_per_run * enumerator.crossing_size) + leftover
            for i, c in enumerate(block.crossings):
                if enumerator.has_crossed_complex_derived_factors or i > 0:
                    def conds_match_weights(start: int, end: int, or_less: bool):
                        nonlocal bad
                        combos = cast(Dict[Tuple[Level, ...], int], {})
                        for t in range(start, end):
                            key = tuple([sample[f][t] for f in c])
                            combos[key] = combos.get(key, 0) + 1
                        for combo, count in combos.items():
                            bad += abs(count - combination_weight(combo))
                            if bad > acceptable_error:
                                return False
                        return True
                    start = enumerator.preamble_sizes[i]
                    c_crossing_size = enumerator.crossing_sizes[i]
                    c_rounds_per_run = (run_length - start) // c_crossing_size
                    c_leftover = (run_length - start) % c_crossing_size
                    for round in range(rounds_per_run):
                        if not conds_match_weights(start, start + c_crossing_size, False):
                            return True
                        start += c_crossing_size
                    if c_leftover > 0:
                        if not conds_match_weights(start, start+c_leftover, True):
                            return True
        return False

    @staticmethod
    def __validate(block: Block) -> None:
        # Triggers checks within `block`:
        block.trials_per_sample()

    @staticmethod
    def __combine_round(run: dict, round: dict) -> dict:
        if len(run) == 0:
            return round
        else:
            new_run = run.copy()
            for key in round:
                new_run[key] = run[key] + round[key]
            return new_run

Components = Tuple[int, Tuple[int, ...], Tuple[int, ...]]

class RandomComponentsShape():
    def __init__(self) -> None:
        self.crossings_shape = 0
        self.combinations_shapes = cast(List[int], [])
        self.independent_shapes = cast(List[int], [])                


"""
Given a fully crossed block with no complex windows, this class stores the data structures and logic for enumerating
valid trial sequences in the design.
"""
class UCSolutionEnumerator():

    def __init__(self, block: CrossBlock) -> None:
        self._block = block
        self._partitions = DesignPartitions(block)
        self._crossing_instances = self.__generate_crossing_instances()
        self._crossing_weights = [combination_weight(tuple(c.values())) for c in self._crossing_instances]
        self._crossing_is_unweighted = all([w == 1 for w in self._crossing_weights])
        self.noncomplex_crossing_size = sum(self._crossing_weights)
        self._source_combinations = self.__generate_source_combinations()
        self.__complex_crossing_instances = self.__count_complex_crossing_instances()
        self.crossing_size = self.noncomplex_crossing_size * self.__complex_crossing_instances
        self._ind_factor_levels = cast(List[Tuple[Factor, List[SimpleLevel]]], []) # Will be populated by solution counting
        self._basic_factor_levels = cast(List[Tuple[Factor, List[SimpleLevel]]], []) # Will be populated by solution counting
        m = self.__complex_crossing_instances
        self._m_or_counters = cast(Union[int, List[int]],
                                   m if self._crossing_is_unweighted else [w * m for w in self._crossing_weights])
        
        self._sorted_derived_factors = self._partitions.get_derived_factors()
        self._sorted_derived_factors.sort(key=lambda f: f._get_depth())

        self._sorted_uncrossed_derived_and_complex_derived = self._partitions.get_uncrossed_derived_and_complex_derived_factors()
        self._sorted_uncrossed_derived_and_complex_derived.sort(key=lambda f: f._get_depth())

        self.has_crossed_complex_derived_factors = (self.__complex_crossing_instances > 1)

        # Maintains a lookup for valid source combinations for a permutation.
        # Example [[2, 3], ...] means that for permutation 0, indices 2 and 3 in the source combinations
        # list are allowed.
        self._valid_source_combinations_indices = cast(List[List[int]], []) # Will be populated by solution counting

        # For multiple crossings, we'll need the size of each crossing and how much to consider the
        # preamble of each:
        self.crossing_sizes = [block.crossing_size(c) for c in block.crossings]
        self.preamble_sizes = [block._trials_per_sample_for_one_crossing(c) - block.crossing_size(c) for c in block.crossings]
        # Check that calculations from two sources agree:
        assert self.crossing_sizes[0] == self.crossing_size

        noncomplex_crossing_size = self.noncomplex_crossing_size
        preamble_size = self.preamble_sizes[0]
        self._preamble_size = preamble_size;

        # Call `__count_solutions` after everything else is set up.
        self._components_shape = RandomComponentsShape()
        self._pmemo = PermutationMemo()
        self._solution_count = self.__count_solutions(self.crossing_size,
                                                      self._components_shape,
                                                      self._pmemo,
                                                      self._valid_source_combinations_indices,
                                                      self._ind_factor_levels)
        self._leftover_components_shape = RandomComponentsShape()
        self._leftover_solution_count = 1
        self._leftover_pmemo = PermutationMemo()
        leftover = (block.trials_per_sample() - preamble_size) % self.crossing_size;
        if (leftover != 0):
            self._leftover_solution_count = self.__count_solutions(leftover,
                                                                   self._leftover_components_shape,
                                                                   self._leftover_pmemo,
                                                                   None,
                                                                   None)

        # How many extra trials do we need to generate by randomly
        # selecting among non-derived factors, to support derived
        # factors with complex windows?
        self._preamble_solution_count = self.__count_preamble_solutions()

    def solution_count(self):
        return self._solution_count

    def leftover_solution_count(self):
        return self._leftover_solution_count

    def preamble_solution_count(self):
        return self._preamble_solution_count

    def crossing_instances_count(self):
        return len(self._crossing_instances)

    def generate_random_samples(self, n: int, leftover: int, sampled: Dict[Tuple[int, ...], bool]) -> List[Tuple[int, dict]]:
        # Select a collection of random numbers, each from the range of solutions.
        # If `leftover` is not zero, then tack on one more sequence that is shorter
        # than the crossing size.
        # Then, make sure we haven't already picked the same sequence according to `sampled`.
        # This rejection-based approach is probably ok for realistic experiments,
        # where we're unlikely to want a number of samples close to the number of solutions
        # at the same time that there are a lot of solutions.
        choice = cast(List[Any],
                      (random.randrange(0, self._preamble_solution_count),
                       tuple([self.random_components(self._components_shape, self.crossing_size, 0) for i in range(n)]),
                       self.random_components(self._leftover_components_shape, leftover, leftover) if leftover > 0 else 0))
        while tuple([choice[0]] + list(choice[1]) + ([choice[2]] if leftover > 0 else [])) in sampled:
            choice = cast(List[Any],
                          (random.randrange(0, self._preamble_solution_count),
                           tuple([self.random_components(self._components_shape, self.crossing_size, 0) for i in range(n)]),
                           self.random_components(self._leftover_components_shape, leftover, leftover) if leftover > 0 else 0))
        return ([(choice[0], self.generate_preamble_sample(choice[0]))]
                + [(components, self.generate_sample_from_components(components)) for components in choice[1]]
                + ([(choice[2],
                     self.generate_leftover_sample(choice[2], leftover))] if leftover > 0 else []))

    def random_components(self, components_shape: RandomComponentsShape, trial_count: int, leftover: int) -> Components:
        crossing_permutation_index = random.randrange(0, components_shape.crossings_shape)        
        if trial_count == len(self._crossing_instances) and self._crossing_is_unweighted:
            source_combination_indices = tuple([random.randrange(0, len) for len in components_shape.combinations_shapes])
        else:
            # The indicies for source combination depend on the chosen permutation
            permutation_indices = self.jth_permutation_indices(len(self._crossing_instances),
                                                               self.crossing_size if leftover == 0 else leftover,
                                                               crossing_permutation_index,
                                                               self._pmemo if leftover == 0 else self._leftover_pmemo)
            indices = []
            for p in permutation_indices:
                indices.append(random.randrange(0, components_shape.combinations_shapes[p]))
            source_combination_indices = tuple(indices)
        independent_factor_combination_indices = tuple([random.randrange(0, len) for len in components_shape.independent_shapes])
        return (crossing_permutation_index,
                source_combination_indices,
                independent_factor_combination_indices)

    def extract_sequence_key(self, solution_variabless: List[Tuple[int, dict]]) -> Tuple[int, ...]:
        return tuple(map(lambda sv: sv[0], solution_variabless))

    def generate_sample_from_components(self, components: Components) -> dict:
        trial_values = self.generate_trial_values(components, self.crossing_size, len(self._crossing_instances),
                                                  self._pmemo)
        return self._trial_values_to_experiment(trial_values)

    def generate_sample(self, sequence_number: int) -> dict:
        """Used for tests where a single random sequence number is provided, instead of random components."""
        shapes = ([self._components_shape.crossings_shape]
                  + self._components_shape.combinations_shapes
                  + self._components_shape.independent_shapes)
        flat_components = extract_components(shapes, sequence_number)
        components = (flat_components[0],
                      tuple(flat_components[1:1+self.crossing_size]),
                      tuple(flat_components[1+self.crossing_size:]))
        return self.generate_sample_from_components(components)

    def generate_leftover_sample(self, components: Components, leftover: int) -> dict:
        trial_values = self.generate_trial_values(components, leftover, len(self._crossing_instances),
                                                  self._leftover_pmemo)
        return self._trial_values_to_experiment(trial_values)

    def _trial_values_to_experiment(self, trial_values: List[dict]) -> dict:
        experiment = cast(dict, {})
        for trial_number, trial_value in enumerate(trial_values):
            for factor, level in trial_value.items():
                if factor not in experiment:
                    experiment[factor] = []
                experiment[factor].append(level)
        return experiment

    def factors_and_levels_to_names(self, experiment: dict) -> dict:
        new_experiment = cast(dict, {})
        for k in experiment:
            new_experiment[k.name] = [(l.name if l else "") for l in experiment[k]]
        return new_experiment

    # Used for an acceptance test:
    def generate_solution_variables(self) -> List[int]:
        components = self.random_components(self._components_shape, self.crossing_size, 0)
        trial_values = self.generate_trial_values(components, len(self._crossing_instances), len(self._crossing_instances),
                                                  PermutationMemo())

        solution = cast(List[int], [])
        # Convert to variable encoding for SAT checking
        for trial_number, trial_value in enumerate(trial_values):
            for factor, level in trial_value.items():
                solution.append(self._block.get_variable(trial_number + 1, (factor, level)))
        solution.sort()
        return solution

    def generate_trial_values(self, components: Components, trial_count: int, crossing_size: int,
                              pmemo: PermutationMemo) -> List[dict]:
        # Component pieces:
        #    The 0th component is always the permutation index for crossing combinations.
        #    The 1st component is a list of source combination indices. The indices are
        #    organized in two possible ways:
        #        1. One per crossing combination; used in the case that there's a 1-to-1 mapping
        #           between crossing combinations and trials.
        #        2. One per trial; used in the case that combinations have weights (so a
        #           combinations can appear multiple times) or we're generating leftover trials
        #           (so some combinations may be missing).
        #    The 2nd component is a list of combination indices for independent basic factors.

        # Generate the inversion sequence for the selected permutation number.
        # Use the inversion sequence to construct the permutation.
        permutation_indices = self.jth_permutation_indices(crossing_size, trial_count, components[0], pmemo)

        permutation = list(map(lambda i: self._crossing_instances[i], permutation_indices))

        # Generate the source combinations for the selected sequence.
        source_combinations = cast(List[dict], [])
        for i, p in enumerate(permutation_indices):
            if trial_count == len(self._crossing_instances) and self._crossing_is_unweighted:
                component_for_p = components[1][p]
            else:
                component_for_p = components[1][i]
            source_combination_index_for_component = self._valid_source_combinations_indices[p][component_for_p]
            source_combinations.append(self._source_combinations[source_combination_index_for_component])

        # Generate the combinations for independent basic factors
        independent_factor_combinations = cast(List[dict], [{}] *trial_count)
        if self._ind_factor_levels:
            for j, (fi, levels) in enumerate(self._ind_factor_levels):
                independent_combination_idx = components[2][j]
                combo = compute_jth_combination(trial_count, len(levels), independent_combination_idx)
                for i in range(trial_count):
                    if not independent_factor_combinations[i]:
                        independent_factor_combinations[i] = {fi : levels[combo[i]]}
                        continue
                    independent_factor_combinations[i][fi] = levels[combo[i]]

        # 5. Merge the selected levels gathered so far to facilitate computing the uncrossed derived factor levels.
        trial_values = cast(List[dict], [{}] * trial_count)
        for t in range(trial_count):
            trial_values[t] = {**permutation[t], **source_combinations[t], **independent_factor_combinations[t]}

        return trial_values

    def jth_permutation_indices(self, crossing_size: int, trial_count: int, component: int, pmemo: PermutationMemo):
        if self.__complex_crossing_instances == 1 and self._crossing_is_unweighted:
            return compute_jth_permutation_prefix(crossing_size, trial_count, component)
        else:
            return compute_jth_prefix_of_permutations_with_copies(crossing_size, self._m_or_counters,
                                                                  trial_count, component, pmemo)

    def generate_preamble_sample(self, sequence_number: int) -> dict:
        run = cast(dict, {})
        if self._preamble_size == 0:
            assert sequence_number == 0
            return run
        for f, levels in self._basic_factor_levels:
            trials = []
            for _ in range(self._preamble_size):
                n = sequence_number % len(levels)
                sequence_number =  sequence_number // len(levels)
                trials.append(levels[n])
            run[f] = trials
        return self._fill_in_derived(run, self._sorted_derived_factors, 0, self._preamble_size)

    def fill_in_nonpreamble_uncrossed_derived(self, run: dict, trials_per_run: int) -> dict:
        # Note: "uncrossed" includes crossed derived that have complex windows
        return self._fill_in_derived(run, self._sorted_uncrossed_derived_and_complex_derived, self._preamble_size, trials_per_run)

    def _fill_in_derived(self, run: dict, sorted_factors: List[DerivedFactor], start: int, end: int) -> dict:
        for df in sorted_factors:
            if start > 0:
                trials = run[df][:start]
            else:
                trials = []
            for i in range(start, end):
                if df.applies_to_trial(i+1):
                    trials.append(df.select_level_for_sample(i, run))
                else:
                    trials.append(None)
            run[df] = trials
        return run

    """
    Generates all the crossings, indexed by factor name for easy lookup later.
    [
        {'factor': 'level', 'factor': 'level', ...},
        ...
    ]
    """
    def __generate_crossing_instances(self) -> List[dict]:
        crossing = self._partitions.get_crossed_noncomplex_factors()
        level_lists = [list(f.levels) for f in crossing]
        crossings = [{crossing[i]: level for i,level in enumerate(levels)} for levels in product(*level_lists)]
        return list(filter(lambda c: not self._block.is_excluded_or_inconsistent_combination(c), crossings))

    def __count_complex_crossing_instances(self) -> int:
        crossing = self._partitions.get_crossed_complex_factors()
        if len(crossing) == 0:
            return 1
        else:
            level_lists = [list(f.levels) for f in crossing]
            crossings = [{crossing[i]: level for i,level in enumerate(levels)} for levels in product(*level_lists)]
            return sum([(0 if self._block.is_excluded_combination(c) else combination_weight(tuple(c.values())))
                        for c in crossings])

    def __generate_source_combinations(self) -> List[dict]:
        ubs = self._partitions.get_uncrossed_basic_source_factors()
        level_lists = [list(f.levels) for f in ubs]
        return [{ubs[i]: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __count_solutions(self,
                          first_n: int,
                          components_shape: RandomComponentsShape,
                          pmemo: PermutationMemo,
                          valid_source_combinations_indices: Optional[List[List[int]]],
                          ind_factor_levels: Optional[List[Tuple[Factor, List[SimpleLevel]]]]):
        """Returns the number of solutions for a single round. When
        minimum_trials increases the number of rounds, then we have
        roughly a power of this result. The first_n argument is
        between 1 and the crossing size, and it indicates how many of
        the possible crossing-size trials we'll keep in a run. If we
        need more trials than the crossing size, we'll pick multiple
        crossing-size runs and concatenate them.
        """
        ##############################################################
        # Permutations of crossing instances
        #
        # In the case of derived factors in the crossing, we consider only
        # those with simple windows. Derived factors with simple windows
        # can be combined with all other combinations, otherwise the design
        # has no solutions, anyway (and we'll detect that by discovering zero
        # allowed combinations in "Uncrossed Dependent Factors" below).
        # Derived factors with complex windows, meanwhile, mean that we
        # have to use rejection sampling, and so it's ok for the
        # "Uncrossed Dependent Factors" step to over-approximate the allowed
        # combinations.
        q = len(self._crossing_instances)
        m = self.__complex_crossing_instances
        n = q * m
        if m == 1 and self._crossing_is_unweighted:
            permutations = factorial(n)
            # We want only the first_n of the trials, so permutations of the
            # remaining trials would all count the same:
            if first_n != n:
                permutations = permutations // factorial(n - first_n)
        else:
            # We need n = q*m trials (well, the first_n of those). But we don't
            # want to distinguish among combinations where the noncomplex crossing
            # component (with m choices of each) is the same. More generally, we
            # weight each combination by a multple of m
            permutations = count_prefixes_of_permutations_with_copies(q, self._m_or_counters, first_n, pmemo)

        solution_count = permutations
        components_shape.crossings_shape = permutations

        ##############################################################
        # Uncrossed Dependent Factors
        #
        # For each combination of crossed factors, determine the possible
        # completions with uncrossed basic factors. We consider derived
        # factors only in the way that they limit completions via
        # uncrossed basic factors.
        level_combinations = self.__generate_source_combinations()

        # Keep only allowed combos for each permutation
        for ci in self._crossing_instances:
            sc_indices = list(range(len(self._source_combinations)))
            for sc_idx, sc in enumerate(self._source_combinations):
                # Apply the derivation fn for each DF in the crossing for this instance and make sure it
                # return true for this level combination. If it doesn't, then remove this combination.
                # The "crossing" here doesn't include crossed derived factors with complex windows,
                # though, so we can only perform this filtering for a derived factor that does
                # not depend on a complex-window derived factor.
                merged_levels = {**ci, **sc}
                for df in self._partitions.get_crossed_noncomplex_derived_factors():
                    # Not yet separating complex:
                    # assert not df.has_complex_window
                    if not df.has_complex_window:
                        w = merged_levels[df].window
                        if not w.predicate(*[(merged_levels[f]).name for f in w.factors]):
                            sc_indices.remove(sc_idx)

            components_shape.combinations_shapes.append(len(sc_indices))
            if isinstance(valid_source_combinations_indices, list):
                valid_source_combinations_indices.append(sc_indices)

        # When we're not generating a leftover or weighted sequence, every crossing will appear
        # once somewhere in the sequence, so we get to pick from all possible completions
        # of all combinations; in that case, we can just multiply the new segment
        # lengths into `solution_count`. Otherwise, we need to consider every choice of
        # `first_n` crossing combinations, and then multiply the 
        if first_n == len(self._crossing_instances) and self._crossing_is_unweighted:
            solution_count *= reduce(op.mul, components_shape.combinations_shapes, 1)
        else:
            solution_count = self.sum_combination_products(solution_count,
                                                           first_n,
                                                           components_shape.combinations_shapes,
                                                           self._m_or_counters,
                                                           pmemo)

        ##############################################################
        # Uncrossed Independent Factors
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        for f in u_b_i:
            levels = list(filter(lambda l: not self._block.is_excluded_combination({f: l}), f.levels));
            if ind_factor_levels is not None:
                ind_factor_levels.append((f, levels))
            possibilities = pow(len(levels), first_n)
            solution_count *= possibilities
            components_shape.independent_shapes.append(possibilities)

        return solution_count

    def __count_preamble_solutions(self):
        if self._preamble_size == 0:
            return 1
        combos = 1
        for f in self._partitions.get_basic_factors():
            levels = list(filter(lambda l: not self._block.is_excluded_combination({f: l}), f.levels));
            self._basic_factor_levels.append((f, levels))
            combos *= len(levels)
        return pow(combos, self._preamble_size)

    def sum_combination_products(self, solution_count: int, first_n: int, shapes: List[int], m_or_counters: Union[int, List[int]],
                                 pmemo: PermutationMemo):
        if all([s == shapes[0] for s in shapes]) and isinstance(m_or_counters, int):
            # Every choice of `first_n` combinations produces the same number of possibilities
            # for source combinations in each trial
            return solution_count * pow(shapes[0], first_n)
        else:
            # Need to sum over the `solution_count` possible ways of picking `first_n` combinations,
            # getting the product of options across trials for each combination. Iterating over all
            # permutations is the slow way around, since the order within the permutation doesn't
            # matter (and we end up ignoring `_m_or_counters`), so there's room for improvement here:
            s = 0
            crossing_size = len(self._crossing_instances)
            for i in range(0, solution_count):
                permutation = compute_jth_prefix_of_permutations_with_copies(crossing_size, m_or_counters, first_n, i, pmemo)
                prod = 1
                for p in permutation:
                    prod *= shapes[p]
                s += prod
            return s

UniformCombinatoricSamplingStrategy = RandomGen
