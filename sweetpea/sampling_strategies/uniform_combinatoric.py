import operator as op
import random
import numpy as np

from functools import reduce
from itertools import product
from math import factorial, ceil
from typing import List, cast, Tuple, Dict, Optional

from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.combinatorics import extract_components, compute_jth_inversion_sequence, construct_permutation, compute_jth_combination
from sweetpea.design_partitions import DesignPartitions
from sweetpea.logic import And
from sweetpea.primitives import get_external_level_name
from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.constraints import Exclude, _KInARow, ExactlyKInARow, AtMostKInARow


class UniformCombinatoricSamplingStrategy(SamplingStrategy):
    """This strategy represents the ideal. Valid sequences are uniformly
    sampled via a bijection from natural numbers to valid trial sequences.

    Right now, the intent is that this will only work for designs without
    complex windows. Once we get that far, we can think about what steps are
    needed to support complex windows. (:class:`.Transition`, etc.)

    This also doesn't quite work yet for :class:`._KInARow` constraints, which
    represent a similar obstacle as the complex windows. However, it will still
    accept designs with constraints. When such designs are given, it will do
    rejection sampling to ensure that only valid sequences are returned. The
    metrics dictionary will include data pertaining to the number of samples
    rejected for each final sample, as well as an average. (On average, how
    many samples need to be generated before one is found that is
    satisfactory?)
    """

    def __str__(self):
        return 'Uniform Combinatoric Sampling Strategy'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        # 1. Validate the block. Only FullyCrossBlock, No complex windows allowed.
        UniformCombinatoricSamplingStrategy.__validate(block)
        metrics = {}

        # 2. Count how many solutions there are. The enumerator will notice
        # the crossing size and minimum-trial request, and it will be prepared
        # to generate runs of a crossing-size length or "leftover" length.
        enumerator = UCSolutionEnumerator(cast(FullyCrossBlock, block))
        metrics['solution_count'] = enumerator.solution_count()

        if (enumerator.solution_count() == 0):
            return SamplingResult([], metrics)

        # Select KInARow constraints to check for rejection sampling.
        constraints = list(filter(lambda c: isinstance(c, _KInARow), block.constraints))

        # 3. Generate samples.
        rejection_sampling_enabled = False
        metrics['rejections'] = []
        sampled = 0
        rejected = 0
        total_rejected = 0
        crossing_size = cast(FullyCrossBlock, block).crossing_size();
        rounds_per_run = max(block.min_trials, crossing_size) // crossing_size
        leftover = max(block.min_trials, crossing_size) % crossing_size
        samples = cast(List[dict], [])
        used_keys = cast(Dict[Tuple[int, ...], bool], {})
        while sampled < sample_count:
            if len(used_keys) == (pow(enumerator.solution_count(), rounds_per_run)
                                  * enumerator.leftover_solution_count()):
                break

            solution_variabless = enumerator.generate_random_samples(rounds_per_run, leftover, used_keys)
            used_keys[enumerator.extract_sequence_key(solution_variabless)] = True

            # Combine randomly selected crossing-sized runs plus a leftover-sized run
            # into one complete run with the requested number of trials.
            run = cast(dict, {})
            for round in range(0, rounds_per_run + (1 if leftover > 0 else 0)):
                run = UniformCombinatoricSamplingStrategy.__combine_round(run, solution_variabless[round][1])

            if rejection_sampling_enabled:
                if UniformCombinatoricSamplingStrategy.__are_constraints_violated(block, run):
                    rejected += 1
                    continue

            metrics['rejections'].append(rejected)
            total_rejected += rejected
            rejected = 0
            sampled += 1

            samples.append(run)

        metrics['sample_count'] = sample_count
        metrics['total_rejected'] = total_rejected
        metrics['avg_rejected'] = total_rejected / sample_count

        return SamplingResult(samples, metrics)

    @staticmethod
    def __are_constraints_violated(block: Block, sample: dict) -> bool:
        constraints = cast(List[_KInARow], filter(lambda c: isinstance(c, _KInARow), block.constraints))
        for c in constraints:
            factor_name = c.level[0]
            level_name = c.level[1]

            level_list = sample[factor_name]
            counts = []
            count = 0
            for l in level_list:
                if count > 0 and l != level_name:
                    counts.append(count)
                    count = 0
                elif l == level_name:
                    count += 1

            if count > 0:
                counts.append(count)

            fn = op.eq
            if isinstance(c, ExactlyKInARow):
                fn = op.eq
            elif isinstance(c, AtMostKInARow):
                fn = op.le
            else:
                raise ValueError("Unexpected constraint found! {}".format(c))

            if not all(map(lambda n: fn(n, c.k), counts)):
                return True

        return False

    @staticmethod
    def __validate(block: Block) -> None:
        if not isinstance(block, FullyCrossBlock):
            raise ValueError('The uniform combinatoric sampling strategy currently only supports FullyCrossBlock.')

        for c in block.constraints:
            if isinstance(c, Exclude):
                raise ValueError('The uniform combinatoric sampling strategy currently does not support Exclude constraints.')

        for f in block.act_design:
            if f.has_complex_window:
                raise ValueError('Found factor in design with complex window! Factor={} The uniform combinatoric sampling strategy currently does not support designs containing factors with complex windows. Sorry!'.format(f.factor_name))

    @staticmethod
    def __combine_round(run: dict, round: dict) -> dict:
        if len(run) == 0:
            return round
        else:
            new_run = {}
            for key in round:
                new_run[key] = run[key] + round[key]
            return new_run


