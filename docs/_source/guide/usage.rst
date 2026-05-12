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


Working With Multiple Crossings
-------------------------------

SweetPea supports multiple crossings for situations where different subsets 
of factors should be crossed independently. This is useful when building more 
complex experimental designs that consist of multiple fully-crossed components.

Defining MultiCrossBlock
^^^^^^^^^^^^^^^^^^^^^^^^

Using :class:`.MultiCrossBlock` creates an experiment description as a 
block of trials based on multiple crossings. This allows you to combine
different subsets of factors into a unified experiment while maintaining
independent full crossings within each subset.

Multiple crossings are useful in complex experimental designs where some
factors are fully crossed only within specific conditions.
By passing a list of crossings to the crossing argument 
in :class:`.MultiCrossBlock`, each inner list defines a separate crossing.

The :class:`.MultiCrossBlock` constructor is a shorthand for
:class:.`.Merge` of separately constructed blocks, each with its own
crossing(s). The :class:`.Merge` constructor is more general, because
it allows each merged block to supply constraints with the block's
original geometry.

.. _working-with-multiple-crossings-example:

Crossing Sizes in MultiCrossBlock
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using multiple crossings, SweetPea ensures that each sub-crossing 
is internally fully crossed. The number of trials required for the block, 
T, is decide by the crossing size of larger crossing. When a crossing's size S 
is smaller than the number of trials T, then the crossing's combinations 
are replicated using the smallest multiple N such that so that S * N >= T. 
If S * N > T, then only the first T generated combinations will be used.
There are two possible strategies for replicating a crossing, and
`mode` selects between them. :attr:`.RepeatMode.WEIGHT` weights
combinations, so that up to N instances of a combination can
appear anywhere in the T trials. :attr:`.RepeatMode.REPEAT` ensures that
each of the S combinations appears once in the first S trials,
then once again in the next S trials, and so on, up to N times.

The difference of these two strategies for replication are shown in
the following example. The first configurations adds weight to ``f2``
so levels that ``"a"``, ``"b"``, and ``"c"`` do not necessarily appear
in the first three trials. The second configuration repeats ``f2`` so
that ``"a"``, ``"b"``, and ``"c"`` all reliably appear within in the
first three trials (and each subsequent group of three).

.. doctest::

    >>> from sweetpea import (Factor, MultiCrossBlock, RepeatMode, synthesize_trials, 
    >>> print_experiments, CMSGen, IterateGen, RandomGen, IterateSATGen)
    >>> f1 = Factor("f1",   ["A", "B", "C", "D"])
    >>> f2 = Factor("f2",   ["a", "b", "c"])
    >>> f3 = Factor("f3", ['1', '2'])
    >>> constraints=[]
    >>> design = [f1, f2, f3]
    >>> crossing = [[f1, f3], [f2]]
    >>> constraints = []
    >>> block = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.WEIGHT)
    >>> experiments = synthesize_trials(block, 1, RandomGen)
    >>> print_experiments(block, experiments)
    Sampling 1 trial sequences using RandomGen.
    Counting possible configurations...
    Generating samples...
    <BLANKLINE>
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    f1 C | f3 2 | f2 c
    f1 D | f3 1 | f2 a
    f1 D | f3 2 | f2 a
    f1 B | f3 2 | f2 b
    f1 A | f3 2 | f2 c
    f1 A | f3 1 | f2 b
    f1 C | f3 1 | f2 a
    f1 B | f3 1 | f2 c
    >>> block = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT)
    >>> experiments = synthesize_trials(block, 1, RandomGen)
    >>> print_experiments(block, experiments)
    Sampling 1 trial sequences using RandomGen.
    Counting possible configurations...
    Generating samples...
    <BLANKLINE>
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    f1 C | f3 1 | f2 b
    f1 C | f3 2 | f2 c
    f1 A | f3 2 | f2 a
    f1 D | f3 2 | f2 a
    f1 B | f3 2 | f2 b
    f1 D | f3 1 | f2 c
    f1 A | f3 1 | f2 a
    f1 B | f3 1 | f2 b


.. _preamble-trials-multiple-crossings-example:

Preamble Trials in MultiCrossBlock
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a :class:`.CrossBlock`, if a derived factor in the crossing has a window size N > 1, 
then N – 1 preamble trials are added to ensure its level is defined on the first trial. 
This can be adjusted using the factor’s starting trial. 
When multiple derived factors are present in the crossing, 
the one with the latest starting trial determines the number of preamble trials. 

