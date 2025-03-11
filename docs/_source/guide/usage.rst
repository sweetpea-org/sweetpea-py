.. _guide_usage:

Using SweetPea
==============

So you've decided to design a factorial experiment. That's excellent! Factorial
experimental designs are a great way to build repeatable experiments with
multiple independent variables. Let's design our experiment in words first, and
then build it in SweetPea.

.. tip::

    If you aren't familiar with factorial experimental design, that's okay! Just
    check out :ref:`our short primer <guide_factorial_design>` first.


A Simple Stroop Experiment
--------------------------

For our example, we'll be testing the `Stroop effect
<https://en.wikipedia.org/wiki/Stroop_effect>`_. From the Wikipedia article:

    In psychology, the **Stroop effect** is the delay in reaction time between
    congruent and incongruent stimuli.

One of the most well-known experiments to test the Stroop effect is to show a
participant a series of words for colors that are also displayed in color.
Sometimes, the color of the word is the same as the color in which the word is
written --- this is called *congruence*. Other times, the word and color are
different, which is *incongruence*.

We have two apparent independent variables: the color and the text. We call
independent variables *factors* in the realm of factorial design.

.. _guide_usage_congruency:
.. note::

    There is also a third factor: whether the pairing of the color and text is
    congruent or incongruent. This is a form of *derived factor*, and we'll come
    back to it later.

To test this effect, we can construct a series of *trials* to administer to a
participant, where each trial is a single color+text pairing. For this
experiment, we will use the three colors red, green, and blue, and we will also
use the names of those colors as the text. All together, this gives us 9
possible values for each trial:

.. role:: red

.. role:: green

.. role:: blue

.. list-table:: Stroop Effect Trials
   :widths: auto
   :align: center
   :header-rows: 1
   :stub-columns: 1

   * -
     - Red (Text)
     - Green (Text)
     - Blue (Text)
   * - Red (Color)
     - :red:`red`
     - :red:`green`
     - :red:`blue`
   * - Green (Color)
     - :green:`red`
     - :green:`green`
     - :green:`blue`
   * - Blue (Color)
     - :blue:`red`
     - :blue:`green`
     - :blue:`blue`

In the parlance of factorial design, these three colors constitute *levels* in
each of the factors. That is to say that the ``color`` factor has three levels,
and the ``text`` factor has three levels.

A trial will consist of showing one of the ``color`` and ``text`` pairs to a
participant and asking them to identify the color in which the text is written.
We will synthesize some *trial sequences* for our experiment now.


Building the Simple Stroop Experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build this simple Stroop experiment, we import and use the following SweetPea
language forms:

* :class:`.Factor` --- constructs factors and their levels
* :class:`.CrossBlock` --- combines the factors to produce trials
* :func:`.synthesize_trials` --- synthesizes trial sequences

To put it together, we do:

.. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials
    >>> text = Factor("text", ["red", "blue", "green"])
    >>> color = Factor("color", ["red", "blue", "green"])
    >>> block = CrossBlock([color, text], [color, text], [])
    >>> experiments = synthesize_trials(block, 1)

The result of this synthesis is based on pseudo-random number generation, and so
the output will not be the same every time. However, when we ran the code to
write this tutorial, we saw the following output (your output should look
similar, though probably not identical):

.. doctest::
    :options: +SKIP

    >>> from sweetpea import print_experiments
    >>> print_experiments(block, experiments)
    1 trial sequences found.
    Experiment 0:
    color green | text blue
    color blue  | text green
    color green | text red
    color green | text green
    color red   | text green
    color red   | text blue
    color blue  | text blue
    color red   | text red
    color blue  | text red

.. tip::

    The :func:`.print_experiments` function is useful for printing the results
    of synthesis.

We generated a *fully-crossed experiment*: all possible color-text pairs were
generated, though their order was randomized. We can see this by sorting a
simplified representation of the experiment:

.. doctest::

    >>> from sweetpea import experiments_to_tuples
    >>> # We immediately access the first element of the returned list.
    >>> # This is because we only generated one trial run.
    >>> simple = experiments_to_tuples(block, experiments)[0]
    >>> for pair in sorted(simple):
    ...     print(pair)
    ...
    ...
    ('blue', 'blue')
    ('blue', 'green')
    ('blue', 'red')
    ('green', 'blue')
    ('green', 'green')
    ('green', 'red')
    ('red', 'blue')
    ('red', 'green')
    ('red', 'red')

