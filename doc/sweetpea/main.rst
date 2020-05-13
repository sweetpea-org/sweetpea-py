Experiments
===========

Create an experiment description using :func:`.fully_cross_block`, then
generate trials for the experiment using :func:`.synthesize_trials` or
:func:`.synthesize_trials_nonuniform`. Print generated trials using
:func:`.print_experiments`.

.. function:: sweetpea.fully_cross_block(design, crossing, constraints, require_complete_crossing=True)

   Creates an experiment description as a block of trials based on a
   single crossing.

   The :func:`fully_cross_block` function is the main way of
   describing an expression. The result is an object that be used with
   a function like :func:`synthesize_trials`.

   The `design` argument lists all of the factors in the design. When
   a sequence of trials is generated, each trial will have one level
   from each factor in `design`.

   The number of trials in each run of the experiment is determined by
   the `crossing` argument. Specifically, the number of trials is the
   product of the number of levels of the factors in `crossing` ---
   unless `require_complete_crossing` is set to false, in which case
   :func:`.exclude` constraints in `constraints` can reduce the number
   of trials.

   Different trial sequences of the experiment will have different
   combinations of levels in different orders. The factors in
   `crossing` supply an implicit constraint, which is that every
   combination of levels in the cross should appear once. Derive
   factors impose additional implement constraints: only combinations
   of levels that are consistent with derivations can appear as a
   trail. Finally, the `constraints` argument can impose additional
   constraints on the generated trials.

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
                                     an :func:`exclude` constraint
   :return: a block description
   :rtype: Block

.. function:: sweetpea.multiple_cross_block(design, crossings, constraints, require_complete_crossing=True)

   Creates an experiment description as a block of trials based on
   multiple crossings.

   The :func:`multiple_cross_block` function is like
   :func:`fully_cross_block`, but it accepts multiple crossings in
   `crossings`, instead of a single crossing.

   The number of trials in each run of the experiment is determined by
   the *maximum* of number that would be determined by an individual
   crossing in `crossings`.

   Every combination of levels in each individual crossing in
   `crossings` appears at least once. Different crossings in
   `crossings` can refer to the same factors, which creates
   constraints on how factor levels are chosen across crossings.

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
   :param require_complete_crossing: same as for :func:`multiple_cross_block`
   :return: a block description
   :rtype: Block

.. function:: sweetpea.synthesize_trials(block, samples=10, sampling_strategy=...)

   Given an experiment description, randomly generates multiple blocks of trials.

   Each block has a number of trials that is determined by the
   experiment's crossing, and each trial is a combination of levels
   subject to implciit and explicit constraints in the experiment
   description.

   **Beware:** Effective uniform sampling is a work in progress, so
   straightforward use of this function might never return a value. To
   get some initial results, try :func:`synthesize_trials_nonuniform`.

   :param block: the experiment description
   :type block: Block
   :param samples: the number of blocks of trials to generate; for
                   example, 1 sample would correspond to a single run
                   of the block with a random ordering of the crossings (that satifies the 
   :type samples: int
   :param sampling_strategy: how a random set of trials is generated; the default is currently
                             :class:`.UnigenSamplingStrategy`, but this is subject to change
   :type sampling_strategy: SamplingStrategy
   :return: a list of blocks; each block is a dictionary mapping each
            factor name to a list of levels, where all the lists in a
            dictionary one level for each trial
   :rtype: List[Dict[any, list]]
           
.. function:: sweetpea.synthesize_trials_nonuniform(block, samples)
                               
   A shorthand for :func:`synthesize_trials` with the sampling
   strategy :class:`.NonUniformSamplingStrategy` if the block has 
   contraints and sampling strategy :class:`.UniformCombinatoricSamplingStrategy`
   if there are no constraints.

   :param block: the experiment description
   :type block: Block
   :param samples: see :func:`synthesize_trials`
   :type samples: int
   :return: see :func:`synthesize_trials`
   :rtype: List[Dict[any, list]]

.. function:: sweetpea.synthesize_trials_uniform(block, samples)
                               
   A shorthand for :func:`synthesize_trials` with the sampling
   strategy :class:`.UnigenSamplingStrategy` if the block has 
   contraints and sampling strategy :class:`.UniformCombinatoricSamplingStrategy`
   if there are no constraints.

   :param block: the experiment description
   :type block: Block
   :param samples: see :func:`synthesize_trials`
   :type samples: int
   :return: see :func:`synthesize_trials`
   :rtype: List[Dict[any, list]]

.. function:: sweetpea.print_experiments(block, trials)

   Prints the trials generated by :func:`synthesize_trials` in a
   human-readable format.

   :param block: the experiment description that was provided to :func:`synthesize_trials`
   :type block: Block
   :param trials: trials generated by :func:`synthesize_trials`
   :type trials: List[Dict[any,list]]
