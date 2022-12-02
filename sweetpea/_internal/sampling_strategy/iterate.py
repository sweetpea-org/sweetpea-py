from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
from sweetpea._internal.sampling_strategy.random import RandomGen

"""
This represents a strategy where we "sample" just by using some
solver repeatedly to produce unique (but not necessarily uniform) samples.
A specific strategy is selected automatically.
"""
class IterateGen(Gen):
    
    @staticmethod
    def class_name():
        return 'NonUniformGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        if block.complex_factors_or_constraints:
            return IterateSATGen.sample(block, sample_count)
        else:
            return RandomGen.sample(block, sample_count)
