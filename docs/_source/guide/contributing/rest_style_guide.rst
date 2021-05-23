.. _rest_style_guide:

reStructuredText Style Guide
============================

SweetPea's documentation is written in a consistent style of reStructredText
(reST). This helps with managing contributions and makes it easier to read in
code. This section details the specifics of SweetPea's reST style.


General
-------

We restrict reST documentation to not go past the 80th character of a line,
except where absolutely necessary due to potential formatting errors. (For
example, a long hyperlink may extend past the 80th column, but additional text
within the same sentence as that hyperlink should be put on separate lines to
accommodate this rule to the greatest extent possible.)


Roles
^^^^^

`Roles
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html>`_ (reST
items surrounded by colons, like ``:role:``) are each preceded by one empty
line.

If the role has an argument, such as ``:class:`MyClass```, then it immediately
follows the role's declaration. If the role offsets some additional text, such
as the ``:returns:`` role used in documenting function return values, then the
body text is set on the immediately following line, indented by 4 spaces.


Directives
^^^^^^^^^^

Like roles, `directives
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html>`_
(reST items preceded by double-dots and followed by double-colons, like ``..
directive::``) are each preceded by one empty line.

Directives are then followed by one empty line, and the content text begins on
the next line after that. Content text is indented by 4 spaces.


Commonly Used Roles and Directives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You may use any roles or directives you find useful, but there are a number of
them that we already make frequent use of:


Roles
"""""

``:math:`<LaTeX math code>```
    Renders the given ``<LaTeX math code>``. See the `Sphinx documentation on
    how to do math
    <https://www.sphinx-doc.org/en/master/usage/extensions/math.html>`_.


Linking Roles
'''''''''''''

There are a number of roles that form hyperlinks. These can link within the same
documentation, to other documentation (via InterSphinx), or to external
websites. All of these roles can be used in two ways:

``:<role>:`<link>```
    Creates a hyperlink to resource ``<link>``.

``:<role>:`link text <link>```
    Creates a hyperlink to resource ``<link>``, but displays as ``link text``.

We omit the second variety in the following documentation, but it is equally
valid in all cases.

``:ref:`<reference_link>```
    Creates a cross-referencing link to the reST section titled
    ``<reference_link>`` within the same documentation.

``:mod:`<module_name>```
    Links to the documentation on the Python module ``<module_name>``.

``:class:`<class_name>```
    Links to the documentation on the Python class ``<class_name>``.

``:func:`<func_name>```
    Links to the documentation on the Python function ``<func_name>``.

    .. note::

        The ``:func:`` role is also used for documenting methods within classes!

``:attr:`<attr_name>```
    Links to the documentation on the Python attribute ``<attr_name>``.
    Attributes are parts of classes that include fields and methods. Prefer
    ``:func:`` for linking to methods, though, unless they are decorated with
    the ``@property`` decorator, in which case use ``:attr:``.

``:term:`<term_name>```
    Links to the glossary entry to the term ``<term_name>`` on the same page.

    .. note::

        The ``:term:`` role can only be used in conjunction with the
        ``glossary`` directive (documented below).


In Function and Class Docstrings
''''''''''''''''''''''''''''''''

These are roles that are only used inside docstrings for functions and classes.

``:param <param_name>:``
    Documents parameter ``<param_name>`` of the function being documented. This
    is also used in class docstrings, which implicitly document the ``__init__``
    method. The description should begin on the next line, indented by four
    spaces.

``:type <param_name>: <type>``
    Documents the type of parameter ``<param_name>`` as being ``<type>``.
    Usually only necessary in class docstrings. The type should go on the same
    line, unless it is very long (in which case it goes on the next line,
    indented by four spaces).

    .. note::

        You may put ``:type:`` roles on the line immediately following a
        ``:param:``'s description, instead of separating with a line as would
        usually be done. There should still be a blank line after the ``:type:``
        line, though.

``:returns:``
    Documents the return value of a function. The description should begin on
    the next line, indented by four spaces.

``:rtype: <type>``
    Documents the return type of a function as being ``<type>``. Follows the
    same conventions as ``:type:``, documented above.


Directives
""""""""""

``.. code-block:: <optional_language_specification>``
    Begins a literal code block. If a language is specified, syntax highlighting
    will be used. (We only use ``python`` and ``rest`` so far.)

    The ``code-block`` directive is smart and can handle multiple line breaks.

``.. glossary::``
    Creates a glossary of terms where each term has a definition and can be
    linked to with the ``:term:`` role.

``.. toctree::``
    Creates a table of contents tree. The ``toctree`` directive is used on any
    page that collects other pages of documentation, such as
    `docs/_source/index.rst`.


In the Python Code
''''''''''''''''''

There is generally not need for use of directives within the Python docstrings,
but we do make regular use of admonitions. Admonitions are directives which get
styled as a colored box of text and are useful for making warnings or pointing
out particularly noteworthy bits of information. The common admonitions are:

``.. deprecated:: <deprecated_version>``
    Documents when the code has been deprecated. The ``<deprecated_version>`` is
    a required argument, and should indicate the version of SweetPea in which
    the code was deprecated. The description on the next line is optional, but
    if present should be short and tell what to use instead.

``.. note::``
    Generally used to document information for a user of the code. Notes should
    convey interesting information, including behavior that may be slightly
    unintuitive or mildly surprising. Notes can also be used for clarification
    when that seems useful.

    .. note::

        Notes should not be used for behavior that is potentially dangerous or
        especially misleading. Prefer the ``warning`` directive for those cases.

    .. note::

       The ``note`` directive is for documentation. Prefer ``# NOTE: ...`` block
       comments for notes about the code itself.

