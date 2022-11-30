.. _derivations:

Derivations
===========

A `Derivation` is identifies combinations of factor levels that select
another level that is constructed with :class:`.DerivedLevel`. Derived
levels for one factor must all have compatible derivations, which
means that the must depend on the same factors in the same order, have
the same window width, same window stride, and the same starting
trial. However, :class:`.ElseLevel` is compatible with any derivation,
as long as other levels in the same factor have compatible derivations.

.. class:: sweetpea.Derivation()

   Abstract class representing a derived-level specification.
           
.. function:: sweetpea.WithinTrial(predicate, factors)

              Describes a level that is selected depending on levels
              from other factors, all within the same trial. The level
              is equivalent to one created via :func:`.Window` with a
              window width of 1 and a stride of 1.

              The factors that the level depends on can be non-derived
              or derived, but any derived factor in `factors` must not
              have a window stride greater than 1.

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
              trial and the immediately preceding trial. The level
              is equivalent to one created via :func:`.Window` with a
              window width of 2 and a stride of 1.

              The same as for :func:`.WithinTrial`, any derived factor
              in `factors` must not have a window stride greater
              than 1.

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

.. function:: sweetpea.Window(predicate, factors, width, stride, start)

              Creates a level that is selected depending on a
              combination of levels from other factors in the current
              trial and multiple preceding trials.

              This function generalizes :class:`.WithinTrial` and
              :class:`.Transition` to select a level depending on
              `width` consecutive trials, and where trials that are
              assigned a level value are separated by `stride`-1
              intervening trials. It also allows an initial `start`
              trial to override the default computation of a starting
              trial.

              The same as for :func:`.WithinTrial`, any derived factor
              in `factors` must not have a window stride greater
              than 1.

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
              :type stride: Optional[int]
              :param start: the first trail (counting from 0) that
                            the derivation's factor will have a level;
                            a `None` value (the default) means that the
                            first trial is automatically determined as
                            the earliest where all factors in `factors`
                            have a level for the trial and preceding `width-1` trials;
                            if `start` combined with `width`
                            means that factors in `factors` will not
                            have a level for some trials, then `predicate` must handle
                            `None` values in the corresponding arguments
                            and indices
              :type start: int
              :type factors: List(Factor)
              :rtype: Derivation
