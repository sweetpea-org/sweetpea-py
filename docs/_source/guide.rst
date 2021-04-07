.. _guide:

SweetPea Guide and Information
==============================

This page will provide a brief overview of the purpose of SweetPea and provide
information on how to get it, use it, and consult the documentation.

.. contents:: Contents:
    :local:

This is some more text.


.. _guide_installation:

Installation
------------

How to install SweetPea.


.. _guide_factorial_design:

Factorial Design
----------------

(Explain the basics of factorial experimental design.)


.. _guide_factors:

Factors
^^^^^^^

Something something factors.


.. _guide_derivations:

Derivations
^^^^^^^^^^^

A *derivation* identifies a combination of *factor* *levels*.
Together, this combination of levels selects another level that is constructed
with :func:`sweetpea.primitives.derived_level`.

There are three variants of derivation: *windows*, *transitions*, and
*within-trial specifications*.

Windows
"""""""

A *window* (constructed with :func:`sweetpea.primitives.window`) creates a
level that is selected depending on a combination of levels from other factors
in the current trial and multiple preceding trials.

Transitions
"""""""""""

A *transition* (constructed with :func:`sweetpea.primitives.transition`)
describes a level that is selected depending on a combination of levels from
other factors in the current trial and the immediately preceding trial.

Within-Trials
"""""""""""""

The *within-trial specifications* (constructed with
:func:`sweetpea.primitives.within_trial`) describe a level that is selected
depending on levels from other factors, all within the same trial.
