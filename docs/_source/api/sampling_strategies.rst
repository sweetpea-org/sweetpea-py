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

.. class:: sweetpea.UniformGen

           Automatically selects among strategies that provide uniformity.
           
           *Uniformity*: Generates trials with a guarantee of
           uniformity, a long as only one trial sequence is requested
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

.. class:: sweetpea.UniGen

           *Uniformity*: Generates trials with a guarantee of
           uniformity. Unfortunately, due to the difficulty of
           sampling with a guarantee, this stategy is unlikely to
           succeed for non-trial designs.

           *Replacement*: Generating multiple trials in one call to
           :func:`.synthesize_trials` produces independent results. That
           is, the single call is the same as separate calls that each
           generate one sequence of trials.

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

           
.. class:: sweetpea.RandomGen(acceptable_error=0)

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

.. class:: sweetpea.IterateILPGen

           Like :class:`.IterateSATGen`, but uses Gurobi and requires
           that the ``gurobipy`` package has been installed.

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
