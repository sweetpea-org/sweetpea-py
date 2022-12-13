.. _derivations:

Derivations
===========

A `Derivation` is identifies combinations of factor levels that select
another level that is constructed with :class:`.DerivedLevel`. Derived
levels for one factor must all have compatible derivations, which
means that they must depend on the same factors in the same order, have
the same window width, same window stride, and the same starting
trial. However, :class:`.ElseLevel` is compatible with any derivation,
as long as other levels in the same factor have compatible derivations.

.. class:: sweetpea.Derivation()

   Abstract class representing a derived-level specification.
           
.. class:: sweetpea.WithinTrial(predicate, factors)

              Describes a level that is selected depending on levels
              from other factors, all within the same trial. The level
              is equivalent to one created via :class:`.Window` with a
              width of 1 and a stride of 1.

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

.. class:: sweetpea.Transition(predicate, factors)

              Describes a level that is selected depending on a
              combination of levels from other factors in the current
              trial and the immediately preceding trial. The level
              is equivalent to one created via :class:`.Window` with a
              width of 2 and a stride of 1.

              The same as for :class:`.WithinTrial`, any derived factor
              in `factors` must not have a window stride greater
              than 1.

              :param predicate: a function that takes as many level
                                dictionaries as factors in `factors`; in each
                                dictionary, ``-1`` is mapped
                                to the level value for the previous
                                trial, and ``0`` is mapped to the
                                level value for the current trial; the
                                function should return true if the
                                combination of levels implies the
                                result derivation
              :type predicate: Callable[[Dict[int, Any], ...], bool]
              :param factors: a list of factors whose levels across
                              trials determine whether a level with
                              the returned derivation is selected
              :type factors: List(Factor)
              :rtype: Derivation

.. class:: sweetpea.Window(predicate, factors, width, stride=1, start=None)

              Creates a level that is selected depending on a
              combination of levels from other factors in the current
              trial and multiple preceding trials.

              This class generalizes :class:`.WithinTrial` and
              :class:`.Transition` to select a level depending on
              `width` consecutive trials, and where trials that are
              assigned a level value are separated by `stride`-1
              intervening trials. It also allows an initial `start`
              trial to override the default computation of a starting
              trial.

              The same as for :class:`.WithinTrial`, any derived factor
              in `factors` must not have a window stride greater
              than 1.

              :param predicate: a function that takes as many level
                                dictionaries as factors in `factors`; in each
                                dictionary, ``0`` is mapped to the
                                level value for the latest of
                                `width` trials, and so on coutning backwards
                                to ``1-width``; the
                                function should return true if the
                                combination of levels implies this
                                level
              :type predicate: Callable[[Dict[int, Any], ...], bool]
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
              :param start: the first trail (counting from 0) that
                            the derivation's factor will have a level;
                            a `None` value (the default) means that the
                            first trial is automatically determined as
                            the earliest where all factors in `factors`
                            have a level for the trial and preceding `width-1` trials;
                            if `start` combined with `width`
                            means that factors in `factors` will not
                            have a level for some trials, then `predicate` must handle
                            `None` values for the corresponding dictionaries and keys
              :type start: Optional[int]
              :type factors: List(Factor)
              :rtype: Derivation
