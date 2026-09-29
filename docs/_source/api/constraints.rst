.. _constraints:

Constraints
===========

.. class:: sweetpea.Constraint()

   Abstract class representing a constraint.
           

.. class:: sweetpea.Exclude(level)

              Constrains an experiment to disallow the specified
              level.

              An :class:`.Exclude` constraint can affect the number of
              trials that are included in a sequence. See
              :class:`.CrossBlock` for more information.

              :param level: either a level,
                            a tuple containing a factor and the name of one of its levels,
                            or a tuple containing a factor and one of its levels
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level]]
              :rtype: Constraint

.. class:: sweetpea.Pin(index, level)

              Constrains an experiment to require the specified level
              at the specified trial index. A negative trial index
              refers to a trial releative to the end of a sequence;
              for example, -1 refers to the last trial. If `index` is
              not in range for trials in an experiment, then the
              experiment will have no satisfying trial sequences.

              :param index: a trial index, counting forward from 0 or backward from -1
              :type index: int
              :param level: either a level,
                            a tuple containing a factor and the name of one of its levels,
                            or a tuple containing a factor and one of its levels
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level]]
              :rtype: Constraint

.. class:: sweetpea.MinimumTrials(k)

              Constrains an experiment to set the specified number of
              minimum trials. See :class:`.CrossBlock` and
              :class:`.Repeat` for more information.

              :param k: minimum number of trials
              :type k: int

.. class:: sweetpea.AtMostKInARow(k, level)

              Constrains an experiment to allow at most `k`
              consecutive trials with the level identified by
              `level`.

              :param k: the maximum number of consecutive repetitions
                        to allow
              :type k: int
              :param level: either a level,
                            a tuple containing a factor and the name of one of its levels,
                            a tuple containing a factor and one of its levels,
                            or just a factor; the last case is a shorthand for a separate
                            constraint for each of the factor's levels
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level], Factor]
              :rtype: Constraint

.. class:: sweetpea.AtLeastKInARow(k, level)

              Constrains an experiment so that when the level
              identified by `level` appears in a trial, it
              also appears in at least `k`-1 adjacent trials.
              
              :param k: the minimum number of consecutive repetitions
                        to require
              :type k: int
              :param level: like :class:`.AtMostKInARow`
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level], Factor]
              :rtype: Constraint

.. class:: sweetpea.ExactlyKInARow(k, level)

              Constrains an experiment so that when the level
              identified by `level` appears in a trial, it also
              appears in exactly `k`-1 adjacent trials.

              :param k: the number of repetitions to require
              :type k: int
              :param level: like :class:`.AtMostKInARow`
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level], Factor]
              :rtype: Constraint

.. class:: sweetpea.ExactlyK(k, level)

              Constrains an experiment so that the level identified by
              `level` appears in exactly `k` trials. If this
              constraint is not consistent with requirements for
              crossing, the experiment will have no satisfying trial
              sequences.

              :param k: the number of repetitions to require
              :type k: int
              :param level: like :class:`.AtMostKInARow`
              :type level: Union[Level, Tuple[Factor, Any], Tuple[Factor, Level], Factor]
              :rtype: Constraint

.. function:: sweetpea.Relax(constraint, by)

              Authorizes `constraint` to be weakened by up to `by`,
              when it would otherwise leave the experiment with no
              satisfying trial sequences. Returns a copy of
              `constraint` to use in place of the original; the
              constraint passed in is unchanged.

              A constraint is weakened only when it is passed through
              this function, and any adjustment that is applied is
              reported as the experiment runs and again by
              :func:`.print_experiments`. An experiment may relax one
              constraint.

              :class:`.ExactlyK`, :class:`.AtMostKInARow`,
              :class:`.AtLeastKInARow` and :class:`.LatinSquare` can
              be relaxed; passing any other constraint raises an
              error. An :class:`.ExactlyK` is adjusted while the block
              is sized, where :class:`.CoverAllCombinations` can
              compute the value it must take. The others have no such
              model, so they are adjusted only after the solver
              reports that the design has no solution.

              For a :class:`.LatinSquare`, `by` is how many sequences
              of N trials may be left out of the pattern, counting
              from the end. A sequence left out keeps its trials but
              is no longer required to hold a combination, so that
              combination may not appear at all. See
              :ref:`relaxing-a-constraint`.

              :param constraint: the constraint that may be weakened
              :type constraint: Constraint
              :param by: how far the constraint may move towards the
                         weaker requirement: for `k`, how many steps;
                         for a :class:`.LatinSquare`, how many
                         sequences may be left out
              :type by: int
              :rtype: Constraint

