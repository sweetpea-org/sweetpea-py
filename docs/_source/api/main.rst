Experiments
===========

Create an experiment description using :func:`.CrossBlock` or
:func:`.MultiCrossBlock`, then generate trials for the experiment
using :func:`.synthesize_trials`. Print generated trials using
:func:`.print_experiments`.

.. class:: sweetpea.Block()

   Abstract class representing an experiment description, which can be
   turned into a sequence of trials with :func:`.synthesize_trials`.
           
.. function:: sweetpea.CrossBlock(design, crossing, constraints, require_complete_crossing=True)

   Creates an experiment description based on a set of factors and a
   subset them that are *crossed*.

   The :func:`.CrossBlock` function is the main way of describing an
   experiment. The result is an object that be used with a function
   like :func:`.synthesize_trials`.

   The `design` argument lists all of the factors in the experiment
   design. When a sequence of trials is generated for the experiment,
   each trial will have one level from each factor in `design`.

   Different trial sequences generated from the experiment will have
   different combinations of levels in different orders. The factors
   in `crossing` supply an initial constraint, which is that every
   combination of levels in the crossing should appear once (within a
   sequence of trials that is determined the crossing size). When
   derived factors are included in a crossing, they effectively impose
   additional contraints, since each derived level is compatble with
   only certain levels of other factors. Finally, the `constraints`
   argument can impose additional constraints on the generated trials.

   The number of trials in each generated trial sequence is also
   determined primarily by the `crossing` argument. Specifically, the
   number of trials starts as the product of the number of levels of
   the factors in `crossing`. This trial count can be adjusted by
   other elements of the design:

   * :func:`.Exclude` constraints in `constraints` can exclude levels
     of a crossed factor. In that case, as long as
     `require_complete_crossing` is set to false, combinations
     involving the factor are removed from the crossing.

   * When the levels of a derived factor in `crossing` have a window
     size N that is greater than 1, then N-1 additional preamble
     trials are added to the start of the sequence, so that the
     derived level is defined for the first trial that starts the
     crossing sequence. When multiple derived factors are included in
     the crossing, the one with the greatest window size determines
     the number of preamble trials. The levels of non-derived factors
     in the preamble trials are selected randomly and independently,
     except that the combinations are subject to any requirements from
     `constraints`, such as an :func:`.AtMostKInARow` constraint or an
     :func:`.Exclude` constraint.

   * When a derived-factor definition implicitly excludes certain
     combinations by the definition of its levels, then the number of
     trials in a crossing can be reduced, but only if
     `require_complete_crossing` is set to false.

   * A :func:`.MinimumTrials` in `constraint` can increase the number
     of trials in a sequence. Additional trials are added afterward by
     replicating the crossing as many times as needed to reach the
     required number of trials. Levels are selected for each
     replication of the crossing independently, except that transition
     derived factors can create dependencies from one replication to
     the next. Preamble trials are not replicated, since each
     replication of the crossing serves as a preamble for the next.
     The last replication can be shorter than the full crossing, in
     which case is reflects a prefix of a full-crossing sequence than
     would otherwise appear.

   :param design: the factors that make up the design
   :type design: List[Factor]
   :param crossing: factors that are fully crossed in the block's trials,
                    which must be a subset of the `design` list
   :type crossing: List[Factor]
   :param constraints: constraints that every sequence of trials must
                       satify; see :ref:`constraints`
   :type constraints: List[Constraint]
   :param require_complete_crossing: dertermines whether every
                                     combination in `crossing` must
                                     appear in a block of trials; a
                                     false value is appropriate if
                                     combinations are excluded through
                                     an :class:`.Exclude` constraint
   :return: a block description
   :rtype: Block

