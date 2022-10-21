Factors and Levels
==================

.. class:: sweetpea.Factor(name, levels)

              A factor for use in an experiment design.

              The levels of a factor can be plain :class:`Level`
              values, any kind of non-:class:`Level` value (which is
              implicitly coerced to a :class:`Level` value), or
              :class:`DerivedLevel` values. In the last case, the
              result is a *derived factor*. The `levels` list must
              either contain all derived levels or all values that are
              note derived levels.

              If a string occurs multiple times in `levels`, each
              instance is a a distinct level. Since the levels have
              the same name, using the level name in contraints or
              derving other factors will effectively refer to all of
              the levels with the same name.

              :param name: the factor's name
              :param levels: the factor's levels
              :type levels: list

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
              affects how the level is used in crossings: combined
              `weight` times with each combination of other factors'
              levels in a crossing. Providing a `weight` is greater
              than 1 is thus conceptually similar to having multiple
              levels with the same `name`, but the would-be copies for
              a weighted level are not distinct. Consequently, a
              sampling strategy without replacement (see :class:`Gen`)
              will produce fewer samples than it would for separate
              levels that use the same name. Along similar lines, a
              :class:`DerivedLevel` can have a weight greater than 1
              to affect crossings, but cannot be included in a level
              multiple times, because each derived level's predicate
              must be distinct.

              A `weight` value has no effect on a level within an
              uncrossed factor. To increase the frequency of a
              non-derived level name relative to other names, use the
              same name for multiple levels within the enclosing
              factor.

              :param name: the level's name, which can be any value
              :param weight: the level's weight
              :type weight: int
              :rtype: Level

              .. property:: name

                 The level's name, which can be any kind of value.


.. function:: sweetpea.DerivedLevel(name, derivation, weight=1)

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
              among the levels supplied to :func:`Factor`, and only in
              combination with other derived levels.

              :param name: the level's name, which can be any value
              :param weight: the level's weight
              :type weight: int
              :returns: a derived level
              :rtype: Level