.. class:: sweetpea.Sequential(factor)

              Constrains the experiment so that the levels of `factor`
              must appear in order over a sequence of trials. When the
              last level of `factor` is used for a trial, the next
              trial starts the sequence again with the first level of
              `factor`.

              :param factor: the factor to constrain to seqential use of its
                             levels in an experiment
              :type factor: Factor
              :rtype: Constraint
           
.. class:: sweetpea.LatinSquare(factors)

              Constrains an experiment so that the levels of `factors`
              are combined in a Latin Square pattern. If the factor in
              `factors` with the most levels has N levels, then every
              N trials will include every level of every factor in
              `factors`. Furthermore, each subsequent sequence of N
              trials will have a distinct possible combination of
              levels until all possibilities are exhausted.

              Which combination a given sequence receives is settled
              when the experiment is solved. Consecutive sequences
              take consecutive combinations and all are used before
              any repeats, but where that cycle starts is left to the
              solver, so it does not depend on the order the levels
              were declared in.

              The given `factors` are typically crossed in an
              experiment description, but they are not required to be
              crossed explicitly; a :class:`LatinSquare` constraint
              effectively forces a crossing as long as an experiment
              includes enough trials.

              See :ref:`Latin Square Counterbalancing <latin-square-counterbalancing>`
              for more information.

              :param factors: the factors forming the Latin Square pattern
              :type factors: List[Factor]
              :rtype: Constraint

.. class:: sweetpea.CoverAllCombinations(*factors, optional=[])

              Constrains an experiment so that its trials collectively
              include every realizable combination of the levels of
              `factors` and of `optional` at least once. A factor that
              is left out of a crossing is assigned by the solver
              subject only to whatever other constraints apply, so
              nothing otherwise guarantees that a particular
              combination ever appears; this constraint supplies that
              guarantee.

              Unlike most constraints, :class:`CoverAllCombinations`
              can increase the number of trials: the count needed for
              coverage is computed when the block is constructed, and
              the block grows to fit, rounded up so that every crossing
              still gets complete passes.

              A combination that cannot occur is not required. That
              includes combinations removed by an :class:`.Exclude`
              constraint and combinations that contradict the predicate
              of a :class:`.DerivedLevel`.

              The trial count reconciles the effects of :class:`.Pin`,
              :class:`.ExactlyK`, and :class:`.Sequential` constraints
              on the listed factors. Ordering constraints such as
              :class:`.AtMostKInARow` and :class:`.LatinSquare` are left
              to the solver instead; when one of those conflicts with
              coverage, :func:`.synthesize_trials` finds no sequences
              and reports which constraints were not accounted for.

              Levels of the listed factors must be unweighted, but
              weighted levels elsewhere in the crossing are supported,
              and they change the trial count accordingly.

              The two groups differ in what may be given up, not in
              what is required to begin with. Every listed factor must
              appear in combination with the others. When the solver
              reports that the design has no solution, the factors named
              in `optional` are given up one at a time, the last one
              first: a factor that has been given up needs only each of
              its own levels to appear, in no particular combination,
              and the block is re-sized to the shorter experiment that
              leaves. A factor may not be in both groups.

              Because factors are given up while the design is being
              solved, the trial count is provisional until then. The
              count is printed as the block is built and again whenever
              it changes, naming the factors given up so far.

              See :ref:`Covering All Combinations <covering-all-combinations>`
              for more information.

              :param factors: the factors that must appear in
                              combination with one another
              :type factors: Factor
              :param optional: further factors the constraint governs,
                               which may be given up---last one first---
                               when the design has no solution, leaving
                               each needing only its own levels to
                               appear rather than its combinations
              :type optional: List[Factor]
              :rtype: Constraint

.. class:: sweetpea.ContinuousConstraint(factors, predicate)

              Constrains :class:`.ContinuousFactor` in an experiment so that 
              the samples generated for these factors meet the proposed 
              constraint function. Since such constraints only apply to 
              factors with continuous sampling functions that 
              should not be included in the crossing, the experiment will 
              sample these factors until the constraints are met after 
              the trial sequences have been satified for discrete factors.

              :param factors: the factors to add constraints on
              :type factors: List[ContinuousFactor]
              :param predicate: a constraint function takes `factors`
                                initialized with sampling function.
                                The function should return true if the
                                combination of factors meet the constraints.
              :type predicate: Callable[[Any, ...], bool]
              :rtype: Constraint
