.. _development:

Developing SweetPea
===================

This section of the guide explains how to work on SweetPea's development.


.. _configuring_development_environment:

Configuring Your Development Environment
----------------------------------------

SweetPea is developed on Python 3.7.9. Unless a backwards-incompatible version
of Python is released, SweetPea should run without issue on newer versions, but
we *require* compatibility with 3.7.9, so we recommend using that for all
SweetPea development.

Like with development of any Python package, use of a `virtual environment
<https://docs.python.org/3/tutorial/venv.html>`_ is recommended.


Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^

SweetPea's required third-party libraries are recorded in the
``requirements.txt`` file at the root of the repository. You can install the
needed libraries with ``pip`` by doing::

    $ pip install -r requirements.txt


Repository Organization
-----------------------

(Explain how the code is organized.)


Workflows
---------

(Explain our GitHub Workflows.)


Pull Requests
-------------

(Explain procedure for making pull requests.)
