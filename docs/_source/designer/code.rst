.. _designer_code:

Working with Code
=================

Every design in the Designer is a SweetPea program, shown in the Python pane.


Editing in either place
-----------------------

A change in the Designer updates the program at once. A change typed into the
Python pane updates the Designer after a short pause.

When the Designer changes a program, it writes it in a standard layout: one
variable per block, with named arguments. Code written in another layout is
reformatted, and its comments are lost; the design stays the same.

**Generate** runs exactly the program in the Python pane.


Opening and saving
------------------

**Import…** in the top bar opens an example or, with *A .py file…*, your own
program. **Save .py** downloads the current program. For example, this program
opens as a Stroop block with a congruency factor and one constraint:

.. code-block:: python

   from sweetpea import *

   color = Factor("color", ["red", "blue"])
   word = Factor("word", ["red", "blue"])
   congruency = Factor("congruency", [
       DerivedLevel("congruent", WithinTrial(lambda color, word: color == word, [color, word])),
       DerivedLevel("incongruent", WithinTrial(lambda color, word: color != word, [color, word])),
   ])

   block = CrossBlock([color, word, congruency], [color, word],
                      [AtMostKInARow(2, (congruency, "incongruent"))])
   experiments = synthesize_trials(block, 3, CMSGen)


Code the Designer can read
--------------------------

As well as factors, blocks and constraints like those above, the Designer reads:

- conditions written with ``lambda`` or ``def``, including an ``if`` that
  returns ``True`` or ``False``, one condition function calling another, and
  ``in`` tests such as ``color in ("red", "green")``;
- ``CrossBlock``, ``MultiCrossBlock``, ``Nest``, ``Merge`` and ``Repeat``, with
  ``RepeatMode`` and ``AlignmentMode``;
- variables holding levels, numbers, lists and blocks;
- the samplers ``CMSGen``, ``IterateGen`` and ``RandomGen``.

.. figure:: /_static/designer/code-error.png
   :alt: The Python pane with random.seed(1) underlined on line 19, and a
         message in the Designer pane that says the code can't be shown in the
         designer at line 19.

   Code the Designer cannot read is underlined, and the Designer pane is locked.

For anything else, a message names the line and what the Designer cannot show,
the line is underlined, and the Designer pane is locked until the code is fixed.
**Restore the code from the designer** puts back the last program the Designer
could read.


.. _designer_limitations:

Not supported yet
-----------------

The Designer cannot yet show:

- ``Window`` derivations that look more than one trial back;
- ``ContinuousFactor``;
- ``Relax``;
- samplers with settings, such as ``RandomGen(acceptable_error=3)``;
- more than one ``synthesize_trials`` call;
- code that uses the generated trials, such as analysis.

Programs that use these still run in SweetPea; they cannot be opened in the
Designer.
