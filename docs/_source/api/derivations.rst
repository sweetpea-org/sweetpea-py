.. _derivations:

Derivations
===========

A `Derivation` is identifies combinations of factor levels that select
another level that is constructed with :func:`derived_level`.

.. class:: sweetpea.Derivation()

   Abstract class representing a derived-level specification.
           
.. function:: sweetpea.WithinTrial(predicate, factors)

              Describes a level that is selected depending on levels
              from other factors, all within the same trial.

              :param predicate: a function that takes as many level
                                names as factors in `factors`; the
                                function should returns true if the
                                combination of levels implies the
                                result derivation
              :type predicate: Callable[[Any, ...], bool]
              :param factors: a list of factors whose levels determine
                              whether level with this derivation is
                              selected
              :type factors: List(Factor)
              :rtype: Derivation

.. function:: sweetpea.Transition(predicate, factors)

              Describes a level that is selected depending on a
              combination of levels from other factors in the current
              trial and the immediately preceding trial.

              :param predicate: a function that takes as many level
                                lists as factors in `factors`; in each
                                list, the first element (at index 0)
                                is the level value for the previous
                                trial, and the second element is the
                                level value for the current trial; the
                                function should returns true if the
                                combination of levels implies the
                                result derivation
              :type predicate: Callable[[list, ...], bool]
              :param factors: a list of factors whose levels across
                              trials determine whether a level with
                              the returned derivation is selected
              :type factors: List(Factor)
              :rtype: Derivation

.. function:: sweetpea.AcrossTrials(predicate, factors, width, stride)

              Creates a level that is selected depending on a
              combination of levels from other factors in the current
              trial and multiple preceding trials.

              This function generalizes :func:`transition` to select a
              level depending on multiple trials, and where the
              preceding trials are separated by `stride`-1 intervening
              trials.

              :param predicate: a function that takes as many level
                                lists as factors in `factors`; in each
                                list, the first element (at index 0)
                                is the level value for the earliest of
                                `width` trials, and so on; the
                                function should returns true if the
                                combination of levels implies this
                                level
              :type predicate: Callable[[list, ...], bool]
              :param factors: a list of factors whose levels across
                              trials determine whether a level with
                              the returned derivation is selected
              :param width: the number of trials of `factors` to
                            consider when selecting the new, derived
                            level
              :type width: int
              :param stride: one more than the number of trials to
                             skip between the trials that are
                             considered when selecting the new,
                             derived level
              :type stride: int
              :type factors: List(Factor)
              :rtype: Derivation
