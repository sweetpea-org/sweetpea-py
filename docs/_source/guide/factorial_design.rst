.. _guide_factorial_design:

Factorial Experiment Design
---------------------------

SweetPea is a domain-specific programming language for creating factorial
experimental designs. Our goal is to make it easy to specify and set up all of
the factors and levels needed for your experiment.

.. hint::

   There's a :ref:`glossary <guide_factorial_glossary>` at the bottom of this
   page for a brief overview of the most important terms.

`Wikipedia gives <https://en.wikipedia.org/wiki/Factorial_experiment>`_ a
decent introductory definition of a :term:`factorial experiment`:

    In statistics, a full **factorial experiment** is an experiment whose design
    consists of two or more factors, each with discrete possible values or
    "levels", and whose experimental units take on all possible combinations of
    these levels across all such factors. A full **factorial design** may also
    be called a **fully crossed design**. Such an experiment allows the
    investigator to study the effect of each factor on the response variable, as
    well as the effects of interactions between factors on the response
    variable.


.. _guide_factorial_factors:

Factors
^^^^^^^

A :term:`factor` is an independent variable in your experiment. In simple
experiments, there may be only one factor --- in which case SweetPea is
definitely overkill for you! But experiments can be successfully run with
multiple factors without issue, and SweetPea will help you plan this out.

.. admonition:: Fun Fact

   The term *factorial* likely first appeared in the 1935 text *The Design of
   Experiments* by Ronald Fisher. The book is also credited with introducing the
   concept of the *null hypothesis*.


.. _guide_factorial_levels:

Levels
^^^^^^

In a factorial experimental design, each factor can take on one of a finite
number of discrete possible values, called :term:`levels <level>`. To make this
more concrete, consider a simple example.


.. _guide_factorial_example:

Example
^^^^^^^

Imagine we are conducting an experiment to observe the `Stroop effect
<https://en.wikipedia.org/wiki/Stroop_effect>`_. In a simple Stroop experiment,
we show a participant the name of a color, and we render the text of that word
in a color other than that which was named. For this experiment, we identify our
factors and levels:

==========  ========================
Factor      Levels
==========  ========================
Color Name  red, blue, green, yellow
Text Color  red, blue, green, yellow
==========  ========================

If this is a :term:`full factorial experiment` (also said that the experiment is
:term:`fully crossed`), then we must conduct one :term:`trial` for each possible
combination of factors and levels. In other words, we must have :math:`4 \times
4 = 16` distinct trials to fully cross the above example experiment.


.. _guide_factorial_derivations:

Derivations
^^^^^^^^^^^

A :term:`derivation` (or :term:`derived level`) is a new level produced by
combining other :term:`levels <level>`. This combination of levels can be
directly constructed with :func:`sweetpea.primitives.derived_level`.

There are three variants of derivation: :ref:`windows
<guide_factorial_derivations_windows>`, :ref:`transitions
<guide_factorial_derivations_transitions>`, and
:ref:`within-trial specifications <guide_factorial_derivations_within-trials>`,
detailed below.


.. _guide_factorial_derivations_windows:

Windows
"""""""

A :term:`window` (constructed with :func:`sweetpea.primitives.window`) creates a
level that is selected depending on a combination of levels from other factors
in the current trial and multiple preceding trials.


.. _guide_factorial_derivations_transitions:

Transitions
"""""""""""

A :term:`transition` (constructed with :func:`sweetpea.primitives.transition`)
describes a level that is selected depending on a combination of levels from
other factors in the current trial and the immediately preceding trial.


.. _guide_factorial_derivations_within-trials:

Within-Trials
"""""""""""""

The :term:`within-trial derivations <within-trial derivation>` (constructed with
:func:`sweetpea.primitives.within_trial`) describe a level that is selected
depending on levels from other factors, all within the same trial.


.. _guide_factorial_glossary:

Glossary
^^^^^^^^

.. glossary::

    derivation
      An artificial :term:`level` that results from the combination of other
      levels. Also called a :term:`derived level`.

    derived level
      See :term:`derivation`.

    factor
      An independent variable in a factorial experiment, composed of finitely
      many :term:`levels <level>`.

    factorial experiment
      An experimental design measuring multiple independent variables (called
      :term:`factors <factor>`) consisting of finitely many discrete possible
      values (called :term:`levels <level>`). A factorial experiment can either
      be classified as a :term:`full factorial experiment` or a
      :term:`fractional factorial experiment`.

    fractional factorial experiment
      A :term:`factorial experiment` consisting of a specific subset of possible
      :term:`trials <trial>` that together expose meaningful information about
      important features of the problem without the resources or redundancy of a
      :term:`full factorial experiment`. An experiment of this nature is said to
      only be :term:`partially crossed`.

    full factorial experiment
      A :term:`factorial experiment` consisting of enough distinct :term:`trials
      <trial>` to independently observe each possible combination of
      :term:`factors <factor>` and :term:`levels <level>`. An experiment of this
      nature is said to be :term:`fully crossed`. Contrasts with a
      :term:`fractional factorial experiment`.

    fully crossed
      A :term:`factorial experiment` run with enough distinct :term:`trials
      <trial>` to be able to distinguish the effects of each :term:`factor` and
      :term:`level` from one another.

    level
      A discrete possible value that a :term:`factor` can have.

    partially crossed
      See :term:`fractional factorial experiment`.

    transition
      A :term:`derivation` that depends on a combination of :term:`levels
      <level>` from other :term:`factors <factor>` in the current trial and the
      immediately preceding trial.

    trial
      An individual repetition of an experiment. A minimum number of trials must
      be run to obtain sufficient evidence to draw conclusions, and this number
      is determined in part by the number of :term:`factors <factor>` and
      :term:`levels <level>`.

    window
      A :term:`derivation` that depends on a combination of :term:`levels
      <level>` from other :term:`factors <factor>` in the current trial and
      multiple preceding trials.

    within-trial derivation
      A :term:`derivation` that depends on :term:`levels <level>` from other
      :term:`factors <factor>`, all within the same trial.
