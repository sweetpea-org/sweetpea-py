from math import ceil, log
from tqdm import tqdm
import sys

from typing import List, cast

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.core import sample_uniform, CNF

"""
This strategy relies UniGen to sample uniformly from possible solutions.
"""
class UniGen(Gen):

    @staticmethod
    def class_name():
        return 'UniGen'

    @staticmethod
    def sample(block: Block, sample_count: int, min_search: bool=False, use_cmsgen=False) -> SamplingResult:

        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_uniform(
            sample_count,
            CNF(backend_request.get_cnfs_as_json()),
            backend_request.fresh - 1,
            block.variables_per_sample(),
            backend_request.get_requests_as_generation_requests(),
            use_docker=False,
            use_cmsgen=use_cmsgen)

        result = list(map(lambda s: Gen.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})
