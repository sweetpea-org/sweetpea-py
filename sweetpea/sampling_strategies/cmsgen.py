from typing import List, cast

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.sampling_strategies.unigen import UnigenSamplingStrategy
from sweetpea.blocks import Block


"""
This strategy relies fully on CMSGen to produce the desired number of samples.
"""
class CMSGen(SamplingStrategy):
    # The CMSGen API is similar to Unigen, so we piggy-back on that implementation.

    @staticmethod
    def class_name():
        return 'CMSGen'

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False) -> SamplingResult:
        return UnigenSamplingStrategy.sample(block, sample_count, min_search, use_cmsgen=True)

CMSGenSamplingStrategy = CMSGen
