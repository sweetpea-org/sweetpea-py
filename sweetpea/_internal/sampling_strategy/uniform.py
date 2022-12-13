from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.sampling_strategy.unigen import UniGen
from sweetpea._internal.sampling_strategy.random import RandomGen

"""
This represents a uniform sampling strategy where a specific strategy
is selected automatically. When requsting more than one sample, however,
the selected strategy may or may not sample with repetition.
"""
class UniformGen(Gen):
    
    @staticmethod
    def class_name():
        return 'UniformGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        if block.complex_factors_or_constraints:
            return UniGen.sample(block, sample_count)
        else:
            return RandomGen.sample(block, sample_count)
