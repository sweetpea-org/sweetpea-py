Experiments
===========

Create an experiment description using :class:`.CrossBlock` or
:class:`.MultiCrossBlock`, then generate trials for the experiment
using :func:`.synthesize_trials`. Print generated trials using
:func:`.print_experiments`.

.. class:: sweetpea.Block()

   Abstract class representing an experiment description, which can be
   turned into a sequence of trials with :func:`.synthesize_trials`.
           
.. class:: sweetpea.CrossBlock(design, crossing, constraints, require_complete_crossing=True)

   Creates an experiment description based on a set of factors and a
   subset of them that are *crossed*.

   The :class:`.CrossBlock` class is the main way of describing an
   experiment. The result is an object that be used with
   :func:`.synthesize_trials` to generate trial sequences.

   The `design` argument lists all of the factors in the experiment
   design. This factors in the design can be either :class:`.DiscreteFactor`
   that contains discrete levels or :class:`.ContinuousFactor` 
   that samples at runtime. When a sequence of trials is generated for 
   the experiment, each trial will have one level from each 
   factor in `design`.

   Different trial sequences generated from the experiment will have
   different combinations of levels in different orders. The factors
   in `crossing` supply an initial constraint, which is that every
   combination of levels in the crossing should appear once (within a
   sequence of trials that is determined the crossing size). Since only 
   discrete factors can have finite number of levels, only 
   :class:`.DiscreteFactor` is allowed in the `crossing`. When
   derived factors are included in a crossing, they effectively impose
   additional contraints, since each derived level is compatble with
   only certain levels of other factors. Finally, the `constraints`
   argument can impose additional constraints on the generated trials.

   The number of trials in each generated trial sequence is also
   determined primarily by the `crossing` argument. Specifically, the
   number of trials starts as the product of the number of levels of
   the factors in `crossing`. This trial count can be adjusted by
   other elements of the design:

   * :class:`.Exclude` constraints in `constraints` can exclude levels
     of a crossed factor. In that case, as long as
     `require_complete_crossing` is set to false, combinations
     involving the factor are removed from the crossing.

   * When the levels of a derived factor in `crossing` have a window
     size N that is greater than 1, then N-1 additional preamble
     trials are normally added to the start of the sequence, so that
     the derived level is defined for the first trial that starts the
     crossing sequence. This behavior can be controlled in a derived
     factor by specifying a starting trial. When multiple derived
     factors are included in the crossing, the one with the latest
     starting trial determines the number of preamble trials. The
     levels of non-derived factors in the preamble trials are selected
     randomly and independently, except that the combinations are
     subject to any requirements from `constraints`, such as an
     :class:`.AtMostKInARow` constraint or an :class:`.Exclude`
     constraint.

   * When a derived-factor definition implicitly excludes certain
     combinations by the definition of its levels, then the number of
     trials in a crossing can be reduced, but only if
     `require_complete_crossing` is set to false.

   * A :class:`.MinimumTrials` in `constraint` can increase the number
     of trials in a sequence. Additional trials are added by
     scaling the weight of each crossing combination as many times as
     needed to meet or exceed the required number of trials. (To scale
     by repeating the crossing, instead, use :class:`.Repeat`.)
     Preamble trials are not scaled. If the minimum trial
     count minus preamble length is not a multiple of the crossing size,
     then it's as if the minimum trial count were rounded up, and
     then trials are discarded at the end.

   :param design: the factors that make up the design
   :type design: List[Factor]
   :param crossing: discrete factors that are fully crossed in the block's trials,
                    which must be a subset of the `design` list. ContinuousFactor
                    cannot be included in `crossing`
   :type crossing: List[DiscreteFactor]
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

