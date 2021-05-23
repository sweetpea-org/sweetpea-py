.. _development:

Developing SweetPea
===================

This section of the guide explains how to work on development of the SweetPea
domain-specific language.


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

The repository follows a particular structure:

==================================  ============================================
Directory                           Purpose of Contents
==================================  ============================================
``/``                               Various top-level files.
``/.github/workflows/``             GitHub Workflows for continuous integration.
``/acceptance/``                    Specialized regression tests.
``/docs/``                          All documentation.
``/docs/_build/``                   Where documentation gets built to.
``/docs/_source/``                  Sources for documentation generation.
``/example_programs/``              Examples of using SweetPea in code.
``/sweetpea/``                      Actual SweetPea implementation code.
``/sweetpea/core/``                 Back-end core implementation code.
``/sweetpea/sampling_strategies/``  Code for various sampling strategies.
``/sweetpea/tests/``                The test suite.
==================================  ============================================

.. note::

    In the rest of the documentation, we leave out the initial ``/`` of paths
    when discussing code in the SweetPea repository.


Workflows
---------

SweetPea uses `GitHub Workflows
<https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions>`_
to perform continuous integration testing and handle other jobs. The workflows
are written in YAML and their specifications live in ``.github/workflows/``. The
workflows we currently use are:

``acceptance-fast.yml``
    Runs the default (non-slow) tests in ``acceptance/``. This usually takes
    around 10 minutes to complete if there are no failures.

    Triggers whenever a push includes changes in the following paths:

    - ``.github/workflows/acceptance-fast.yml``
    - ``requirements.txt``
    - ``acceptance/**``
    - ``sweetpea/**``

``acceptance-slow.yml``
    Runs all tests in ``acceptance/``. This usually takes close to 20 minutes to
    complete if there are no failures.

    Triggers on pull requests or whenever a push modifies the
    ``.github/workflows/acceptance-slow.yml`` file.

``gh-pages.yml``
    Publishes the GitHub Pages website.

    Triggers when a push includes changes in the ``docs/_build/html/**`` path.
    This means that to trigger an update in the GitHub Pages, you must
    :ref:`build the documentation <building_the_documentation>` and push the
    resulting changes to that directory.

``platform-report.yml``
    Provides information about the platforms used when running the workflows.

    This workflow never runs automatically. It must be run manually, either
    through the web interface or by using the GitHub Actions API. (You probably
    never need to run it, though.)

``tests.yml``
    Runs the test suite in ``sweetpea/tests/``.

    Triggers on pull requests and whenever a push includes changes in the
    following paths:

    - ``.github/workflows/test.yml``
    - ``requirements.txt``
    - ``sweetpea/**``

``typecheck.yml``
    Runs the mypy static type checker to inspect the code for type correctness.

    Triggers on pull requests and whenever a push includes changes in the
    following paths:

    - ``.github/workflows/typecheck.yml``
    - ``sweetpea/**``


Pull Requests
-------------

We will review all good-faith pull requests. For information on creating a pull
requests, see `GitHub's documentation on the matter
<https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request>`_.
