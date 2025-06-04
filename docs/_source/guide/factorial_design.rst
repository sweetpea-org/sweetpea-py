.. _guide_factorial_design:

Factorial Experiment Design
===========================

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
-------

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
------

In a factorial experimental design, each factor can take on one of a finite
number of discrete possible values, called :term:`levels <level>`. To make this
more concrete, consider a simple example.


.. _guide_factorial_example:

Example
-------

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
-----------

A :term:`derivation` (or :term:`derived level`) is a new level produced by
combining other :term:`levels <level>`. This combination of levels can be
directly constructed with :func:`sweetpea.DerivedLevel`.

Derivations can also be constrained by :term:`derivation windows <derivation
window>`, which allow for specifying specific manners in which different levels
from multiple factors can interact across trial boundaries:

- :ref:`Within-trial windows
  <guide_factorial_derivations_within-trial_windows>`
  look only within a single given trial.
- :ref:`Transition windows <guide_factorial_derivations_transition_windows>`,
  look at a trial and the previous one, so it can describe transitions between
  two consecutive trials.
- :ref:`General windows <guide_factorial_derivations_basic_windows>` are defined
  in terms of a trial and any number of preceding trials.
- :ref:`ContinuousFactor windows <guide_factorial_derivations_continuousfactor_windows>` 
  offer similar functionality to general derivation windows, 
  but operate on values of :class:`.ContinuousFactor` across a trial 
  and any number of preceding trials, rather than on discrete levels.

These are explained more below.


.. _guide_factorial_derivations_within-trial_windows:

Within-Trial Windows
^^^^^^^^^^^^^^^^^^^^

The :term:`within-trial windows <derivation window, within-trial>`
(:class:`sweetpea.WithinTrial`) describe a level that
is selected depending on levels from other factors, all within the same trial.
For example, when one factor is a color and another factor is the text of a color name,
each trial can be categozied as “congurent” or “incongrent” individually.

.. _guide_factorial_derivations_transition_windows:

Transition Windows
^^^^^^^^^^^^^^^^^^

A :term:`transition window <derivation window, transition>`
(:class:`sweetpea.Transition`) describes a level that
is selected depending on a combination of levels from other factors in the
current trial and the immediately preceding trial. For example, a trial
might be categorized as “same” if it is categorized as “congurent”
and the previous trial was also categorized as “congurent”.


.. _guide_factorial_derivations_basic_windows:

General Windows
^^^^^^^^^^^^^^^

A general :term:`derivation window`
(:class:`sweetpea.Window`) creates a level that is selected
depending on a combination of levels from other factors in the current trial and
zero or more preceding trials.


.. _guide_factorial_derivations_continuousfactor_windows:

ContinuousFactor Windows
^^^^^^^^^^^^^^^^^^^^^^^^

A :term:`continuousfactor window <derivation window, continuousfactor>`
(:class:`sweetpea.ContinuousFactorWindow`) is special kind of general window 
that operates on :class:`.ContinuousFactor` instead of discrete levels. 
It allows access to values of one or more :class:`.ContinuousFactor` 
across a number of previous trials defined by window `width`. 
This is useful for defining new continuousfactors that depend on recent trends, 
changes, or history — for example, computing the difference between the current 
and previous trial values of reward.


.. _guide_factorial_glossary:

Glossary
--------

.. glossary::

    constraint
      An element of an :term:`experiment design` that affects the generation of
      :term:`trials <trial>` for the experiment. For example, a constraint
      may exclude a particular combination of levels, it may prevent a certain
      number of levels from appearing in consecutive sequences, or it may
      increase the number of :term:`trials <trial>` in an experiment
      by establishing a minimum trial count.

    crossing
      Short for :term:`experiment crossing`.

    derivation
      An artificial :term:`level` that results from the combination of other
      levels. Also called a :term:`derived level`.

    derivation window
      A window constraining a :term:`derivation` that depends on a combination
      of :term:`levels <level>` from other :term:`factors <factor>` in the
      current trial and zero or more preceding trials.

    derivation window, transition
      A :term:`derivation window` that depends on a combination of :term:`levels
      <level>` from other :term:`factors <factor>` in the current trial and the
      immediately preceding trial.

    derivation window, within-trial
      A :term:`derivation window` that depends on :term:`levels <level>` from
      other :term:`factors <factor>`, all within the same trial.

    derivation window, continuousfactor
      A :term:`continuousfactor window` that operates over continuous-valued
      :term:`continuousfactors <continuousfactor>` rather than discrete levels. 
      It provides runtime access to a
      sliding window of numeric values across multiple trials.

    derived level
      See :term:`derivation`.

    design
      Short for :term:`experiment design`.

    experiment
      Usually, a particular instantiation of a sequence of :term:`trials <trial>`
      for an experiment design. When clear from context, “experiment” may be used
      instead as a shorthand for :term:`experiment design`.

    experiment crossing
      A subset of the :term:`factors <factor>` that define an
      experiment. Except as modified by exclusions and minimum-trials
      :term:`constraints <constraint>`, a sequence of :term:`trials <trial>` for an
      experiment combines every possible :term:`level` of each :term:`factor`
      in the crossing with every :term:`level` of every other :term:`factor`
      in the crossing. For a :term:`factor` that is not in the crossing,
      a :term:`level` is assigned independently or based on explicit
      :term:`constraints <constraint>` or :term:`derived levels <derived level>`.

    experiment design
      The set of factors and coonstraints that define an experiment
      and that determine the :term:`trials <trial>` of the experiment.

    factor
      An independent variable in a factorial experiment, composed of finitely
      many :term:`levels <level>`.

    continuousfactor
      A factor whose values are sampled from a distribution function at runtime, 
      rather than chosen from a predefined list of discrete levels. 

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

    transition window
      See :term:`derivation window, transition`.

    trial
      An individual event in an experiment that is defined by a
      combination of levels. The numebr of trials contained in an
      experiment is determined in part by the number of :term:`factors
      <factor>` and :term:`levels <level>` in the experiment design
      and the way that they are crossed.

    window
      See :term:`derivation window`.

    within-trial derivation
      See :term:`derivation window, within-trial`.

    continuousfactor window
      See :term:`derivation window, continuousfactor`.