.. class:: sweetpea.MultiCrossBlock(design, crossings, constraints, require_complete_crossing=True, mode=RepeatMode.EQUAL)

   Creates an experiment description as a block of trials based on
   multiple crossings.

   The :class:`.MultiCrossBlock` class generalizes
   :class:`.CrossBlock`, but it accepts multiple crossings in
   `crossings`, instead of a single crossing. Since
   :class:`.MultiCrossBlock` is more general, a :class:`.CrossBlock`
   instance is also a :class:`.MultiCrossBlock` instance.

   The number of trials in each generated sequence for the experiment
   is determined by the *maximum* of number that would be determined
   by an individual crossing in `crossings`, and every combination 
   of levels in each individual crossing in `crossings` appears at 
   least once within that crossing's size.

   When a crossing's size S is smaller than the number of trials T to
   be generated (as determined by another crossing whose size is
   larger than S), the crossing's combinations are replicated using
   the smallest multiple N such that so that S * N >= T. If S * N >
   T, then only the first T generated combinations will be used.
   There are two possible strategies for replicating a crossing, and
   `mode` selects between them. :attr:`.RepeatMode.WEIGHT` weights
   combinations, so that up to N instances of a combination can
   appear anywhere in the T trials. :attr:`.RepeatMode.REPEAT` ensures that
   each of the S combinations appears once in the first S trials,
   then once again in the next S trials, and so on, up to N times. 
   An example illustrating the difference of these two strategies is shown in  
   :ref:`Crossing Sizes in MultiCrossBlock <working-with-multiple-crossings-example>` section.
    
   At the same time, different crossings in `crossings` can refer to the same
   factors, which creates constraints on how factor levels are chosen
   across crossings in a given trial.



   :param design: the factors that make up the design
   :type design: List[Factor]
   :param crossings: a list of crossings, where each crossing is a
                     list of discrete factors that are fully crossed in the
                     block's trials; the factors in each crossing must
                     be a subset of the `design` list
   :type crossings: List[List[DiscreteFactor]] 
   :param constraints: constraints that every sequence of trials must
                       satify; see :ref:`constraints`
   :type constraints: List[Constraint]
   :param require_complete_crossing: same as for :class:`.CrossBlock`
   :param mode: determines the strategy for :class:`.RepeatMode`, 
                whether to use :attr:`.RepeatMode.WEIGHT` OR :attr:`.RepeatMode.REPEAT`
                to generate additional trials for smaller crossings.
                Mode must be specified when crossing sizes are different.
                The default value is :attr:`RepeatMode.EQUAL`, which suggests
                all crossings have equal crossing sizes. If str is provided instead of 
                a :class:`.RepeatMode`, it will behave identically by mapping the string to 
                the corresponding enum: 'weight' maps to :attr:`.RepeatMode.WEIGHT`, 
                'repeat' maps to :attr:`.RepeatMode.REPEAT` and 'equal' maps to :attr:`.RepeatMode.EQUAL`
   :type mode: Union[str, RepeatMode]
   :return: a block description
   :rtype: Block

.. class:: sweetpea.Repeat(block, constraints)

   Repeats the crossings of a given :class:`.MultiCrossBlock` (or
   :class:`.CrossBlock`) enough times to satisfy a minimum trial count
   specified in `constraints`. Unlike increasing the minimum trial
   count within `block`, levels are selected for each replication of
   the crossing independently, except that transition derived factors
   can create dependencies from one replication to the next.

   Preamble trials are not replicated, since each replication of the
   crossing serves as a preamble for the next. If `block` contains
   multiple crossings, then all crossings must have the same preamble
   length.

   Other constraints apply within each single repetetion or across the
   sequence of repetitions, depending on whether the constraint is
   specified as part `block` or provided in `constraints` for the
   repetition. For example, a :class:`.Pin` constraint within `block`
   applies to one trial of each repetition (where the index is
   relative to each repetition), while a :class:`.Pin` constraint in
   `constraints` applies to one trial for the entire trial sequence.
   When a crossing has preamble trials, constraints in `block` apply
   to a preamble for each repetition, which overlaps with the trials
   of the previous repetition. An :class:`.Exclude` constraint is not
   allowed in `constraints`, since that would imply changing the size
   of each repetition.

   If `constraints` is empty, then the repetition has no effect, and
   generating trials from the repetition will be the same as
   generating them from `block` directly.

   :param block: the block to repeat
   :type block: MultiCrossBlock
   :param constraints: a list that cannot include
                       :class:`.Exclude` constraints
   :type constraints: List[Constraint]
   :return: a block description
   :rtype: Block

