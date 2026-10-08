"""Gurobi-backed variant of :class:`.IterateSATGen`.

This strategy is intentionally undocumented: it is kept importable so that
existing code continues to work, but it is not advertised in the API
reference or the example programs.

It is functional -- with `pip install gurobipy` it produces valid samples --
but it requires a dependency that is declared nowhere in SweetPea's
packaging, it is limited by Gurobi's free license size cap, it has no test
coverage, and benchmarking in Sep 2026 found it 1.2x to 3.5x *slower* than
IterateSATGen across nine designs, with the gap widening on designs with
more crossing structure. The motivating idea -- that an ILP encoding handles
SweetPea's cardinality constraints better than a CNF encoding -- did not pay
off at these problem sizes.
"""

from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.core import CNF
from sweetpea._internal.core.generate.sample_ilp import sample_ilp_iterate

class IterateILPGen(Gen):

    @staticmethod
    def class_name():
        return 'IterateILPGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        backend_request = block.build_backend_request()
        if block.show_errors():
            return SamplingResult([], {})

        solutions = sample_ilp_iterate(sample_count,
                                       CNF(backend_request.get_cnfs_as_json()),
                                       block.variables_per_sample(),
                                       backend_request.get_requests_as_generation_requests())

        result = list(map(lambda s: Gen.decode(block, s.assignment), solutions))
        return SamplingResult(result, {})
