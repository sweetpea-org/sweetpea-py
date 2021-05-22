.. _guide_installation:

Installation and Setup
----------------------

There are two ways to get SweetPea installed on your computer: through the
Python Package Index (via ``pip``) or by cloning the repository and installing
manually.

.. attention::

   SweetPea is developed with Python 3.7.9. It should work in any
   backwards-compatible Python version later than 3.7.9 (and we have integration
   tests for this), but it will likely not work for earlier versions. Please
   ensure you are using at least Python 3.7.9 before installing SweetPea!

Automated Installation from the Python Package Index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install SweetPea from the Python Package Index (PyPI), simply do::

  $ pip install sweetpea

This will automatically install the most recent published release of SweetPea.

Manual Installation from Source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, you can install SweetPea manually. This can be useful if you want
to have the most recent development updates, since the PyPI version will likely
always be slightly behind (to ensure stability).

You can clone the repository, the SweetPea dependencies, and make the
``sweetpea`` package discoverable in your local Python installation by doing::

  $ git clone https://github.com/sweetpea-org/sweetpea-py.git
  $ cd sweetpea-py
  $ pip install -r requirements.txt
  $ pip install -e .

Contributing to SweetPea Development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We also accept contributions to SweetPea. See the :ref:`Contributing to SweetPea
<guide_contributing>` section of the guide for more information.
