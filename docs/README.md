# SweetPea Documentation Meta Information

This page gives information about the resources and process involved in writing
documentation for SweetPea. This is not itself documentation of the SweetPea
language or package.


## Structure of This Directory

The `/docs/` directory contains:

  * `.gitignore`
      * Manages documentation-specific git settings.
  * `Makefile`
      * Builds the documentation.
  * `README.md` (this file)
      * Informs contributors about how SweetPea's documentation works.
  * `_build/`
      * Contains the results of documentation generation (i.e., the
        documentation itself).
  * `_source/`
      * Contains the inputs to the documentation generator.


## Reading

The documentation for the current published version of SweetPea is available
[online](https://sweetpea-org.github.io). However, you can build a local copy by
following the [Building](#building) instructions below, and then opening the
file [`./_build/html/index.html`](./_build/html/index.html) in your web
browser.


## Building

To build the documentation, install the necessary dependencies and then invoke
the `Makefile`. Ensure the SweetPea requirements are installed (see the SweetPea
documentation), and then:

    $ pip install sphinx sphinx-rtd-theme
    $ make html

This will build the documentation as a website with its home page at
`_build/html/index.html`.


### Sphinx

SweetPea's documentation is built using the
[Sphinx](https://www.sphinx-doc.org/en/master/) documentation generation tool,
which is invoked via the `Makefile` in this directory. The standard `make`
invocation we use to generate the web pages is (from this directory):

    $ make html

This will build the necessary documentation and output the results as `.html`
web pages in the `_build/html/` subdirectory.

Sphinx's operation can be configured by code in the `_source/conf.py` file. The
options employed in this configuration can be found in the Sphinx documentation.


#### Automatic Documentation

We currently don't try generate documentation from docstrings. That
approach tends to confuse internal implementation documentation with
the public API.

#### Documentation Style

We also use the [Read The Docs Sphinx
Theme](https://sphinx-rtd-theme.readthedocs.io/en/stable/) to style our
documentation. If you want to build the documentation locally, you'll need to
install the theme to get the same result:

    $ pip install sphinx-rtd-theme


## Contributing

Documentation for SweetPea is written in the Sphinx flavor of [reStructuredText
(reST)](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html).
Contributions to the SweetPea documentation can be separated into two
categories:

  1. Documentation in the SweetPea Guide.
  2. Technical documentation in the `sweetpea` Python package.

Guide documentation (1) is meant to be prose that explains what SweetPea is, how
it works, and how to use it. This constitutes information on installation,
configuration, usage tutorials, etc., but it does *not* include lengthy
technical documentation. The technical documentation (2) is written in the
`sweetpea` Python code directly, and it is extracted automatically by
sphinx-apidoc [as explained above](#automatic-documentation).


### reStructuredText (reST)

reStructuredText, or reST, is the markup language used by the Sphinx
documentation build system. An explanation of reST is beyond the scope of this
README, but information about SweetPea's particular usage can be found in the
SweetPea Guide section on [Contributing to the
Documentation](https://sweetpea-org.github.io/guide/contributing/documentation).


### Guide Documentation

The SweetPea Guide is meant as an explanation of how to get SweetPea working and
then use it to design experiments. The Guide is not the place for technical
minutiae. It should maintain a clear, prose-like tone as though dictated by an
excellent instructor.
