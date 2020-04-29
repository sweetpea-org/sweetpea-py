Factors and Levels
==================

.. function:: sweetpea.primitives.factor(name, levels)

              Creates a plain factor for use in an experiment design.

              The name of a factor can be any printable value. The
              levels of a factor can printable values that are used as
              the level names, or the levels can be derived levels
              created by :func:`derived_level` (which must be
              distinct, mutually exclusive, and cover all cases). The
              `levels` list must either contain all derived levels or
              contain all printable values. A *derived factor* is one
              whose levels are derived levels, and that creates an
              implicit constraint on the way the levels appear in an
              experiment; see :func:`.fully_cross_block`.

              If a printable value occurs multiple times in `levels`,
              each instance is a a distinct level. Since the levels
              have the same name, using the level name in contraints
              or derving other factors will effectively refer to all
              of the levels with the same name.

              :param name: the factor's name
              :param levels: the factor's levels
              :type levels: list
              :returns: a factor
              :rtype: Factor

.. function:: sweetpea.primitives.derived_level(name, derivation)

              Creates a derived level, which depends on the levels of
              other factors in a design.

              :para name: the level's name, which can be any printable
                          value
              :param derivation: a condition on other factors' levels; see
                                 :ref:`derivations`.
              :type derivation: Derivation
              :returns: a derived level
