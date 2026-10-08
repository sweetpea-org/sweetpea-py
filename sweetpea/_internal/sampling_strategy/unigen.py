from math import ceil, log
from tqdm import tqdm
import sys

from typing import List, Optional, cast

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.core import sample_uniform, CNF

"""
This strategy relies UniGen to sample uniformly from possible solutions.

UniGen's guarantee is *approximate* uniformity: each satisfying trial sequence
is produced with probability between 1/((1+epsilon) * N) and (1+epsilon)/N,
where N is the number of satisfying sequences, and that guarantee itself holds
with probability at least 1-delta. Leaving `epsilon` and `delta` as None uses
the underlying sampler's own defaults (epsilon=0.8, delta=0.2).
"""
class UniGen(Gen):

    def __init__(self,
                 seed: Optional[int] = None,
                 epsilon: Optional[float] = None,
                 delta: Optional[float] = None):
        """
        :param seed: Random seed. ``None`` (the default) draws a fresh seed for
                     every call, so repeated runs differ. Supplying an integer
                     makes a run reproducible.
        :param epsilon: Uniformity tolerance. ``None`` uses the sampler's
                        default of 0.8. Smaller values tighten the guarantee at
                        a steep cost in running time.
        :param delta: Confidence parameter; the guarantee holds with
                      probability at least 1-delta. ``None`` uses the sampler's
                      default of 0.2.
        """
        self.seed = seed
        self.epsilon = epsilon
        self.delta = delta

    def __str__(self):
        return UniGen.class_name()

    @staticmethod
    def class_name():
        return 'UniGen'

    @staticmethod
    def _run(block: Block,
             sample_count: int,
             use_cmsgen: bool = False,
             seed: Optional[int] = None,
             epsilon: Optional[float] = None,
             delta: Optional[float] = None) -> SamplingResult:

        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_uniform(
            sample_count,
            CNF(backend_request.get_cnfs_as_json()),
            backend_request.fresh - 1,
            block.variables_per_sample(),
            backend_request.get_requests_as_generation_requests(),
            use_cmsgen=use_cmsgen,
            seed=seed,
            epsilon=epsilon,
            delta=delta)

        result = list(map(lambda s: Gen.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})

    @staticmethod
    def sample(block: Block, sample_count: int, use_cmsgen=False) -> SamplingResult:
        return UniGen._run(block, sample_count, use_cmsgen=use_cmsgen)

    def sample_object(self, block: Block, sample_count: int) -> SamplingResult:
        return UniGen._run(block, sample_count,
                           use_cmsgen=False,
                           seed=self.seed,
                           epsilon=self.epsilon,
                           delta=self.delta)