``.. tip::``
    A handy tip about using the code being discussed. These are generally gentle
    reminders of something a user may have forgotten, but should not contain
    critical information.

``.. todo::``
    Incomplete code or documentation. We generally prefer block comments for
    code to-dos, but a ``todo`` directive is more appropriate when it's marking
    documentation that needs to be finished in the middle of a larger docstring.

``.. warning::``
    Similar to ``note``, but more severe. Warnings should be used to document
    cases where the code may behave surprisingly, such as unexpected
    side-effects.

Note that there are more admonitions than these, and custom admonitions can be
written with the ``admonition`` directive, but these are the ones we currently
use in the Python code.


Docstrings
----------

Python docstrings are triple-quoted strings that are inserted immediately
*after* the construct they document. For example, if we wanted to document a
function ``foo``:

.. code-block:: python

    def foo(arg1: Type1, arg2: Type2) -> ReturnType:
        """Returns the result of fooing ``arg1`` with ``arg2``.

        :param arg1:
            A good argument.

        :param arg2:
            Another good argument.

        :returns:
            Some nifty thing or other.
        """
        # This is the actual function implementation.
        return do_a_foo(arg1, arg2)

Even in docstrings, we restrict reST code to go no further than the 80th column
in a line.


.. _rest_style_guide_functions:

Functions
^^^^^^^^^

Function docstrings should be written in the present tense with active voice,
giving the function agency. For example, a function that adds two numbers might
be documented as:

.. code-block:: python

    def add(lhs: int, rhs: int) -> int:
        """Adds ``lhs`` to ``rhs`` and returns the result.

        .. note::

            This function is just a big wrapper for ``+``.

        :param lhs:
            The left-hand side of the addition.

        :param rhs:
            The right-hand side of the addition.

        :returns:
            The result of adding the numbers.
        """
        return lhs + rhs


Style Notes
"""""""""""

- We use the double quotation mark ``"``.
- The documentation begins on the same line as the initial triple quote ``"""``.
- If the content is short enough to fit on one line and also fit the closing
  triple quote within the 80-character line length limit, the closing triple
  quote goes on the same line.
- If the content itself fits within the 80-character line length limit but the
  closing triple quote does not, the closing triple quote is placed on its own
  line.
- In all other cases, the closing triple quote goes on its own line.
- The function body begins on the line immediately after the closing triple
  quote in every case. (Note that code comments beginning with ``#`` are counted
  as part of the function body.)


Content Notes
"""""""""""""

- The description of the function should be thorough enough to fully explain the
  function's purpose and how to use it, but it should not degrade into examples
  or detailed explanations of experimental designs unless such examples are
  absolutely necessary. Broader discussion of experimental design should be
  relegated to :ref:`the guide <guide>`.
- Parameters are documented *after* the function description.
- All parameters are explicitly documented separately with ``:param ___:``.
- The function's return value is documented with ``:returns:`` *after* the
  parameters.
- All reST `roles
  <https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html>`_
  (such as ``:param ___:`` and ``:returns:``) are preceded by an empty line.


Classes
^^^^^^^

Class docstrings begin just after the class definition begins, and should
describe what an abstract instance of that class is for. Note that the rules for
placing the closing triple quote are the same as those for :ref:`functions
<rest_style_guide_functions>`.

Class docstrings should be written in place of docstrings on ``__init__``
methods, because many classes are written *without* an ``__init__`` (such as
those made with :func:`dataclasses.dataclass`). The class docstrings should
document all of the parameters to the initialization process, including
:class:`InitVars <dataclasses.InitVar>` and the like.

Unlike docstrings for functions, class docstrings should *always* be followed by
an empty line.


Attributes
""""""""""

In most cases, *all* public attributes (fields and methods) should be
documented.

Fields cannot be documented with docstrings, and instead are documented with a
modified form of the Python line comment using ``#:`` instead of ``#``:

.. code-block:: python

    from dataclasses import dataclass


    @dataclass
    class FieldExample:
        """An example for documenting a field.

        :param field:
            The field we're making an example of.
        :type field: int
        """

        #: An integer field in the :class:`.FieldExample`.
        field: int

The style of these comments is identical to that of docstrings, except that each
line must begin with ``#:``. If you want to include a regular (non-reST) comment
about a field, it must go *before* the ``#:`` or else Sphinx will not build the
documentation correctly.

If a field is overriding some default value set by a superclass, the child
class's field does not necessarily need to be documented. Consider the following
example:

.. code-block:: python

    from dataclasses import dataclass


    @dataclass
    class Parent:
        """The parent class in this example.

        :param field:
            The field we're making an example of.
        :type field: int
        """

        #: An integer field for example.
        field: int


    @dataclass
    class Child(Parent):
        """The child class in this example. Note that the :attr:`.field` field
        does not have a ``#:`` reST comment accompanying it.

        :param field:
            The field we're making an example of. Note the nifty new default
            value!
        :type field: int
        """

        field: int = 42

Though not required, it is also encouraged to document atypical non-public
attributes in the same manner as if they were public. By this we mean that you
can omit documentation for common non-public attributes, like double-underscore
methods (e.g., ``__str__``), but we encourage documentation for custom or unique
non-public fields.


Modules
^^^^^^^

Modules should also have docstrings that explain the purpose and use of the
module. Module docstrings are written beginning on the very first line of the
module. All modules should have a module docstring.
