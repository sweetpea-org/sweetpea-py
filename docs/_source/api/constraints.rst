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

.. class:: sweetpea.LatinSquare(outer_factors, num_diagonals=None)

              Constrains a :class:`.NestedBlock` experiment to use Latin
              Square counterbalancing across participants.

              A Latin Square partitions the combinations of ``outer_factors``
              into diagonals, where each diagonal is assigned to a different
              participant. For a square grid (all factors have the same number
              of levels), each diagonal contains exactly one level of each
              factor, ensuring balanced coverage.

              The diagonal for each combination is computed as::

                 diagonal = (i1 + i2 + ...) % D

              where ``i1, i2, ...`` are the level indices and ``D`` is
              ``num_diagonals`` (defaulting to the maximum number of levels
              across all factors).

              :class:`.LatinSquare` is used with :class:`.NestedBlock` and the
              ``participants`` parameter of :func:`.synthesize_trials`. 

              For rectangular grids (factors with different numbers of levels),
              balance warnings are printed at construction time.

              :param outer_factors: the factors forming the outer grid of the
                                    Latin Square; these should also be the
                                    external factors in the :class:`.NestedBlock`
              :type outer_factors: List[Factor]
              :param num_diagonals: number of diagonals (and thus distinct
                                    participant assignments) to create; defaults
                                    to ``max`` of all factor level counts
              :type num_diagonals: Optional[int]
              :rtype: Constraint
