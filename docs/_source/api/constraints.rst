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
              minimum trials. See :class:`.CrossBlock` for more
              information.

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
