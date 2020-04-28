.. _constraints:

Constraints
===========

.. function:: at_most_k_in_a_row(k, levels)

              Constrains an experiment to allow at most `k`
              consecutive trials with the same level among those in
              `levels`.

              :param k: the maximum number of consecutive repetitions
                        to allow
              :type k: int
              :param levels: either a factor or a tuple of a factor
                             and level names within the factor;
                             specifying just a factor is the same as
                             listing all of the factor's levels
              :type levels: Union[Factor, Tuple(Factor, list)]
              :rtype: Constraint

.. function:: no_more_than_k_in_a_row(k, levels)

              The same as :func:`at_most_than_k_in_a_row`.
                                    
.. function:: exactly_k_in_a_row(k, levels)

              Constrains an experiment to allow levels among those
              specified in `levels` only when they appear as part of a
              sequence of exactly `k` consecutive trials with the same
              level.

              :param k: the number of repetitions to require
              :type k: int
              :param levels: either a factor or a tuple of a factor
                             and level names within the factor;
                             specifying just a factor is the same as
                             listing all of the factor's levels
              :type levels: Union[Factor, Tuple(Factor, list)]
              :rtype: Constraint

.. function:: exclude(factor, levels)

              Constrains an experiment to disallow the specified
              levels.

              :param factor: the factor whose levels are named by `levels`
              :type factor: Factor
              :param levels: a list of level names among the levels in `factor`
              :type levels: list
              :rtype: Constraint