.. function:: sweetpea.synthesize_trials(block, samples=10, sampling_strategy=IterateGen)

   Given an experiment description, generates multiple blocks of trials.

   Each block has a number of trials that is determined by the
   experiment's crossing, and each trial is a combination of levels
   subject to implcit and explicit constraints in the experiment
   description.

   The `sampling_strategy` argument determines properties of the
   resulting samples, such as whether each sequence reflects a
   uniformly random choice over all valid sequences. See
   :ref:`sampling_strategies` for more information.

   Note that the default sampling strategy *does not* provide a
   guarantee of uniform sampling. The default is chosen to produce
   a result as quickly as possible for the broadest range of
   designs.

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
   :rtype: List[Dict[str, list]]
           
.. function:: sweetpea.print_experiments(block, experiments)

   Prints the trials generated by :func:`.synthesize_trials` in a
   human-readable format.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, list]]

.. function:: sweetpea.tabulate_experiments(block=None, experiments, factors=None, trials=None)

   Tabulates the number of times each crossing combination occurs in
   each sequence of `experiments`, and prints a summary in a
   human-readable format. This function might be used to check that
   :func:`.synthesize_trials` produces an expected distirbution, for
   example.
   
   Factors relevant to a crossing are normally extracted from `block`,
   but they can be specified separately as `factors`. When `block` is
   supplied, it must contain a single crossing, as opposed to a
   multi-crossing block produced by :class:`.MultiCrossBlock`.

   Normally, all trails in each sequence are tabulate. If 'trails` is
   provided, is lists trials that should be tabulated, and other
   trials are ignored. Trial indices in `trials` count from 0.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, list]]
   :param factors: an alernative to `block` supplying factors to use as a crossing
   :type factors: List[Factor]
   :param trials: the indices of trials to tabulate, defaults to all trials
   :type trials: List[int]

.. function:: sweetpea.save_experiments_csv(block, experiments, file_prefix)

   Saves each sequence of `experiments` to a file whose name is
   `file_prefix` followed by an underscore, a number counting from
   `0`, and “.csv”.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, list]]
   :param file_prefix: file-name prefix
   :type file_prefix: str

.. function:: sweetpea.experiments_to_dicts(block, experiments)

   Converts a result from :func:`.synthesize_trials`, where each
   generated sequence is represented as a dictionary of lists, so that
   each generated sequence is instead represented as a list of dictionaries.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, list]]
   :return: a list of lists of dictionaries, where each dictionary maps each
            factor name to the string name for the levels of the trial
   :rtype: List[List[Dict[str, Any]]]

.. function:: sweetpea.experiments_to_tuples(block, experiments)

   Converts a result from :func:`.synthesize_trials`, where each
   generated sequence is represented as a dictionary of lists, so that
   each generated sequence is instead represented as a list of tuples.

   :param block: the experiment description that was provided to :func:`.synthesize_trials`
   :type block: Block
   :param experiments: sequences generated by :func:`.synthesize_trials`
   :type experiments: List[Dict[str, list]]
   :return: a list of lists of tuples, where each tuple contains the string
            names of levels selected for one trial
   :rtype: List[List[tuple]]


.. class:: sweetpea.RepeatMode

   Represents the strategies for generating additional trials
   when individual crossings in a design differ in size. 
   The :class:`.RepeatMode` is used in :class:`.MultiCrossBlock` 
   to determine how to align the number of
   trials across multiple crossings. When crossings have different crossing sizes,
   additional trials must be added to ensure consistency across the design.

   There are three available modes:

   - :attr:`.EQUAL`: Indicates that all crossings are expected to have equal sizes,
     and no additional trials should be added. This is the default setting.

   - :attr:`.REPEAT`: Repeats the smaller crossings enough times until they reach the
     required trial count to align with the trial count of larger crossings.
     Unlike scaling the weight of smaller crossing combinations,
     levels are selected for each replication of the crossing independently.

   - :attr:`.WEIGHT`: Additional trials are added by scaling the weight of the smaller crossing 
     combination to align with the trial count of larger crossings. 
     Preamble trials are not scaled. 

   :class:`.RepeatMode` is typically not instantiated directly; instead, it is passed
   as a configuration value to :class:`.MultiCrossBlock`
