from typing import List, cast

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.core import CNF, sample_non_uniform

"""
This represents a strategy where we "sample" just by using a SAT
solver repeatedly to produce unique (but not uniform) samples.
"""
class IterateSATGen(Gen):

    @staticmethod
    def class_name():
        return 'IterateSATGen'

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

        result = list(map(lambda s: Gen.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})

