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
              not derived levels, and derived levels must all use a
              compatible derivation as described in :ref:`derivations`.
              The names of the levels must be
              distinct; create a level with a weight to get the
              effect of multiple levels with he same name.

              Since a factor can use be initialized using a keyword argument 
              `sampling_function` or `sampling_method`, the level of such a 
              factor would not be the finite levels as in other cases. If the 
              factor is not a *derived factor* of other factors or values, the 
              levels would be empty. Otherwise, the factor would be a 
              *derived factor* of other factors or values defined in the levels.

              :param name: the factor's name
              :param levels: the factor's levels
              :type levels: List[Level]
              :param sampling_function: A function to sample a factor (optional)
              :type sampling_function: Callable[..., float]
              :param sampling_method: A pre-defined method to sample a factor (optional)
              :type sampling_method: Literal["uniform", "gaussian", "exponential", "lognormal"]
              :param sampling_range: Parameters for a sampling_method such as range or mean/std (optional)
              :type sampling_range: List[float]

              .. property:: name

                The factor's name.

                :type: str

              .. method:: get_level(name)

                Finds a returns a level of the factor with a given
                name. If the factor has multiple levels with the same
                name, any one of them might be returned. The factor 
                initialized with a sampling function does not support 
                such function since it does not have levels.

                Indexing a factor with `[]` is the same as calling the
                `get_level` method.

                :param name: the level's name
                :returns: a level with the given name
                :rtype: Level

              .. property:: levels

                Returns the factor's levels. The factor initialized with 
                a sampling function would not this property.

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
              produce fewer samples than it would for separate levels.
              Along similar lines, a
              :class:`.DerivedLevel` can have a weight greater than 1
              to affect crossings, but cannot be included in a level
              multiple times, because each derived level's predicate
              must match a different set of inputs.

              For a non-derived level whose factor is not crossed (or,
              more generally, is not in all crossings in a
              :class:`.MultiCrossBlock`), a `weight` value has the same
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

              .. property:: factor

                Returns the level's factor. This property exists only
                for a :class:`.Level` object that is extracted from a
                :class:`.Factor` object.

                :returns: a factor
                :rtype: Factor


.. class:: sweetpea.DerivedLevel(name, derivation, weight=1)

              Creates a derived level, which depends on the levels of
              other factors in a design. All derived levels for one factor
              must use compatible derivations as described in :ref:`derivations`.

              :param name: the level's name, which can be any value
              :param derivation: a condition on other factors' levels; see
                                 :ref:`derivations`
              :type derivation: Derivation
              :param weight: the level's weight
              :type weight: int
              :returns: a derived level
              :rtype: Level

.. class:: sweetpea.ElseLevel(name, weight=1)

              Creates a derived level that acts as an “else” case,
              matching any arguments that other derived levels do not
              match. An “else” derived level can appear only once
              among the levels supplied to :class:`.Factor`, and only in
              combination with other derived levels. It is compatible
              with any derivation described in :ref:`derivations`.

              :param name: the level's name, which can be any value
              :param weight: the level's weight
              :type weight: int
              :returns: a derived level
              :rtype: Level