.. function:: sweetpea.MultiCrossBlock(design, crossings, constraints, require_complete_crossing=True)

   Creates an experiment description as a block of trials based on
   multiple crossings.

   The :func:`.MultiCrossBlock` function is like :func:`.CrossBlock`,
   but it accepts multiple crossings in `crossings`, instead of a
   single crossing.

   The number of trials in each generated sequence for the experiment
   is determined by the *maximum* of number that would be determined
   by an individual crossing in `crossings`.

   Every combination of levels in each individual crossing in
   `crossings` appears at least once within that crossing's size.
   Smaller crossing sizes lead to replications of that crossing to
   meet the number of trials required for larger crossings. At the
   same time, different crossings in `crossings` can refer to the same
   factors, which creates constraints on how factor levels are chosen
   across crossings in a given trial.

   :param design: the factors that make up the design
   :type design: List[Factor]
   :param crossings: a list of crossings, where each crossing is a
                     list of factors that are fully crossed in the
                     block's trials; the factors in each crossing must
                     be a subset of the `design` list
   :type crossings: List[List[Factor]]
   :param constraints: constraints that every sequence of trials must
                       satify; see :ref:`constraints`
   :type constraints: List[Constraint]
   :param require_complete_crossing: same as for :func:`.MultiCrossBlock`
   :return: a block description
   :rtype: Block

.. function:: sweetpea.synthesize_trials(block, samples=10, sampling_strategy=IterateGen)

   Given an experiment description, generates multiple blocks of trials.

   Each block has a number of trials that is determined by the
   experiment's crossing, and each trial is a combination of levels
   subject to implciit and explicit constraints in the experiment
   description.

   The `sampling_strategy` argument determines properties of the
   resulting samples, such as whether each sequence reflects a
   uniformly random choice over all valid sequences. See see
   :ref:`sampling_strategies` for more information.

   :param block: the experiment description
   :type block: Block
   :param samples: the number of sequences of trials to generate; for
                   example, 1 sample would correspond to a single run
                   of the experiment with a random ordering of the trials
                   (subject to the experiment's constraints)
   :type samples: int
   :param sampling_strategy: how a random set of trials is generated; the default is currently
                             :class:`.IterateGen`, but this is subject to change
   :type sampling_strategy: Gen
   :return: a list of blocks; each block is a dictionary mapping each
            factor name to a list of levels, where all of the lists in the
            dictionary have one item for each trial
   :rtype: List[Dict[str, List[str]]]
           
.. function:: sweetpea.print_experiments(block, experiments)

   Prints the trials generated by :func:`.synthesize_trials` in a
   human-readable format.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str,list]]

.. function:: sweetpea.tabulate_experiments(block=None, experiments, factors=None, trials=None)

   Tabulates the number of times each crossing combination occurs in
   each sequence of `experiments`, and prints a summary in a
   human-readable format. This function might be used to check that
   :func:`.synthesize_trials` produces an expected distirbution, for
   example.
   
   Factors relevant to a crossing are normally extracted from `block`,
   but they can be specified separately as `factors`. When `block` is
   supplied, it must contain a single crossing, as opposed to a
   multi-crossing block produced by :func:`.MultiCrossBlock`.

   Normally, all trails in each sequence are tabulate. If 'trails` is
   provided, is lists trials that should be tabulated, and other
   trials are ignored. Trial indices in `trials` count from 0.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, List[str]]]
   :param factors: an alernative to `block` supplying factors to use as a crossing
   :type factors: List[Factor]
   :param trials: the indices of trials to tabulate, defaults to all trials
   :type trials: List[int]

.. function:: sweetpea.save_experiments_csv(block, experiments, file_prefix)

   Saves each sequence of `experiments` to a file whoe name is
   `file_prefix` followed by an underscore, a number counting from
   `0`, and “.csv”.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, List[str]]]
   :param file_prefix: file-name prefix
   :type file_prefix: str

.. function:: sweetpea.experiments_to_tuples(block, experiments, file_prefix)

   Converts a result from :func:`.synthesize_trials`, where each
   generated sequence is represented as a dictory of lists, so that
   each generated sequence is instead represented as a list of tuples.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, List[str]]]
   :return: a list of lists of tuples, where each tuple contains the string
            names of levels selected for one trial
   :rtype: List[List[Tuple[str, ...]]]
