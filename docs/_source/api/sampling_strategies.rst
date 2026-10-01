.. _sampling_strategies:

Sampling Strategies
===================

.. class:: sweetpea.Gen

           Abstract class for a sampling strategy (i.e., a generator
           of trials).

           A subclass of :class:`.Gen` can be used instead of an
           instance to mean the same sampling strategy as an instance
           with default arguments.

           *Uniformity*: Different subclasses of `Gen` provide
           different guarantees about coverage of the space of possible
           trial sequences. A guarantee of uniformity means that is a
           single trial sequence is requested via
           :func:`.synthesize_trials`, the generated sequence is chosen
           randomly among all trial sequences that fit the constraints
           of the experiment definition, and all such trial sequences
           are eqaully likely to be reported.

           *Replacement*: Different subclasses of :class:`.Gen` provide
           different behaviors when multiple trial sequences are
           requested with a single call to :func:`.synthesize_trials`.
           Some strategies sample with replacement, producing
           independently chosen results. Others sample without
           replacement, which means they are potentially capable of
           counting the total number of trial sequences that satisfy the
           experiment's constraints.

.. class:: sweetpea.UniformGen(seed=None, epsilon=None, delta=None)

           Automatically selects among strategies that provide uniformity.
           Arguments are forwarded to the selected strategy; ``epsilon``
           and ``delta`` are ignored unless :class:`.UniGen` is selected.
           
           *Uniformity*: Generates trials with a guarantee of
           uniformity, as long as only one trial sequence is requested
           at a time.

           *Unspecified Replacement*: Generating multiple trials
           sequences in a call to :func:`.synthesize_trials` may or
           may not produce independent results.

.. class:: sweetpea.IterateGen

           Automatically selects among strategies that implement
           non-replacement for a single request of multiple
           experiments, but the strategy may or may not provide
           uniformity for a single experiment.
           
           *Unspecified Uniformity*: Might not sample uniformly among
           possible experiments.

           *Without Replacement*: Generating multiple trials in one
           call to :func:`.synthesize_trials` produces a list of
           distinct trial sequences. The number of returned
           experiments will be less than the requested number if the
           pool of possible trial sequences is exhausted.

.. class:: sweetpea.UniGen(seed=None, epsilon=None, delta=None)

           *Approximate Uniformity*: Each satisfying trial sequence is
           generated with probability between ``1/((1+epsilon) * N)`` and
           ``(1+epsilon)/N``, where ``N`` is the number of satisfying
           sequences; that guarantee itself holds with probability at
           least ``1-delta``. For an exact guarantee, see
           :class:`.RandomGen`.

           Unfortunately, due to the difficulty of sampling with a
           guarantee, this strategy is unlikely to succeed for
           non-trivial designs.

           *Replacement*: Generating multiple trials in one call to
           :func:`.synthesize_trials` produces independent results. That
           is, the single call is the same as separate calls that each
           generate one sequence of trials.

           :param seed: a random seed; ``None`` draws a fresh seed for
                        each call, and an integer makes a run reproducible
           :type seed: typing.Optional[int]

           :param epsilon: the uniformity tolerance above; ``None`` uses
                           the underlying sampler's default of ``0.8``,
                           and smaller values tighten the guarantee at a
                           cost in running time
           :type epsilon: typing.Optional[float]

           :param delta: the confidence parameter above; ``None`` uses the
                         underlying sampler's default of ``0.2``
           :type delta: typing.Optional[float]

.. class:: sweetpea.CMSGen

           *Quasi-Uniformity*: Generates trials that appear to be
           uniformly chosen based on the available technology for
           detecting non-uniformity. This strategy may perform well in
           terms of sampling possible configurations, despite a having
           no formal guarantee of uniformity.

           *Replacement*: Generating multiple trials in one call to
           :func:`.synthesize_trials` produces independent results. That
           is, the single call is the same as separate calls that each
           generate one sequence of trials.

           
.. class:: sweetpea.RandomGen(acceptable_error=0, seed=None)

           *Uniformity*: Generates trials with a guarantee of
           uniformity. Constraints or derived factors with a window
           greater than 1 can force generation to use rejection
           sampling, which may fail to find instances in a reasonable
           time if the search space is large.

           *Without Replacement*: When multiple trials are generated
           in one call to :func:`.synthesize_trials`, each of the
           results is constrained to be distinct. The number of
           returned experiments will be less than the requested number
           if the pool of possible trial sequences is exhausted.

           :param acceptable_error: With derived factors in the
                                    crossing, a number of combinations
                                    with those levels that are allowed
                                    to be missing (in which case other
                                    combinations will be duplicated);
                                    this parameter weakens the
                                    rejection step of rejection
                                    sampling, which can be useful when
                                    samples that match all constraints
                                    of the experiment prove difficult
                                    to find
           :type acceptable_error: int

           :param seed: a random seed; ``None`` leaves the generators
                        unseeded, and an integer makes a run reproducible
                        by seeding the process-wide ``random`` and
                        ``numpy`` generators
           :type seed: typing.Optional[int]
           
.. class:: sweetpea.IterateSATGen

           *Non-Uniformity*: Generates trials by repeatedly finding
           solutions to an experiment design's constraints, but with
           no guarantee of uniform coverage or even randomness (i.e.,
           each separate use of :func:`.synthesize_trials` with this
           stragegy may produce the same result).

           *Without Replacement*: When multiple trials are generated
           in one call to :func:`.synthesize_trials`, each of the
           results is constrained to be distinct. The number of
           returned experiments will be less than the requested number
           if the pool of possible trial sequences is exhausted.

.. class:: sweetpea.SMGen

           An experimental sampler that is especially effective for
           designs that include derived factors with transition level.
           Currently, windows sizes greater than 1 are not supported,
           many constraints are unsupported, and multiple crossings
           are unsupported.

           *Non-Uniformity*: Generates trials through a search that
           may not produce uniform coverage.

           *Replacement*: Generating multiple trials in one call to
           :func:`.synthesize_trials` produces independent results. That
           is, the single call is the same as separate calls that each
           generate one sequence of trials.
