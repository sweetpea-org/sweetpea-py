.. _guide_usage:

Using SweetPea
==============

.. note::

    We are constantly seeking to improve the user interface of the SweetPea
    language. If something seems difficult or unintuitive to you, please let us
    know by :ref:`filing an issue <issues>`!

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

.. note::

    There is also a third factor: whether the pairing of the color and text is
    congruent or incongruent. This is a form of *derived factor*, and we'll come
    back to it later.

To test this effect, we will construct a series of *trials* to administer to a
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
* :func:`.fully_cross_block` --- combines the factors to produce trials
* :func:`.synthesize_trials_non_uniform` --- uses non-uniform sampling to
  synthesize trial sequences

To put it together, we do:

.. doctest::

    >>> from sweetpea import Factor, fully_cross_block, synthesize_trials_non_uniform
    >>> text = Factor("text", ["red", "blue", "green"])
    >>> color = Factor("color", ["red", "blue", "green"])
    >>> block = fully_cross_block([color, text], [color, text], [])
    >>> experiments = synthesize_trials_non_uniform(block, 1)
    Sampling 1 trial sequences using the class <class 'sweetpea.sampling_strategies.uniform_combinatoric.UniformCombinatoricSamplingStrategy'>

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

    >>> from sweetpea import simplify_experiments
    >>> # We immediately access the first element of the returned list.
    >>> # This is because we only generated one trial run.
    >>> simple = simplify_experiments(experiments)[0]
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
