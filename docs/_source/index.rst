.. _introduction:

SweetPea
========

SweetPea is a `domain-specific programming language
<https://en.wikipedia.org/wiki/Domain-specific_language>`_ built for the
declarative specification of randomized experimental designs and the synthesis
of trial sequences generated from those design specifications.

An `experimental design <https://en.wikipedia.org/wiki/Factorial_experiment>`_
is a description of experimental factors, relationships between those factors,
constraints on the sequencing of factors, and how to map those factors onto a
sequence of trials. Such a design is constructed by calling the various
functions exposed at the top of the :mod:`sweetpea` module.

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   .. NOTE: We start at _apidoc/sweetpea instead of _apidoc/modules because we
      only provide a single module, so having a higher-level organizational page
      isn't very helpful.
   _apidoc/sweetpea

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
