.. _sampling_strategies:

Sampling Strategies
===================

.. class:: sweetpea.Gen

           Abstract class for a sampling strategy (i.e., a generator
           of trials).

           A subclass of :class:`Gen` can be used instead of an
           instance to mean the same sampling strategy as an instance
           with default arguments.

           *Uniforimity*: Different subclasses of `Gen` provide
           different guarantee about coverage of the space of possible
           trial sequences. A guarantee of uniformity means that is a
           single trial sequence is requested via
           :func:`synthesize_trials`, the generated sequence is chosen
           randomly among all trial sequences that fit the constraints
           of the experiment definition, and all such trial sequences
           are eqaully likely to be reported.

           *Independence*: Different subclasses of `Gen` provide
           different behavior when multiple trial sequences are
           requested with a single call to :func:`synthesize_trials`.
           Some strategies produce independenly chosen results, while
           some produce distinct results in the returned list of
           sequences.
           
.. class:: sweetpea.UniGen

           *Uniforimity*: Generates trials with a guarantee of
           uniformity. Unfortunately, due to the difficulty of
           sampling with a guarantee, this stategy is unlikely to
           succeed for non-trial designs.

           *Independence*: Generating multiple trials in one call to
           :func:`synthesize_trials` with this strategy produces
           indepedent results. That is, the single call is the same as
           separate calls that each generate one sequence of trials.

.. class:: sweetpea.CMSGen

           *Quasi-Uniforimity*: Generates trials that appear to be
           uniformly chosen based on the available technology for
           detecting non-uniformity. This strategy may perform well in
           terms of sampling possible configurations, despite a having
           no formal guarantee of uniformity.

           *Independence*: Generating multiple trials in one call to
           :func:`synthesize_trials` with this strategy produces
           indepedent results. That is, the single call is the same as
           separate calls that each generate one sequence of trials.

           
.. class:: sweetpea.RandomGen(acceptable_error=0)

           *Uniforimity*: Generates trials with a guarantee of
           uniformity. Constraints or derived factors with a window
           greater than 1 can force generation to use rejection
           sampling, which may fail to find instances in a reasonable
           time if the search space is large.

           *Non-Independence*: When multiple trials are generated in
           one call to :func:`synthesize_trials` with this strategy,
           each of the results is constrained to be distinct. The
           number of returned experiments will be less than the
           requested number if the pool of possible trial sequences is
           exhausted.

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
           
.. class:: sweetpea.IterateGen

           *Non-Uniforimity*: Generates trials by repeatedly finding
           solutions to an experiment design's constraints, but with
           no guarantee of uniform coverage or even randomness (i.e.,
           each separate use of :func:`synthesize_trials` with this
           stragegy may produce the same result).

           *Non-Independence*: When multiple trials are generated in
           one call to :func:`synthesize_trials` with this strategy,
           each of the results is constrained to be distinct. The
           number of returned experiments will be less than the
           requested number if the pool of possible trial sequences is
           exhausted.
