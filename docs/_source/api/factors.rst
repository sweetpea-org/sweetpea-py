Factors and Levels
==================

.. class:: sweetpea.Factor(name, levels)

              A factor for use in an experiment design.

              By default :class:`.Factor` in SweetPea always creates 
              a :class:`.DiscreteFactor` which contains a finite number of levels 
              (Refer to :class:`.ContinuousFactor` for non-discrete factors). 
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

              .. property:: levels

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

.. class:: sweetpea.ContinuousFactor(name, distribution)

              Sweetpea also supports a :class:`.ContinuousFactor` for factors
              without finite levels, which sample continuously at runtime. 
              This is different from :class:`.DiscreteFactor` that requires 
              a finite discrete levels during its initialization. 
              A :class:`.ContinuousFactor` can dynamically generate values
              at runtime based on the input distribution. 
              
              To initialize a :class:`.ContinuousFactor`, a `distribution` is
              required in order to generate values at runtime. The `distribution`
              must be an instance of a :class:`.Distribution`. 
              Several built-in types are available for :class:`.Distribution`.  
              
              ``UniformDistribution(low, high)``: Samples values from a uniform distribution within 
              a given range.
              
              ``GaussianDistribution(mean, sigma)``: Samples values from a normal distribution with 
              a specified mean and standard deviation.
              
              ``ExponentialDistribution(rate)``: Samples values from an exponential distribution with 
              a given rate parameter.
              
              ``LogNormalDistribution(mean, sigma)``: Samples values from a log-normal distribution 
              with a specified mean and standard deviation.
              
              ``CustomDistribution(func, function_inputs=[])``: Allows sampling dynamically from a 
              user-defined distribution.

              If `UniformDistribution`, `GaussianDistribution`, `LogNormalDistribution`,
              or `LogNormalDistribution` is used to initialize the :class:`.ContinuousFactor`,
              the factor will generate values following the corresponding distribution 
              at runtime, thus the factor is always a *non-derived continuousfactor*. 
              If `CustomDistribution` is used to initialize the :class:`.ContinuousFactor`,
              it will use a custom sampling function (`func`) to generate values. In addition to 
              the user-defined `func`, `CustomDistribution` can also take an additional argument,
              `function_inputs`, which is a list of inputs for the user-defined function.
              When `function_inputs` is not provided or empty, `func` should not require additional
              inputs to generate values. When `function_inputs` is provided, 
              it serves as reference values for sampling values at runtime. 
              For example, if `function_inputs` contains a :class:`.DiscreteFactor` or 
              a :class:`.ContinuousFactor` in the design, the ContinuousFactor initialized 
              is considered a *derived continuousfactor*. In such cases,
              the :class:`.ContinuousFactor` needs to use the values/levels for 
              these factors in the experiment in order to generate values. 
              The `function_inputs` can also contain inputs of other datatypes 
              for `func` to generate values.
              
              If `distribution` is not set or recognized, an error will be raised.

              :param name: The name of the continuous factor.
              :type name: str
              :param distribution: A distribution used to generate values dynamically.
              :type distribution: Distribution


.. class:: sweetpea.DiscreteFactor(name, levels)

              In contrast to :class:`.ContinuousFactor` that generate values
              dynamically, a :class:`.DiscreteFactor` takes on a finite set of distinct,
              separate values (or levels) during its initialization. 
              Each level can be represented using the :class:`.Level` class.
              In SweetPea, a :class:`.DiscreteFactor` is initialized 
              using the :class:`.Factor` class. 
              
              