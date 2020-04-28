SweetPea
========

SweetPea is a language for declaratively specifying randomized
experimental designs and synthesizing trial sequences generated from
the design specification. An experimental design is a description of
experimental factors, relationships between factors, sequential
constraints, and how to map those factors onto a sequence of trials.
Such a design is constructed by calling SweetPea functions such as
:func:`.fully_cross_block`, :func:`.factor`, :func:`.derived_level`, and
:func:`.at_most_k_in_a_row`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   sweetpea/main
   sweetpea/factors
   sweetpea/derivations
   sweetpea/constraints
   sweetpea/sampling_strategies

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
