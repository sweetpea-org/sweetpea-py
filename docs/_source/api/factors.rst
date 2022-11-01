Factors and Levels
==================

.. class:: sweetpea.Factor(name, levels)

              A factor for use in an experiment design.

              The levels of a factor can be plain :class:`.Level`
              values, any kind of non-:class:`.Level` value (which is
              implicitly coerced to a :class:`.Level` value), or
              :class:`.DerivedLevel` values. In the last case, the
              result is a *derived factor*. The `levels` list must
              either contain all derived levels or all values that are
              not derived levels. The names of the levels must be
              distinct; create a level with a weight to get the
              effect of multiple levels with he same name.

              :param name: the factor's name
              :param levels: the factor's levels
              :type levels: List[Level]

              .. property:: name

                The factor's name.

                :type: str

              .. method:: get_level(name)

                Finds a returns a level of the factor with a given
                name. If the factor has multiple levels with the same
                name, any one of them might be returned.

                Indexing a factor with `[]` is the same as calling the
                `get_level` method.

                :param name: the level's name
                :returns: a level with the given name
                :rtype: Level

              .. method:: levels()

                Returns the factor's levels.

                :returns: a list of levels
                :rtype: List[Level]

.. class:: sweetpea.Level(name, weight=1)

              A level for use in a non-derived factor. A level object
              can be used for only one factor.

              If `weight` is provided as a value greater than 1, it
              affects how the level is used in crossings, causing it
              to be combined `weight` times with each combination of
              other factors' levels in a crossing. That's conceptually
              similar to having multiple levels with the same `name`,
              but as long as the level's factor is part of a block's
              crossing, the `weight` crossing occurrences of the level
              are not considered distinct. Consequently, a sampling
              strategy without replacement (see :class:`.Gen`) will
              produce fewer samples than it would for separate levels
              that use the same name. Along similar lines, a
              :class:`.DerivedLevel` can have a weight greater than 1
              to affect crossings, but cannot be included in a level
              multiple times, because each derived level's predicate
              must match a different set of inputs.

              For a non-derived level whose factor is not crossed (or,
              more generally, is not in all crossings in a
              :func:`.MultiCrossBlock`), a `weight` value has the same
              effect as duplicating the level's name. That is, the
              would-be copies are treated as distinct, which means
              that sampling with replacement is biased toward levels
              with greater weight. For sampling strategies without
              replacement, the weight thus increases the number of
              samples that are considered distinct.

              :param name: the level's name, which can be any value
              :param weight: the level's weight
              :type weight: int
              :rtype: Level

              .. property:: name

                 The level's name, which can be any kind of value.


.. class:: sweetpea.DerivedLevel(name, derivation, weight=1)

              Creates a derived level, which depends on the levels of
              other factors in a design.

              :param name: the level's name, which can be any value
              :param derivation: a condition on other factors' levels; see
                                 :ref:`derivations`
              :type derivation: Derivation
              :param weight: the level's weight
              :type weight: int
              :returns: a derived level
              :rtype: Level

.. function:: sweetpea.ElseLevel(name, weight=1)

              Creates a derived level that acts as an “else” case,
              matching any arguments that other derived levels do not
              match. An “else” derived level can appear only once
              among the levels supplied to :class:`.Factor`, and only in
              combination with other derived levels.

              :param name: the level's name, which can be any value
              :param weight: the level's weight
              :type weight: int
              :returns: a derived level
              :rtype: Level
