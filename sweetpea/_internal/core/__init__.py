"""This module provides the fundamental functionality needed for SweetPea to
actually *do* anything. Primarily, this involves handling data representation
and making calls to external utilities for solving logic problems via
SAT-solving.


Data Representation
===================

SweetPea works by representing constraints on experimental designs as
`propositional logic formulas
<https://en.wikipedia.org/wiki/Propositional_formula>`_. These formulas are
converted into `conjunctive normal form
<https://en.wikipedia.org/wiki/Conjunctive_normal_form>`_ and are then passed
to an external SAT solver to either be solved or sampled.

Internally to :mod:`.core`, these formulas are represented as :class:`.CNF`
instances. These are comprised of :class:`Clauses <.Clause>`, which are in turn
comprised of :class:`Vars <.Var>`. The :class:`.Var`, :class:`.Clause`, and
:class:`.CNF` classes are very expressive and can easily be used to manipulate
advanced logic problems.


External Utilities
==================

Once the data is in a compatible formulaic representation, it must be shipped
to an external utility to be solved or sampled from. SweetPea Core makes use of
the following utilities:

  * `CryptoMiniSAT <https://github.com/msoos/cryptominisat>`_, an advanced
    incremental SAT solver.
  * `Unigen <https://github.com/meelgroup/unigen>`_, a state-of-the-art,
    almost-uniform sampler that uses CryptoMiniSAT.


Using Core
==========

There are only a few functions exported from :mod:`.core`, as well as a small
number of classes to support using those functions.

Functions
---------

  * :func:`~sweetpea.core.generate.is_satisfiable.cnf_is_satisfiable`
  * :func:`~sweetpea.core.generate.sample_non_uniform.sample_non_uniform`
  * :func:`~sweetpea.core.generate.sample_non_uniform.sample_non_uniform_from_specification`
  * :func:`~sweetpea.core.generate.sample_uniform.sample_uniform`
  * :func:`~sweetpea.core.generate.utility.combine_cnf_with_requests`

Classes
-------

  * :class:`~sweetpea.core.cnf.Var`
  * :class:`~sweetpea.core.cnf.Clause`
  * :class:`~sweetpea.core.cnf.CNF`
  * :class:`~sweetpea.core.generate.utility.AssertionType`
  * :class:`~sweetpea.core.generate.utility.GenerationRequest`
  * :class:`~sweetpea.core.generate.utility.Solution`
"""

from .cnf import Clause, CNF, Var
from .generate import (
    AssertionType, GenerationRequest, Solution,
    cnf_is_satisfiable, sample_non_uniform, sample_non_uniform_from_specification, sample_uniform,
    combine_cnf_with_requests
)
