.. _designer_structure:

Reading the Block Structure
===========================

The Block structure pane draws how a design's blocks fit together. Click any
part of the drawing to open that block on the Blocks step.

.. figure:: /_static/designer/structure.png
   :alt: The session_block frame, with chips for morning and afternoon, contains
         the stroop_trials block with a circular repeat arrow. A plus junction
         joins the frame to the hand_assignment block, and a bracket underneath
         reads Merge, experiment, 16 trials.

   The *Stroop sessions* example: Stroop trials run twice in each of two
   sessions, merged with a balanced response hand.

**Blocks.** A box shows the block's name in bold, what it crosses, and its
number of trials. The strip at the bottom has a tick for each trial.

**Nest: a frame.** The outer block frames the inner block. The frame's header
shows the outer block's name and a chip for each combination it holds, here
*morning* and *afternoon*. Everything inside runs once for each chip. The band
at the bottom of the frame belongs to the Nest: its name, its trials, and the
constraints that apply across all of them.

**Merge: side by side.** Merged blocks sit next to each other, joined by a
**+**. The bracket underneath gives the Merge's name, its trials and its
constraints. Every trial gets a level from each merged block.

**Repeat: a circular arrow.** The arrow leaves the block and points back into
it. The label above gives the number of runs, such as **repeat ×2**, with the
constraints that span the runs underneath.

**Constraints.** Each constraint is a chip marked with a chain-link icon, placed
on what it governs: a block, a Nest's band, a Merge's bracket, or a Repeat's
arrow.

**Zoom.** The drawing shrinks to fit the pane. Use **+** and **−** to zoom in,
and **Fit** to see the whole design again.


The timeline
------------

The Blocks step also shows a timeline of one sequence, with a row for each
block's crossing (see :ref:`designer_building`). An outer block shows one span
for each combination it holds; a plain block shows a tick for each trial. After
**Generate**, the spans show the levels of the first sequence.
