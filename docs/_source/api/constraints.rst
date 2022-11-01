.. _constraints:

Constraints
===========

.. class:: sweetpea.Constraint()

   Abstract class representing a constraint.
           

.. function:: sweetpea.Exclude(factor, level)

              Constrains an experiment to disallow the specified
              level.

              :param factor: the factor whose levels are named by `levels`
              :type factor: Factor
              :param level: a level or name of a level among `factor`'s levels
              :type level: Union[Level, Any]
              :rtype: Constraint

.. function:: sweetpea.MinimumTrials(k)

              Constrains an experiment to set the specified number 
              of minimum trials.

              :param k: minimum number of trials
              :type k: int

.. function:: sweetpea.AtMostKInARow(k, factor_and_level)

              Constrains an experiment to allow at most `k`
              consecutive trials with the level identified by
              `factor_and_level`.

              :param k: the maximum number of consecutive repetitions
                        to allow
              :type k: int
              :param factor_and_level: either a tuple containing a factor and one of its levels,
                                       a tuple containing a factor and the name of one of its levels,
                                       or just a factor; the last case is a shorthand for a separate
                                       constraint for each of the factor's levels
              :type factor_and_level: Union[Tuple[Factor, Level], Tuple[Factor, Any], Factor]
              :rtype: Constraint

.. function:: sweetpea.AtLeastKInARow(k, factor_and_level)

              Constrains an experiment so that when the level
              identified by `factor_and_level` appears in a trial, it
              also appears in at least `k`-1 adjacent trials.
              
              :param k: the minimum number of consecutive repetitions
                        to require
              :type k: int
              :param factor_and_level: like :func:`AtMostKInARow`
              :type factor_and_level: Union[Tuple[Factor, Level], Tuple[Factor, Any], Factor]
              :rtype: Constraint

.. function:: sweetpea.ExactlyKInARow(k, factor_and_level)

              Constrains an experiment so that when the level
              identified by `factor_and_level` appears in a trial, it
              also appears in exactly `k`-1 adjacent trials.

              :param k: the number of repetitions to require
              :type k: int
              :param factor_and_level: like :func:`AtMostKInARow`
              :type factor_and_level: Union[Tuple[Factor, Level], Tuple[Factor, Any], Factor]
              :rtype: Constraint

.. function:: sweetpea.ExactlyK(k, factor_and_level)

              Constrains an experiment so that the level identified by
              `factor_and_level` appears in exactly `k` trials.

              :param k: the number of repetitions to require
              :type k: int
              :param factor_and_level: like :func:`AtMostKInARow`
              :type factor_and_level: Union[Tuple[Factor, Level], Tuple[Factor, Any], Factor]
              :rtype: Constraint
