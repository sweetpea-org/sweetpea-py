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

.. class:: sweetpea.Level(name)

              A level for use in a non-derived factor. A level object
              can be used for only one factor.

              .. property:: name

                The level's name, which can be any kind of value.


.. function:: sweetpea.DerivedLevel(name, derivation)

              Creates a derived level, which depends on the levels of
              other factors in a design.

              :param name: the level's name, which can be any value
              :param derivation: a condition on other factors' levels; see
                                 :ref:`derivations`
              :type derivation: Derivation
              :returns: a derived level
              :rtype: Level

.. function:: sweetpea.ElseLevel(name)

              Creates a derived level that acts as an “else” case,
              matching any arguments that other derived levels do not
              match. An “else” derived level can appear only once
              among the levels supplied to :func:`Factor`, and only in
              combination with other derived levels.

              :param name: the level's name, which can be any value
              :returns: a derived level
              :rtype: Level