Because the ``color`` factor has :math:`3` levels and the ``text`` factor has
:math:`3` levels, when we fully cross the factors we get :math:`3 \times 3 = 9`
resulting trials.


SweetPea Feature Recap
^^^^^^^^^^^^^^^^^^^^^^

In building our simple Stroop experiment, we used a few of the most important
SweetPea forms. Let's review them now.


Simple Factors and Levels
"""""""""""""""""""""""""

*Simple factors* are factors that are composed only of simple levels. *Simple
levels* are levels that are essentially just names and nothing more; they are
not dependent on any other factors or levels.

While it is possible to import the :class:`.Level` class, it is
usually not necessary (unless you want to assign weights to levels).
Simple levels can only be put into simple factors, which in turn can
only consist of simple levels, and we can create simple levels
implicitly during :class:`.Factor` initialization.

When you construct a :class:`.Factor`, you also pass a list of levels to it. If
those levels are not instances of the :class:`.Level` class, SweetPea will
automatically convert them into instances of :class:`.Level`.

To put all this information together: you can create a simple factor composed of
simple levels by just using the :class:`.Factor` initializer:

.. doctest::

    >>> from sweetpea import Factor
    >>> factor = Factor("factor_name", ("one", 2, 3.0, True))
    >>> len(factor.levels)
    4
    >>> factor["one"].name
    'one'
    >>> factor["one"].factor is factor
    True

.. warning::

    Although you can index into a factor by a level's name to access the level,
    the indexing function expects its argument to be a string! This means that
    you cannot retrieve the second level of the above factor by the value we
    used to create it:

    .. doctest::

        >>> factor[2].name
        Traceback (most recent call last):
          ...
        KeyError: 'Factor factor_name has no level named 2.'

    Instead, you must use the string representation generated by the value's
    ``__str__`` method, which can be called using the :func:`str` function:

    .. doctest::

        >>> factor[str(2)].name
        '2'

We will discuss complex factors (also known as *derived factors*) a bit later.


Block Creation
""""""""""""""

After you get your factors and levels together, you can create an experimental
design :class:`.Block` using one of the appropriate functions. We showed how it
looks to use :func:`.fully_cross_block` in our simple example above. The
function takes a number of arguments, but in the simplest case you need only do:

.. doctest::

    >>> from sweetpea import Factor, fully_cross_block
    >>> f1 = Factor("f1", (1, 2, 3))
    >>> f2 = Factor("f2", ("a", "b", "c"))
    >>> block = fully_cross_block([f1, f2], [f1, f2], [])

That is to say that when you're only dealing with a simple experiment (an
experiment comprised only of simple factors), you can probably just use a list
of your factors as both the ``design`` and your ``crossing``, and then hold the
``constraints`` empty with an empty list.