"""
Given a fully crossed block with no complex windows, this class stores the data structures and logic for enumerating
valid trial sequences in the design.
"""
class UCSolutionEnumerator():

    def __init__(self, block: FullyCrossBlock) -> None:
        self._block = block
        self._partitions = DesignPartitions(block)
        self._crossing_instances = self.__generate_crossing_instances()
        self._source_combinations = self.__generate_source_combinations()
        self._segment_lengths = cast(List[int], []) # Will be populated by solution counting

        # Maintains a lookup for valid source combinations for a permutation.
        # Example [[2, 3], ...] means that for permutation 0, indices 2 and 3 in the source combinations
        # list are allowed.
        self._valid_source_combinations_indices = cast(List[List[int]], []) # Will be populated by solution counting

        # Call `__count_solutions` after everything else is set up.
        crossing_size = block.crossing_size()
        self._segment_lengths = cast(List[int], [])
        self._solution_count = self.__count_solutions(crossing_size,
                                                      self._segment_lengths,
                                                      self._valid_source_combinations_indices)
        self._leftover_segment_lengths = cast(List[int], [])
        self._leftover_solution_count = 1
        leftover = max(block.min_trials, crossing_size) % crossing_size;
        if (leftover != 0):
            self._leftover_solution_count = self.__count_solutions(leftover,
                                                                   self._leftover_segment_lengths,
                                                                   None)

    def solution_count(self):
        return self._solution_count

    def leftover_solution_count(self):
        return self._leftover_solution_count

    def generate_random_samples(self, n: int, leftover: int, sampled: Dict[Tuple[int, ...], bool]) -> List[Tuple[int, dict]]:
        # Select a sequence of n random numbers, each from the range of solutions.
        # If `leftover` is not zero, then tack on one more sequence that is shorter
        # than the crossing size.
        # Then, make sure we haven't already picked the same sequence according to `sampled`.
        # This rejection-based approach is probably ok for realistic experiments,
        # where we're unlikely to want a number of samples close to the number of solutions
        # at the same time that there are a lot of solutions.
        sequence_key = (tuple([random.randrange(0, self._solution_count) for i in range(n)]),
                        random.randrange(0, self._leftover_solution_count))
        while tuple(list(sequence_key[0]) + ([sequence_key[1]] if leftover > 0 else [])) in sampled:
            sequence_key = (tuple([random.randrange(0, self._solution_count) for i in range(n)]),
                            random.randrange(0, self._leftover_solution_count))
        return (list(map(lambda sequence_number: (sequence_number, self.generate_sample(sequence_number)),
                         sequence_key[0]))
                + ([(sequence_key[1],
                     self.generate_leftover_sample(sequence_key[1], leftover))] if leftover > 0 else []))

    def extract_sequence_key(self, solution_variabless: List[Tuple[int, dict]]) -> Tuple[int, ...]:
        return tuple(map(lambda sv: sv[0], solution_variabless))

    def generate_sample(self, sequence_number: int) -> dict:
        trial_values = self.generate_trail_values(sequence_number, self._block.crossing_size(), self._segment_lengths)
        return self._trial_values_to_experiment(trial_values)

    def generate_leftover_sample(self, sequence_number: int, leftover: int) -> dict:
        trial_values = self.generate_trail_values(sequence_number, leftover, self._leftover_segment_lengths)
        return self._trial_values_to_experiment(trial_values)

    def _trial_values_to_experiment(self, trial_values: List[dict]) -> dict:
        experiment = cast(dict, {})
        for trial_number, trial_value in enumerate(trial_values):
            for factor, level in trial_value.items():
                if factor.factor_name not in experiment:
                    experiment[factor.factor_name] = []
                experiment[factor.factor_name].append(level.name)
        return experiment

    def generate_trail_values(self, sequence_number: int, trial_count: int, segment_lengths: List[int]) -> List[dict]:
        # 1. Extract the component pieces (permutation, each combination setting, etc)
        #    The 0th component is always the permutation index.
        #    The 1st-nth components are always the source combination indices for each trial in the sequence
        #    Any following components are the combination indices for independent basic factors.
        components = extract_components(segment_lengths, sequence_number)

        # 2. Generate the inversion sequence for the selected permutation number.
        #    Use the inversion sequence to construct the permutation.
        inversion_sequence = compute_jth_inversion_sequence(trial_count, components[0])
        permutation_indices = construct_permutation(inversion_sequence)
        permutation = list(map(lambda i: self._crossing_instances[i], permutation_indices))

        # 3. Generate the source combinations for the selected sequence.
        source_combinations = cast(List[dict], [])
        for i, p in enumerate(permutation_indices):
            component_for_p = components[p + 1]
            source_combination_index_for_component = self._valid_source_combinations_indices[p][component_for_p]
            source_combinations.append(self._source_combinations[source_combination_index_for_component])

        # 4. Generate the combinations for independent basic factors
        independent_factor_combinations = cast(List[dict], [{}] *trial_count)
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        if u_b_i:
            independent_combination_idx = components[trial_count+1]
            for f in u_b_i:
                combo = compute_jth_combination(trial_count, len(f.levels), independent_combination_idx)
                for i in range(trial_count):
                    if not independent_factor_combinations[i]:
                        independent_factor_combinations[i] = {f : f.levels[combo[i]]}
                        continue
                    independent_factor_combinations[i][f] = f.levels[combo[i]]

        # 5. Merge the selected levels gathered so far to facilitate computing the uncrossed derived factor levels.
        trial_values = cast(List[dict], [{}] * trial_count)
        for t in range(trial_count):
            trial_values[t] = {**permutation[t], **source_combinations[t], **independent_factor_combinations[t]}

        # 6. Generate uncrossed derived level values
        u_d = self._partitions.get_uncrossed_derived_factors()
        for f in u_d:
            for t in range(trial_count):
                # For each level in the factor, see if the derivation function is true.
                for level in f.levels:
                    if level.window.fn(*[(trial_values[t][f]).name for f in level.window.args]):
                        trial_values[t][f] = level

        return trial_values

    """
    Generates all the crossings, indexed by factor name for easy lookup later.
    [
        {'factor': 'level', 'factor': 'level', ...},
        ...
    ]
    """
    def __generate_crossing_instances(self) -> List[dict]:
        crossing = self._partitions.get_crossed_factors()
        level_lists = [list(f.levels) for f in crossing]
        return [{crossing[i]: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __generate_source_combinations(self) -> List[dict]:
        ubs = self._partitions.get_uncrossed_basic_source_factors()
        level_lists = [list(f.levels) for f in ubs]
        return [{ubs[i]: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __count_solutions(self,
                          first_n: int,
                          segment_lengths: List[int],
                          valid_source_combinations_indices: Optional[List[List[int]]]):
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
        n = self._block.crossing_size()
        n_factorial = factorial(n) // factorial(n - first_n)
        segment_lengths.append(n_factorial)

        ##############################################################
        # Uncrossed Dependent Factors
        level_combinations = self.__generate_source_combinations()

        # Keep only allowed combos for each permutation
        for ci in self._crossing_instances:
            sc_indices = list(range(len(self._source_combinations)))
            for sc_idx, sc in enumerate(self._source_combinations):
                # Apply the derivation fn for each DF in the crossing for this instance and make sure it returns
                # true for this level combination. If it doesn't, then remove this combination.
                merged_levels = {**ci, **sc}
                for df in self._partitions.get_crossed_factors_derived():
                    w = merged_levels[df].window
                    if not w.fn(*[(merged_levels[f]).name for f in w.args]):
                        sc_indices.remove(sc_idx)

            segment_lengths.append(len(sc_indices))
            if isinstance(valid_source_combinations_indices, list):
                valid_source_combinations_indices.append(sc_indices)

        ##############################################################
        # Uncrossed Independent Factors
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        for f in u_b_i:
            segment_lengths.append(pow(len(f.levels), first_n))

        return reduce(op.mul, segment_lengths, 1)
