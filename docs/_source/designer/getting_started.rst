.. _designer_getting_started:

Getting Started
===============

Installing and starting
-----------------------

The Designer runs on your own computer. A small Python server does the SweetPea
work, and the Designer opens in your web browser. It is in the ``gui`` folder of
the SweetPea repository.

Install SweetPea from source as described in :ref:`guide_installation`. Then,
from the repository folder, install the server's packages and build the
Designer once::

  $ pip install -r gui/backend/requirements.txt
  $ cd gui/frontend
  $ npm install
  $ npm run build

.. attention::

   The Designer needs Python 3.9 or later. Building it needs `Node.js
   <https://nodejs.org>`_ 18 or later.

Start the Designer from the ``gui/backend`` folder::

  $ cd gui/backend
  $ python -m sweetpea_gui

It opens in your browser at http://localhost:8765 and runs until you close the
terminal or press :kbd:`Ctrl+C`.


The window
----------

.. figure:: /_static/designer/overview.jpg
   :alt: The SweetPea Designer, showing the top bar and the Designer, Block
         structure and Python panes side by side.

   The Designer with the *Stroop sessions* example open on the Blocks step.

**Top bar.** **Import…** opens an example or your own ``.py`` file, and
**Save .py** downloads the design as a SweetPea program. The four numbered steps
(**Factors**, **Blocks**, **Constraints**, **Generate**) choose what the
Designer pane shows. **Show / hide panes** turns each pane on or off.

**Designer pane.** Where you build the design. See :ref:`designer_building`.

**Block structure pane.** A drawing of how the blocks fit together. See
:ref:`designer_structure`.

**Python pane.** The design as a SweetPea program. See :ref:`designer_code`.

Hide a pane with its **Hide** button or the top bar; the others then share the
width equally. Drag the bar between two panes to resize them.


Trying an example
-----------------

Choose **Import…** and pick an example, then go to **Generate** and press
**Generate**. The examples range from *Simple: color × size* to *Stroop sessions
(Nest, Repeat, Merge)*.

Importing replaces the current design. Use **Save .py** first to keep it.
