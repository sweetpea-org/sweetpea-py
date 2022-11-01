from typing import List, cast

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.core import CNF, sample_non_uniform

"""
This represents the non-uniform sampling strategy, in which we 'sample' just by using a SAT
solver repeatedly to produce unique (but not uniform) samples.
"""
class IterateGen(SamplingStrategy):

    @staticmethod
    def class_name():
        return 'IterateGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_non_uniform(sample_count,
                                       CNF(backend_request.get_cnfs_as_json()),
                                       backend_request.fresh - 1,
                                       block.variables_per_sample(),
                                       backend_request.get_requests_as_generation_requests())

        result = list(map(lambda s: SamplingStrategy.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})

NonUniformSamplingStrategy = IterateGen