When using :class:`.MultiCrossBlock`, if crossings require different 
numbers of preamble trials due to derived factors with varying window sizes, 
the `alignment` parameter controls how crossings are aligned. 
Use :attr:`.AlignmentMode.POST_PREAMBLE` to start all crossings after the unified preamble
trials, or :attr:`.AlignmentMode.PARALLEL_START` to start individual crossing from 
its own required preamble trials. 

The difference of these two strategies are shown in the following example. If 
:attr:`.AlignmentMode.PARALLEL_START` is used in the :class:`.MultiCrossBlock`, 
the crossing ``[color, task_transition]`` would have one preamble trial because of 
derived factor task_transition, whereas the crossing [task] and [word] would have 
no preamble trials since it does not require preamble trials. Thus the first trial
``color green | word red   | task word  | task_transition`` is considered preamble 
trial for the crossing ``[color, task_transition]``, but the first 
trial for the crossing ``[task]`` and the crossing ``[word]``.
If :attr:`.AlignmentMode.POST_PREAMBLE` is used in the :class:`.MultiCrossBlock`,
the first trial ``color red | word blue | task color | task_transition`` would be the 
preamble trial for all crossings:  

.. doctest::

    >>> from sweetpea import (Factor, MultiCrossBlock, RepeatMode, synthesize_trials, 
    >>> print_experiments, CMSGen, IterateGen, RandomGen, IterateSATGen, Repeat, 
    >>> DerivedLevel, Transition, MinimumTrials, Window, AlignmentMode, CrossBlock)
    >>> color   = Factor("color",   ["red", "blue", "green"])
    >>> word   = Factor("word",   ["red", "blue", "green"])
    >>> task = Factor("task", ['color', 'word'])
    >>> def task_repeat(task):
            return task[0] == task[-1]
    >>> def task_switch(task):
            return not task_repeat(task)
    >>> task_transition = Factor("task_transition", [
            DerivedLevel("repeat", Transition(task_repeat, [task])),
            DerivedLevel("switch", Transition(task_switch, [task]))
        ])
    >>> design = [color, word, task, task_transition]
    >>> crossing = [[color, task_transition], [task], [word]]
    >>> constraints = []
    >>> block = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT, alignment=AlignmentMode.PARALLEL_START)
    >>> experiments = synthesize_trials(block, 1, CMSGen)
    >>> print_experiments(block, experiments)
    Sampling 1 trial sequences using CMSGen.
    Encoding experiment constraints...
    Running CMSGen...
    <BLANKLINE>
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    color green | word red   | task word  | task_transition       
    color red   | word blue  | task color | task_transition switch
    color green | word green | task color | task_transition repeat
    color green | word green | task word  | task_transition switch
    color red   | word red   | task word  | task_transition repeat
    color blue  | word blue  | task color | task_transition switch
    color blue  | word blue  | task color | task_transition repeat
    >>> block = MultiCrossBlock(design, crossing, constraints, mode=RepeatMode.REPEAT, alignment=AlignmentMode.POST_PREAMBLE)
    >>> experiments = synthesize_trials(block, 1, CMSGen)
    >>> print_experiments(block, experiments)
    Sampling 1 trial sequences using CMSGen.
    Encoding experiment constraints...
    Running CMSGen...
    <BLANKLINE>
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    color red   | word blue  | task color | task_transition       
    color green | word red   | task color | task_transition repeat
    color blue  | word blue  | task word  | task_transition switch
    color red   | word green | task word  | task_transition repeat
    color red   | word blue  | task color | task_transition switch
    color blue  | word green | task color | task_transition repeat
    color green | word red   | task word  | task_transition switch

ContinuousFactor in SweetPea
----------------------------

In addition to factors with discrete levels, SweetPea also supports a 
:class:`.ContinuousFactor`, which can be initialized using a `distribution`. 
Unlike discrete factors, :class:`ContinuousFactor` allows 
sampling values dynamically at runtime based on the pre-defined distribution.

Defining ContinuousFactor
^^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`.ContinuousFactor` uses an input distribution to sample values at runtime.
It does not have the finite number of levels as other factors. 
As a result, such factors can only be added to the design of the block
instead of the crossing. The crossing needs to consist of factor(s) with finite levels. 

