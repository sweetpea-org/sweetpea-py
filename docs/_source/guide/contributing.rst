.. _guide_contributing:

Contributing to SweetPea
------------------------

Found some incorrect documentation? Have an idea for an extra feature? We take
pull requests! This part of the guide explains how to contribute to SweetPea
development.

Configuring Your Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SweetPea is developed on Python 3.7.9. Unless a backwards-incompatible version
of Python is released, SweetPea should run without issue on newer versions, but
development *must* be on 3.7.9 to ensure we do not accidentally rely on newer
features.

.. NOTE::
   We chose 3.7.9 because we wanted the most recent version of a major release
   of Python with certain features but which was also stable enough to be
   advisable for widespread use.

Like with any Python package, it is recommended to use a `virtual environment
<https://docs.python.org/3/tutorial/venv.html>`_ for developing SweetPea.

Once your virtual environment is configured, install the necessary dependencies
from the Python Package Index (PyPI)::

  $ pip install -r requirements.txt

Documentation Dependencies
""""""""""""""""""""""""""

The SweetPea documentation has additional dependencies. To install them, do::

  $ pip install sphinx sphinx-rtd-theme

Repository Organization
^^^^^^^^^^^^^^^^^^^^^^^

(Discuss how the SweetPea code is organized, what goes where, etc.)
