from typing import List, cast

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.sampling_strategy.unigen import UniGen
from sweetpea._internal.block import Block


"""
This strategy relies CMSGen to sample from possible solutions in a way that
might be uniform, with without a firm guarantee of uniformity, so that the
lack of correlation would need to be checked independently.
"""
class CMSGen(Gen):
    # The CMSGen API is similar to Unigen, so we piggy-back on that implementation.

    @staticmethod
    def class_name():
        return 'CMSGen'

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False) -> SamplingResult:
        return UniGen.sample(block, sample_count, min_search, use_cmsgen=True)
