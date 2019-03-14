import operator as op
import random

from functools import reduce
from itertools import product
from math import factorial
from typing import List, cast

from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.combinatorics import extract_components, compute_jth_inversion_sequence, construct_permutation, compute_jth_combination
from sweetpea.design_partitions import DesignPartitions
from sweetpea.primitives import get_level_name
from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult


"""
This strategy represents the ideal. Valid sequences are uniformly sampled via a bijection from natural
numbers to valid trial sequences.

Right now, the intent is that this will only work for designs without complex windows. Once we get that
far, we can think about what steps are needed to support complex windows. (Transition, etc.)
"""
class UniformCombinatoricSamplingStrategy(SamplingStrategy):

    def __str__(self):
        return 'Uniform Combinatoric Sampling Strategy'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        # 1. Validate the block. Only FullyCrossBlock, No complex windows allowed.
        UniformCombinatoricSamplingStrategy.__validate(block)

        # 2. Count how many solutions there are.
        enumerator = UCSolutionEnumerator(cast(FullyCrossBlock, block))

        # 3. Generate samples.
        samples = []
        for _ in range(sample_count):
            solution_variables = enumerator.generate_random_sample()
            sample = SamplingStrategy.decode(block, solution_variables)
            samples.append(sample)

        return SamplingResult(samples, {})

    @staticmethod
    def __validate(block: Block) -> None:
        if not isinstance(block, FullyCrossBlock):
            raise ValueError('The uniform combinatoric sampling strategy currently only supports FullyCrossBlock.')

        for f in block.design:
            if f.has_complex_window():
                raise ValueError('Found factor in design with complex window! Factor={} The uniform ' +
                    'combinatoric sampling strategy currently does not support designs containing ' +
                    'factors with complex windows. Sorry!'.format(f.name))


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

        # Needs to be called last.
        self._solution_count = self.__count_solutions()

    def solution_count(self):
        return self._solution_count

    def generate_random_sample(self) -> List[int]:
        # Select a random number from the range of solutions.
        # sequence_number = np.random.randint(0, self._solution_count, dtype=np.long)
        sequence_number = random.randrange(0, self._solution_count)
        return self.generate_sample(sequence_number)

    def generate_sample(self, sequence_number: int) -> List[int]:
        # 1. Extract the component pieces (permutation, each combination setting, etc)
        #    The 0th component is always the permutation index.
        #    The 1st-nth components are always the source combination indices for each trial in the sequence
        #    Any following components are the combination indices for independent basic factors.
        components = extract_components(self._segment_lengths, sequence_number)

        # 2. Generate the inversion sequence for the selected permutation number.
        #    Use the inversion sequence to construct the permutation.
        l = self._block.crossing_size()
        inversion_sequence = compute_jth_inversion_sequence(l, components[0])
        permutation_indices = construct_permutation(inversion_sequence)
        permutation = list(map(lambda i: self._crossing_instances[i], permutation_indices))

        # 3. Generate the source combinations for the selected sequence.
        source_combinations = cast(List[dict], [])
        for i, p in enumerate(permutation_indices):
            component_for_p = components[p + 1]
            source_combination_index_for_component = self._valid_source_combinations_indices[p][component_for_p]
            source_combinations.append(self._source_combinations[source_combination_index_for_component])

        # 4. Generate the combinations for independent basic factors
        independent_factor_combinations = cast(List[List[dict]], [[{}]] * l)
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        for f_idx, independent_combination_idx in enumerate(components[l + 1:]):
            f = u_b_i[f_idx]
            combo = compute_jth_combination(l, len(f.levels), independent_combination_idx)
            combo_dicts = [{f.name: f.levels[level_idx] for level_idx in combo}]
            independent_factor_combinations[f_idx] = combo_dicts

        # 5. Merge the selected levels gathered so far to facilitate computing the uncrossed derived factor levels.
        trial_values = cast(List[dict], [{}] * l)
        for t in range(l):
            i_d_f = {k: v for d in independent_factor_combinations[t] for k, v in d.items()}
            trial_values[t] = {**permutation[t], **source_combinations[t], **i_d_f}

        # 6. Generate uncrossed derived level values
        u_d = self._partitions.get_uncrossed_derived_factors()
        for f in u_d:
            for t in range(l):
                # For each level in the factor, see if the derivation function is true.
                for level in f.levels:
                    if level.window.fn(*[trial_values[t][f.name] for f in level.window.args]):
                        trial_values[t][f.name] = level.name

        # 7. Convert to variable encoding for SAT checking
        solution = cast(List[int], [])
        for trial_number, trial_value in enumerate(trial_values):
            for factor_name, level_name in trial_value.items():
                solution.append(self._block.get_variable(trial_number + 1, (factor_name, level_name)))

        solution.sort()
        return solution

    """
    Generates all the crossings, indexed by factor name for easy lookup later.
    [
        {'factor': 'level', 'factor': 'level', ...},
        ...
    ]
    """
    def __generate_crossing_instances(self) -> List[dict]:
        crossing = self._partitions.get_crossed_factors()
        level_lists = [list(map(get_level_name, f.levels)) for f in crossing]
        return [{crossing[i].name: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __generate_source_combinations(self) -> List[dict]:
        ubs = self._partitions.get_uncrossed_basic_source_factors()
        level_lists = [list(map(get_level_name, f.levels)) for f in ubs]
        return [{ubs[i].name: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __count_solutions(self):
        self._segment_lengths = []
        ##############################################################
        # Permutations of crossing instances
        n = self._block.crossing_size()
        n_factorial = factorial(n)
        self._segment_lengths.append(n_factorial)

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
                    w = df.get_level(merged_levels[df.name]).window
                    if not w.fn(*[merged_levels[f.name] for f in w.args]):
                        sc_indices.remove(sc_idx)

            self._segment_lengths.append(len(sc_indices))
            self._valid_source_combinations_indices.append(sc_indices)

        ##############################################################
        # Uncrossed Independent Factors
        u_b_i_counts = []
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        for f in u_b_i:
            self._segment_lengths.append(pow(len(f.levels), n))

        return reduce(op.mul, self._segment_lengths, 1)
