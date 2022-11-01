"""This module provides functionality for partitioning designs into subsets of
factors.
"""


from sweetpea.blocks import Block
from sweetpea.primitives import DerivedFactor


class DesignPartitions():
    """Encapsulates the logic for partitioning a design into specific subsets
    of factors. For example, factors which are in the design, but not in the
    crossing, or not constrained by any derived levels, etc.
    """

    def __init__(self, block: Block) -> None:
        self._block = block
        self._crossed = None

    def get_crossed_noncomplex_factors(self):
        """Only gets factors for the first crossing."""
        if self._crossed:
            return self._crossed
        result = self._block.crossings[0]
        result = list(filter(lambda f: not f.has_complex_window, result))
        self._crossed = result
        return result

    def get_crossed_noncomplex_derived_factors(self):
        return list(filter(lambda f: isinstance(f, DerivedFactor), self.get_crossed_noncomplex_factors()))

    def get_crossed_complex_factors(self):
        """Only gets factors for the first crossing."""
        result = []
        for f in self._block.crossings[0]:
            if f.has_complex_window:
                if f not in result:
                    result.append(f)
        return result

    def get_uncrossed_and_complex_factors(self):
        crossed = self.get_crossed_noncomplex_factors()
        return list(filter(lambda f: f not in crossed, self._block.act_design))

    def get_source_factors(self):
        # Source factors are depended on by at least one noncomplex derived factor in the crossed factors.
        source_factors = []
        for derived_factor in self.get_crossed_noncomplex_derived_factors():
            for source_factor in derived_factor.levels[0].window.factors:
                if source_factor not in source_factors:
                    source_factors.append(source_factor)
        return source_factors

    def get_uncrossed_basic_factors(self):
        uncrossed = self.get_uncrossed_and_complex_factors()
        return list(filter(lambda f: not isinstance(f, DerivedFactor), uncrossed))

    def get_uncrossed_basic_source_factors(self):
        source_factors = self.get_source_factors()
        return list(filter(lambda f: f in source_factors, self.get_uncrossed_basic_factors()))

    def get_uncrossed_basic_independent_factors(self):
        source_factors = self.get_source_factors()
        return list(filter(lambda f: f not in source_factors, self.get_uncrossed_basic_factors()))

    def get_uncrossed_derived_and_complex_derived_factors(self):
        return list(filter(lambda f: isinstance(f, DerivedFactor), self.get_uncrossed_and_complex_factors()))

    def get_basic_factors(self):
        return list(filter(lambda f: not isinstance(f, DerivedFactor), self._block.act_design))

    def get_derived_factors(self):
        return list(filter(lambda f: isinstance(f, DerivedFactor), self._block.act_design))
