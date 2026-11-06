.. _designer_building:

Building a Design
=================

A design is built in four steps, chosen in the top bar: factors, blocks,
constraints, then generating trials. :ref:`guide_factorial_design` explains the
ideas behind each step.


1. Factors
----------

.. figure:: /_static/designer/factors.png
   :alt: Three factor cards: color and size with two levels each, and the
         derived factor volume with a yelling level and an otherwise level.

   The *Simple* example: two factors and a derived factor, *volume*.

**+ Factor** adds a factor. Type its levels into the *+ level, then Enter* box.
The number next to a level is its weight: how often it appears compared with the
other levels. **×** removes a level or a factor.

**+ Derived factor** adds a factor whose level follows from other factors, such
as whether a trial is congruent.

- **Based on** lists the factors it depends on.
- **within the same trial** compares factors in one trial. **compared with the
  previous trial** can also look one trial back, for repeat and switch trials.
- A level applies **when** its condition holds, or **otherwise** when no other
  level does. A factor can have one *otherwise* level.
- A condition compares a factor with a level or another factor, such as
  *color is red* or *color is not word*. **+ and / or** combines conditions.

Renaming a factor or a level updates every place that uses it.

A factor only appears in trials if a block includes it. New factors join the
first block; a factor in no block is marked *not in any block*.


2. Blocks
---------

.. figure:: /_static/designer/blocks.png
   :alt: The Blocks step: a timeline of 16 trials, then a Merge box containing
         the session block, whose Design and Crossing rows have session ticked.

   The Blocks step: the trial timeline, and the first blocks of a design.

A block crosses factors so that every combination of their levels appears. Each
block's box has:

- **Design**: the factors that get a level on every trial.
- **Crossing**: the factors whose combinations are balanced. **+ crossing**
  adds a second crossing over the same trials.
- **every combination must appear**: turn this off when constraints rule out
  some combinations.
- **Advanced**: rarely needed settings for crossings of different sizes.
- **Constraints**: rules that apply within each run of the block.

**Arrange…**, at the top of each box, combines blocks:

Nest inside a new outer block
   Adds an outer block. Each of its combinations is held for a full run of the
   inner block, for example two sessions that each run every Stroop trial.
   Choose the outer block's factor under its **Crossing**.

Merge with other blocks
   Runs blocks over the same trials, each balanced on its own. **+ block** adds a
   block to the Merge; **×** removes one.

Repeat
   Runs the block again until its *Minimum trials* constraint is met.

Remove this Nest / Merge / Repeat
   Removes the arrangement and keeps the blocks inside it.

A Nest, Merge or Repeat has its own constraints, which apply across everything
inside it. Where you put a constraint decides where it applies. In a nested
design, *at most 2 incongruent in a row* on the Repeat holds within each
session; on the Nest it also holds across the change from one session to the
next.


3. Constraints
--------------

The Constraints step lists each block with its constraints. **+ Constraint…**
adds one.

At most K in a row
   A level, or any level of a factor, never repeats more than K trials in a row.

At least K in a row
   Whenever the level appears, it runs for at least K trials.

Exactly K in a row
   Whenever the level appears, it runs for exactly K trials.

Exactly K times
   The level appears exactly K times in each sequence.

Exclude a level
   The level never appears.

Pin a trial
   The trial at a position always has this level. 0 is the first trial, -1 the
   last.

Minimum trials
   Each sequence has at least this many trials.

Cover all combinations
   Every combination of these factors' levels appears, and the sequence is
   sized to fit.

Latin square
   With N levels, every N trials include every level of each factor, and each
   run of N trials takes a different combination.

Sequential
   The factor's levels appear in their listed order, starting over after the
   last.

See :ref:`constraints` for full definitions.


4. Generate
-----------

.. figure:: /_static/designer/generate.png
   :alt: The Generate step with 2 sequences, the CMSGen sampler, and a table of
         trials with color, word, congruency, session and response_hand columns.

   Two generated sequences of the *Stroop sessions* design.

Choose how many **Sequences** to make and a **Sampler**, then press
**Generate**. Each sequence appears as a table of trials. **Download CSV** saves
all sequences in one file, with a sequence and a trial number on each row.

If no sequence fits the design, the Designer reports that the solver found no
answer (UNSAT). Loosen or remove a constraint and try again. **Solver report**
shows SweetPea's own output.


.. _designer_errors:

When something is wrong
-----------------------

The Designer checks the design after every change:

- Boxes refuse impossible values, such as a name already in use or a K below 1.
- Mistakes in the design, such as a factor with no levels, show as a message at
  the top of the Designer pane, and *Design has a problem* appears in the top
  bar. The message names what is wrong and how to fix it. **Generate** stays
  off until it is fixed.
- Code the Designer cannot read is reported with its line number. See
  :ref:`designer_code`.

Only a design with no solution waits for **Generate**, because only the solver
can find that out.