To use :class:`.ContinuousFactor`, we import and use the following SweetPea language forms:

* :class:`.ContinuousFactor` --- constructs continuous factors with a distribution

To put it together, we do:

.. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials,\
    >>> print_experiments, ContinuousFactor, CustomDistribution
    >>> import random
    >>> def sample_continuous():
    >>>   return random.uniform(0.5, 1.5)
    >>> response_time = ContinuousFactor("response_time", [],\
    >>> distribution=CustomDistribution(sample_continuous))
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

.. _window-for-continuous-factor-example:

Windows for ContinuousFactor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just like derivations on discrete levels can look at previous trials using windows,
SweetPea also supports defining derived continuous factors using windows over past values.

To do this, use the :class:`.ContinuousFactorWindow` along with a :class:`.CustomDistribution`
that takes windowed input.

Here’s a minimal example that demonstrates how to define a derived :class:`.ContinuousFactor` using 
a :class:`.ContinuousFactorWindow` over another :class:`.ContinuousFactor`. 
Specifically, it creates a `reward_diff` factor that calculates the difference between 
the current and previous reward values of `reward`:

.. doctest::

    >>> from sweetpea import ContinuousFactor, ContinuousFactorWindow, CustomDistribution, Factor, \
    >>> CrossBlock, synthesize_trials, MinimumTrials, print_experiments
    >>> import random
    >>> def sample_continuous():
    >>>     return random.uniform(0, 1)
    >>> reward = ContinuousFactor("reward", distribution=CustomDistribution(sample_continuous))
    >>> def difference(window):
    >>>     return window[0] - window[-1]
    >>> window = ContinuousFactorWindow([reward], width=2)
    >>> reward_diff = ContinuousFactor("reward_diff", distribution=CustomDistribution(difference, [window]))
    >>> color = Factor("color", ["red", "blue"])
    >>> block = CrossBlock([color, reward, reward_diff], [color], [MinimumTrials(6)])
    >>> experiments = synthesize_trials(block, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(block, experiments)
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    color blue | reward 0.9148493567759514  | reward_diff nan                
    color blue | reward 0.5751320373836653  | reward_diff -0.3397173193922861
    color red  | reward 0.22538414657155603 | reward_diff -0.3497478908121092
    color red  | reward 0.34749367375749685 | reward_diff 0.12210952718594081
    color red  | reward 0.7889544775824884  | reward_diff 0.44146080382499153
    color blue | reward 0.8445088438260279  | reward_diff 0.05555436624353949

Constraints for Design with ContinuousFactors 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When designing an experiment using :class:`.ContinuousFactor`, you can 
also impose some constraints on the factor. 

Let's say we look at the above list of trials and decide "we should ensure 
that the ``response_time`` should be less than 1." 

In that case, we can add :class:`.ContinuousConstraint` to achieve that. 

.. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials,\
    >>> print_experiments, ContinuousConstraint, ContinuousFactor, CustomDistribution
    >>> import random
    >>> def sample_continuous():
    >>>   return random.uniform(0.5, 1.5)
    >>> response_time = ContinuousFactor("response_time", [],\
    >>> distribution=CustomDistribution(sample_continuous))
    >>> factor_for_crossing = Factor("color", ["red", "blue", "green"])
    >>> def less_than_one(a):
    >>>   return (a<1)
    >>> cc = ContinuousConstraint([response_time], less_than_one)
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



Nesting Designs with NestedBlock
--------------------------------

Instead of performing multiple crossings in parallel with
:class:`.MultiCrossBlock` or :class:`.Merge`, some experiments need an
inner crossing nested within each combination of an outer crossing.

The :class:`.Nest` constructor performans that nesting. Note that
:class:`.Nest` is applied to existing blocks that are formed with,
say, :class:`.CrossBlock` or :class:`.MultiCrossBlock`. The combined
blocks can have overlapping sets of factors in their designs, but they
must have distinct factors in their crossings.

.. _nestedblock-example:

Using NestedBlock
^^^^^^^^^^^^^^^^^
A :class:`.Nest` block keeps an `outer block` combination
constant over multiple trials representing an instance of the `inner block`.

Let's start with a 2×2 inner design:

.. doctest::

    >>> from sweetpea import Factor, CrossBlock
    >>> A = Factor("A", ["a1", "a2"])
    >>> B = Factor("B", ["b1", "b2"])
    >>> inner = CrossBlock([A, B], [A, B], [])
    >>> inner.trials_per_sample()
    4

Here we repeat the 2×2 inner block for each level of an outer block
that has a session :class:`.Factor`. During each 4-trial instance of
the inner block, session is constant.

.. doctest::

    >>> from sweetpea import Nest, synthesize_trials, print_experiments
    >>> session = Factor("session", ["s1", "s2"])
    >>> outer = CrossBlock([session], [session], [])
    >>> nb = Nest(outer_block=outer, inner_block=inner, constraints=[])
    >>> nb.trials_per_sample()
    8 # Total trials = #session levels × inner trials = 2 × 4 = 8.
    >>> exps = synthesize_trials(nb, 1) 
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(nb, exps) 
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    session s2 | A a2 | B b2
    session s2 | A a2 | B b1
    session s2 | A a1 | B b1
    session s2 | A a1 | B b2
    session s1 | A a2 | B b1
    session s1 | A a1 | B b2
    session s1 | A a2 | B b2
    session s1 | A a1 | B b1

Note that the outer ``session`` levels are not required to be in
order. To force those levels to be in order, we could use
:class:`.Merge` to add a :class:`.Sequential` constraint.

.. doctest::

    >>> from sweetpea import Merge, Sequential, RepeatMode
    >>> nb2 = Merge([nb], constraints=[Sequential(session)])
    >>> exps = synthesize_trials(nb2, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(nb2, exps)
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    session s1 | A a2 | B b2
    session s1 | A a2 | B b1
    session s1 | A a1 | B b2
    session s1 | A a1 | B b1
    session s2 | A a2 | B b2
    session s2 | A a1 | B b1
    session s2 | A a2 | B b1
    session s2 | A a1 | B b2

Nesting inside nesting
^^^^^^^^^^^^^^^^^^^^^^

You can create a :class:`.Nest` using another :class:`.Nest` 
as the `inner block`. Each outer level repeats the entire 
original `inner block`. 

.. doctest::

    >>> day = Factor("day", ["d1", "d2"])
    >>> outermost = CrossBlock(design=[day], crossing=[day], constraints=[])
    >>> nnb = Nest(outer_block=outermost, inner_block=nb, constraints=[])
    >>> exps = synthesize_trials(nnb, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(nnb, exps)
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    day d2 | session s1 | A a2 | B b2
    day d2 | session s1 | A a1 | B b1
    day d2 | session s1 | A a1 | B b2
    day d2 | session s1 | A a2 | B b1
    day d2 | session s2 | A a1 | B b2
    day d2 | session s2 | A a2 | B b1
    day d2 | session s2 | A a2 | B b2
    day d2 | session s2 | A a1 | B b1
    day d1 | session s1 | A a2 | B b2
    day d1 | session s1 | A a1 | B b2
    day d1 | session s1 | A a2 | B b1
    day d1 | session s1 | A a1 | B b1
    day d1 | session s2 | A a2 | B b2
    day d1 | session s2 | A a2 | B b1
    day d1 | session s2 | A a1 | B b2
    day d1 | session s2 | A a1 | B b1

.. _latin-square-counterbalancing:
    
Latin Square Counterbalancing
-----------------------------

A *Latin Square* is pattern that orders a crossing so that successive
diagonals are first explored, which provides a more varierty for
combinations within a trial subsequence than could be expected
otherwise. A Latin Square can be particularly useful in an experiment
with multiple participants, where each participant sees only a subset
of the possible combinations, but still sees each level that could
contribute to a combination---and all conbinations are generated
across multiple participants. SweetPea supports Latin Square
counterbalancing through the :class:`.LatinSquare` constraint, which
expects a list of factors that are crossed.

A 2x2 Example
^^^^^^^^^^^^^

Suppose we have `Font` (`small` or `big`) and `Color` (`red` or
`green`) to cross, and we don't need every participant to see every
combination. Since these factor each have 2 levels, there are 2
diagonals in a Latin Square for the factors.

.. list-table:: 2x2 Latin Square Diagonals
   :widths: auto
   :align: center
   :header-rows: 1
   :stub-columns: 1

   * -
     - Color red
     - Color green
   * - Font small
     - Diagonal 0
     - Diagonal 1
   * - Font big
     - Diagonal 1
     - Diagonal 0

- **Diagonal 0**: (small, red) and (big, green)
- **Diagonal 1**: (small, green) and (big, red)

If we simply cross the factors, there's no guarantee that both colors
will show up in the first two trails, only that all `Font`-`Color` word
combinations will show up over four trials.
  
  .. doctest::

    >>> from sweetpea import Factor, CrossBlock, synthesize_trials, print_experiments
    >>> font  = Factor("Font",  ["small", "big"])
    >>> color = Factor("Color", ["red", "green"])
    >>> b = CrossBlock(design=[font, color], crossing=[font, color], constraints=[])
    >>> exps = synthesize_trials(b, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(b, exps)
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    Font big   | Color green
    Font small | Color green
    Font big   | Color red  
    Font small | Color red 

We can force both `Font` levels and both `Color` levels to show up in
the first two trials---without picking a specific color or font---by
adding a :class:`.LatinSquare` constraint.

  .. doctest::

    >>> from sweetpea import LatinSquare, Merge
    >>> lsb = Merge(blocks=[b], constraints=[LatinSquare([font, color])])
    >>> exps = synthesize_trials(lsb, 1)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(lsb, exps)
    1 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    Font big   | Color green
    Font small | Color red  
    Font big   | Color red  
    Font small | Color green

After generating this trial sequence, we might use the first two
trials for the first participant, and the second two trials for the
second participant.

Synthesizing Experiments for Participants
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using just the output of ``print_experiments(lsb, exps)``, we have to
figure out for ourselves where to draw the boundary between
participants. If the block for an experiment has a :class:`.LatinSquare`
constraint with a name for the diagonal, then printing breaks up
each generated experiment into sections labelled by participant name.

  .. doctest::

    >>> lsb = Merge(blocks=[b], constraints=[LatinSquare([font, color],
                                                         name="Participant")])
    >>> exps = synthesize_trials(lsb, 2)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(lsb, exps)
    2 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    <BLANKLINE>
    Participant 0:
    Font big   | Color green
    Font small | Color red  
    <BLANKLINE>
    Participant 1:
    Font big   | Color red  
    Font small | Color green
    <BLANKLINE>
    Experiment 1:
    <BLANKLINE>
    Participant 0:
    Font big   | Color green
    Font small | Color red  
    <BLANKLINE>
    Participant 1:
    Font small | Color green
    Font big   | Color red  

    
Latin Squares as Crossing
^^^^^^^^^^^^^^^^^^^^^^^^^

In the example with `Font` and `Color`, we crossed the factors to take
sure that each generated experiment covers all combinations. The
:class:`LatinSquare` constraint does not require the factors that is
is given to be crossed already. The constraint that it imposes is
stronger than crossing in terms of trial sequences, but weaker than
crossing because :class:`LatinSquare` does not imply a number of
trials. It can be imposed after the fact to a design that supplies
enough trials.

  .. doctest::

    >>> from sweetpea import (Factor, CrossBlock, MinimumTrials,
                              Nest, LatinSquare,
                              synthesize_trials, print_experiments)
    >>> font  = Factor("Font",  ["small", "big"])
    >>> color = Factor("Color", ["red", "green"])
    >>> task  = Factor("Task",  ["read", "paint"])
    >>> b = CrossBlock(design=[font, color],
                       crossing=[],
                       constraints=[MinimumTrials(2)])
    >>> nb = Nest(outer_block=CrossBlock([task], [task], []),
                  inner_block=b,
                  constraints=[LatinSquare([font, color],
                                           name="Participant")])
    >>> exps = synthesize_trials(nb, 2)
    Sampling 1 trial sequences using NonUniformGen.
    Encoding experiment constraints...
    Running CryptoMiniSat...
    >>> print_experiments(nb, exps)
    2 trial sequences found.
    <BLANKLINE>
    Experiment 0:
    <BLANKLINE>
    Participant 0:
    Task paint | Font big   | Color green
    Task paint | Font small | Color red  
    <BLANKLINE>
    Participant 1:
    Task read | Font small | Color green
    Task read | Font big   | Color red  
    <BLANKLINE>
    Experiment 1:
    <BLANKLINE>
    Participant 0:
    Task paint | Font small | Color red  
    Task paint | Font big   | Color green
    <BLANKLINE>
    Participant 1:
    Task read | Font small | Color green
    Task read | Font big   | Color red  
