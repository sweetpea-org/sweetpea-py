Legacy
======

The :mod:`sweetpea` module exports other names for historical reasons,
but they should not be used in new program.

.. function:: sweetpea.fully_cross_block()

   Use :func:`sweetpea.CrossBlock`.

.. function:: sweetpea.multiple_cross_block()

   Use :func:`sweetpea.MultiCrossBlock`.

.. function:: sweetpea.simplify_experiments()

   Use :func:`sweetpea.experiments_to_tuples`.

.. function:: sweetpea.experiment_to_csv()

   Use :func:`sweetpea.same_experiments_csv`.

.. function:: sweetpea.synthesize_trials_uniform()

   Use :func:`sweetpea.synthesize_trials` with :class:`UniGen`.

.. function:: sweetpea.synthesize_trials_non_uniform()

   Use :func:`sweetpea.synthesize_trials` with :class:`IterateGen`.

.. class:: sweetpea.SimpleLevel

   Use :class:`sweetpea.Level`.

.. class:: sweetpea.DerivationWindow

   Use :class:`sweetpea.Window`.

.. class:: sweetpea.WithinTrialDerivationWindow

   Use :class:`sweetpea.WithinTrial`.

.. class:: sweetpea.TransitionDerivationWindow

   Use :class:`sweetpea.Transition`.

.. function:: sweetpea.exclude

   Use :func:`sweetpea.Exclude`.
              
.. function:: sweetpea.minimum_trials

   Use :func:`sweetpea.MinimumTrials`.
              
.. function:: sweetpea.at_most_k_in_a_row

   Use :func:`sweetpea.AtMostKInARow`.
              
.. function:: sweetpea.at_least_k_in_a_row

   Use :func:`sweetpea.AtLeastKInARow`.
              
.. function:: sweetpea.exactly_k_in_a_row

   Use :func:`sweetpea.ExactlyKInARow`.

.. class:: sweetpea.UnigenSamplingStrategy

   Use :class:`sweetpea.UniGen`.

.. class:: sweetpea.NonUniformSamplingStrategy

   Use :class:`sweetpea.IterateGen`.

.. class:: sweetpea.UniformCombinatoricSamplingStrategy

   Use :class:`sweetpea.RandomGen`.

