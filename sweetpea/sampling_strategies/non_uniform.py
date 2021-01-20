from typing import List, cast

from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.blocks import Block
from sweetpea.core import generate_non_uniform_samples

"""
This represents the non-uniform sampling strategy, in which we 'sample' just by using a SAT
solver repeatedly to produce unique (but not uniform) samples.
"""
class NonUniformSamplingStrategy(SamplingStrategy):

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        backend_request = block.build_backend_request()
        if block.errors:
            for e in block.errors:
                print(e)
                if "WARNING" not in e:
                    return SamplingResult([], {})

        solutions = cast(List[dict], [])

        solutions = generate_non_uniform_CNF(sample_count, 
            backend_request.get_cnfs_as_json(), 
            backend_request.fresh - 1,
            block.variables_per_sample(),
            backend_request.get_requests_as_json())

        result = list(map(lambda s: SamplingStrategy.decode(block, s['assignment']), solutions))
        return SamplingResult(result, {})