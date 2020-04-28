Sampling Strategies
===================

.. class:: sweetpea.sampling_stratgies.unigen.UnigenSamplingStrategy

           Generates trials with some guarantee of uniformity. Unfortunately, this
           stategy is unlikely to succeed for non-trial designs.
           
.. class:: sweetpea.sampling_stratgies.non_uniform.NonUniformSamplingStrategy

           Generates trials by repeatedly finding solutions to an
           experiment design's constraints, but with no guarantee of
           uniform coverage.

.. class:: sweetpea.sampling_stratgies.uniform_combinatoric.UniformCombinatoricSamplingStrategy

           Generates trials with a guarantee of uniformity, but
           currently works only for experiment designs without
           constraints or derived factors.
