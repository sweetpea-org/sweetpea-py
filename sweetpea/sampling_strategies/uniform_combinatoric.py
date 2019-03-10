import operator as op

from functools import reduce
from itertools import product
from math import factorial

from sweetpea.blocks import Block, FullyCrossBlock
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

        # 2. Count the number of solutions and prepare the data structures for sample construction.

        # 3. Generate samples.

        return SamplingResult([], {})

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

        # Needs to be called last.
        self._solution_count = self.__count_solutions()

    def solution_count(self):
        return self._solution_count

    """
    Generates all the crossings, indexed by factor name for easy lookup later.
    [
        {'factor': 'level', 'factor': 'level', ...},
        ...
    ]
    """
    def __generate_crossing_instances(self):
        crossing = self._partitions.get_crossed_factors()
        level_lists = [list(map(get_level_name, f.levels)) for f in crossing]
        return [{crossing[i].name: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __get_source_combinations(self):
        ubs = self._partitions.get_uncrossed_basic_source_factors()
        level_lists = [list(map(get_level_name, f.levels)) for f in ubs]
        return [{ubs[i].name: level for i,level in enumerate(levels)} for levels in product(*level_lists)]

    def __count_solutions(self):
        ##############################################################
        # Permutations of crossing instances
        n = self._block.crossing_size()
        n_factorial = factorial(n)

        ##############################################################
        # Uncrossed Dependent Factors
        level_combinations = self.__get_source_combinations()

        ci_level_combos = []
        # Keep only allowed combos for each permutation
        for ci in self._crossing_instances:
            lc_copy = level_combinations.copy()
            for lc in level_combinations:
                # Apply the derivation fn for each DF in the crossing for this instance and make sure it returns
                # true for this level combination. If it doesn't, then remove this combination.
                merged_levels = {**ci, **lc}
                for df in self._partitions.get_crossed_factors_derived():
                    w = df.get_level(merged_levels[df.name]).window
                    if not w.fn(*[merged_levels[f.name] for f in w.args]):
                        lc_copy.remove(lc)

            ci_level_combos.append(lc_copy)

        ##############################################################
        # Uncrossed Independent Factors
        u_b_i_counts = []
        u_b_i = self._partitions.get_uncrossed_basic_independent_factors()
        for f in u_b_i:
            u_b_i_counts.append(pow(len(f.levels), n))

        count = n_factorial * reduce(op.mul, map(len, ci_level_combos), 1) * reduce(op.mul, u_b_i_counts, 1)
        return count
