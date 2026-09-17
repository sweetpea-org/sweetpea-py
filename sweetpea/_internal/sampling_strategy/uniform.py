from typing import Optional

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

    def __init__(self,
                 seed: Optional[int] = None,
                 epsilon: Optional[float] = None,
                 delta: Optional[float] = None):
        """
        :param seed: Random seed, forwarded to whichever strategy is selected.
                     ``None`` (the default) draws a fresh seed for every call,
                     so repeated runs differ. An integer makes a run
                     reproducible.
        :param epsilon: Uniformity tolerance, forwarded to :class:`.UniGen`.
                        Ignored when the design routes to :class:`.RandomGen`,
                        which samples exactly uniformly and so needs no
                        tolerance.
        :param delta: Confidence parameter, forwarded to :class:`.UniGen`.
                      Ignored for the same reason as ``epsilon``.
        """
        self.seed = seed
        self.epsilon = epsilon
        self.delta = delta

    def __str__(self):
        return UniformGen.class_name()

    @staticmethod
    def class_name():
        return 'UniformGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        if block.complex_factors_or_constraints:
            return UniGen.sample(block, sample_count)
        else:
            return RandomGen.sample(block, sample_count)

    def sample_object(self, block: Block, sample_count: int) -> SamplingResult:
        if block.complex_factors_or_constraints:
            return UniGen(seed=self.seed,
                          epsilon=self.epsilon,
                          delta=self.delta).sample_object(block, sample_count)
        else:
            # RandomGen samples exactly uniformly, so `epsilon` and `delta`,
            # which bound UniGen's deviation from uniform, do not apply.
            return RandomGen(seed=self.seed).sample_object(block, sample_count)