Trial Synthesis
"""""""""""""""

Once you have a complete experimental design in the form of a :class:`.Block`,
you're ready to use it to synthesize trials. In the above example, we used the
:func:`.synthesize_trials` with the default parameter `sampling_strategy` as 
:class:`.IterateGen`, which conducts non-uniform SAT-sampling to synthesize 
the trials.


Working With Derived Levels
---------------------------

We've covered simple factors and levels, so now we move on to the more complex
capabilities of SweetPea: derivations and constraints.


Derivation
^^^^^^^^^^

*Derivation* is the process of creating new levels that depend in some way upon
information contained in other levels from other factors --- and sometimes other
trials. In other words, *derivation* is what produces :class:`DerivedLevels
<.DerivedLevel>`.

Derivation is perhaps best explained through example. We resume the Stroop
example from above, and return to the issue of :ref:`congruency
<guide_usage_congruency>`. Recall that we had produced two simple factors of
three levels each. Now we would like to create a factor for ``congruency`` that
has two levels: ``congruent`` and ``incongruent``. A trial's ``congruency`` is
determined by the same trial's ``color`` and ``text``: if they align, then the
``congruency`` is ``congruent``. Otherwise, the trial is ``incongruent``.

Let's create the ``congruency`` factor now. We start by recreating the ``color``
and ``text`` simple factors from before:

.. doctest::

    >>> from sweetpea import Factor
    >>> text = Factor("text", ["red", "blue", "green"])
    >>> color = Factor("color", ["red", "blue", "green"])

Next, we need to define the predicate functions that will be used to determine
whether a color-text pair is congruent.

.. doctest::

    >>> def congruent(color: str, word: str) -> bool:
    ...     return color == word
    ...
    >>> def incongruent(color: str, word: str) -> bool:
    ...     return not congruent(color, word)
    ...

Now, we can construct the derived levels. While simple levels can be constructed
directly by the :class:`.Factor` during initialization, :class:`.DerivedLevel`
instances must be manually instantiated. :class:`DerivedLevels <.DerivedLevel>`
also require a *derivation window* as an argument. We will discuss this more
in-depth in a little bit, so for now just trust us that we want to use the
:class:`.WithinTrial` for this particular job:

.. doctest::

    >>> from sweetpea import DerivedLevel, WithinTrial
    >>> con_level = DerivedLevel("congruent", WithinTrial(congruent, [color, text]))
    >>> inc_level = DerivedLevel("incongruent", WithinTrial(incongruent, [color, text]))

Finally, we can construct the ``congruency`` factor:

.. doctest::

    >>> congruency = Factor("congruency", [con_level, inc_level])

Now when we create a full crossing using :class:`.CrossBlock`, we will
include the ``congruency`` factor with the rest of the design. However, it is
*not* part of the crossing itself. The result of synthesizing trials from such a
crossing will be a random arrangement of the following trials:

.. list-table:: Stroop Effect Trials With Congruency
   :widths: auto
   :align: center
   :header-rows: 1
   :stub-columns: 0

   * - Color
     - Text
     - Congruency
   * - red
     - red
     - congruent
   * - red
     - green
     - incongruent
   * - red
     - blue
     - incongruent
   * - green
     - red
     - incongruent
   * - green
     - green
     - congruent
   * - green
     - blue
     - incongruent
   * - blue
     - red
     - incongruent
   * - blue
     - green
     - incongruent
   * - blue
     - blue
     - congruent

We can verify this by using the :func:`.experiments_to_tuples` function on the
result of synthesizing one trial run from this design:

.. doctest::

    >>> from sweetpea import CrossBlock, synthesize_trials, experiments_to_tuples
    >>> design = [color, text, congruency]
    >>> crossing = [color, text]
    >>> block = CrossBlock(design, crossing, [])
    >>> experiments = synthesize_trials(block, 1)
    >>> for pair in sorted(experiments_to_tuples(block, experiments)[0]):
    ...     print(pair)
    ...
    ...
    ('blue', 'blue', 'congruent')
    ('blue', 'green', 'incongruent')
    ('blue', 'red', 'incongruent')
    ('green', 'blue', 'incongruent')
    ('green', 'green', 'congruent')
    ('green', 'red', 'incongruent')
    ('red', 'blue', 'incongruent')
    ('red', 'green', 'incongruent')
    ('red', 'red', 'congruent')


Constraints
^^^^^^^^^^^

Sometimes when designing an experiment, you'd like to impose some constraints on
the mechanisms that generate trial sequences. SweetPea has you covered.

Let's say we look at the above list of trials and decide "Hmm, maybe we should
ensure we don't get too many ``incongruent`` trials in a row." After all, there
are six ``incongruent`` trials to just three ``congruent`` ones!

Arbitrarily, we will choose to limit trial sequences such that only two
``incongruent`` trials may appear in a row. This will be accomplished using the
:func:`~sweetpea.AtMostKInARow` function.

.. doctest::

    >>> # We resume from the previous session.
    >>> from sweetpea import AtMostKInARow
    >>> congruency_constraint = AtMostKInARow(2, congruency)
    >>> block = CrossBlock(design, crossing, [congruency_constraint])
    >>> experiments = synthesize_trials(block, 3)
    Sampling 3 trial sequences
    >>> print_experiments(block, experiments)  # doctest: +SKIP
    3 trial sequences found.
    Experiment 0:
    color red   | text green | congruency incongruent
    color green | text blue  | congruency incongruent
    color red   | text red   | congruency congruent
    color blue  | text green | congruency incongruent
    color red   | text blue  | congruency incongruent
    color green | text green | congruency congruent
    color green | text red   | congruency incongruent
    color blue  | text red   | congruency incongruent
    color blue  | text blue  | congruency congruent
    <BLANKLINE>
    Experiment 1:
    color red   | text green | congruency incongruent
    color blue  | text red   | congruency incongruent
    color red   | text red   | congruency congruent
    color blue  | text green | congruency incongruent
    color red   | text blue  | congruency incongruent
    color green | text green | congruency congruent
    color green | text red   | congruency incongruent
    color blue  | text blue  | congruency congruent
    color green | text blue  | congruency incongruent
    <BLANKLINE>
    Experiment 2:
    color red   | text green | congruency incongruent
    color blue  | text red   | congruency incongruent
    color red   | text red   | congruency congruent
    color blue  | text green | congruency incongruent
    color red   | text blue  | congruency incongruent
    color blue  | text blue  | congruency congruent
    color green | text red   | congruency incongruent
    color green | text blue  | congruency incongruent
    color green | text green | congruency congruent

We can see from these outputs that we never get more than two trials in a row
with the same ``congruency`` level selected. However, note that the constraint
is *not* imposed across experiment boundaries: the final trial of the second
experiment is ``incongruent``, and the first two trials of the third experiment
are also ``incongruent``. This adds up to three consecutive trials! But this
behavior is expected. The :class:`~sweetpea.AtMostKInARow`
constraint only looks *within* a given experiment, not across experiments.


ContinuousFactor in SweetPea
----------------------------

In addition to factors with discrete levels, SweetPea also supports a 
:class:`.ContinuousFactor`, which can be initialized using a `sampling_function`. 
Unlike discrete factors, :class:`ContinuousFactor` allows 
sampling values dynamically at runtime using the sampling function.

Defining ContinuousFactor
^^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`.ContinuousFactor` uses a sampling function as the input. Since it uses the sampling 
function to sample values during runtime, it does not have the finite number of levels as 
other factors. As a result, such factors can only be added to the design of the block
instead of the crossing. The crossing needs to consist of factor(s) with finite levels. 

To use :class:`.ContinuousFactor`, we import and use the following SweetPea language forms:

* :class:`.ContinuousFactor` --- constructs continuous factors with sampling function

To put it together, we do:

.. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials,\
    >>> print_experiments, ContinuousFactor, CustomSampling
    >>> import random
    >>> def sample_continuous():
    >>>   return random.uniform(0.5, 1.5)
    >>> response_time = ContinuousFactor("response_time", [],\
    >>> sampling_function=CustomSampling(sample_continuous))
    >>> factor_for_crossing = Factor("color", ["red", "blue", "green"])
    >>> block = CrossBlock([factor_for_crossing, response_time], [factor_for_crossing], [])
    >>> experiments = synthesize_trials(block, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(block, experiments) 
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    color blue  | response_time 0.9695361854047209
    color red   | response_time 1.2529270082663353
    color green | response_time 1.4106548040758589

Constraints for Design with ContinuousFactors 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When designing an experiment using :class:`.ContinuousFactor`, you can 
also impose some constraints on the factor. 

Let's say we look at the above list of trials and decide "we should ensure 
that the ``response_time`` should be less than 1." 

In that case, we can add :class:`.ConstinuousConstraint` to achieve that. 

.. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials,\
    >>> print_experiments, ConstinuousConstraint, ContinuousFactor
    >>> import random
    >>> def sample_continuous():
    >>>   return random.uniform(0.5, 1.5)
    >>> response_time = ContinuousFactor("response_time", [],\
    >>> sampling_function=CustomSampling(sample_continuous))
    >>> factor_for_crossing = Factor("color", ["red", "blue", "green"])
    >>> def less_than_one(a):
    >>>   return (a<1)
    >>> cc = ConstinuousConstraint([response_time], less_than_one)
    >>> block = CrossBlock([factor_for_crossing, response_time], [factor_for_crossing], [cc])
    >>> experiments = synthesize_trials(block, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    Trial: 0, Sampling count to meet continuous constraints: 6
    >>> print_experiments(block, experiments) 
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    color blue  | response_time 0.5357413769177958
    color red   | response_time 0.9859899610573284
    color green | response_time 0.5929666932777036