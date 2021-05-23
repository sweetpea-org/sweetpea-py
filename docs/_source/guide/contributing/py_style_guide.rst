.. _py_style_guide:

Python Style Guide
==================

This section documents the specifics of the Python style preferred in the
SweetPea code.


Note on PEP 8
-------------

In most cases, SweetPea's code follows `PEP 8
<https://www.python.org/dev/peps/pep-0008/>`_, the official Python style guide.
However, there are some extra rules we follow, and some rules we relax. These
are all detailed below. If something is not detailed below, look for examples of
similar constructs in the existing code. If nothing can be found to explain how
something should be done, we defer to PEP 8 or, if PEP 8 has nothing to say on
the matter, the developer's intuition.


Maximum Line Length
-------------------

Lines of code are limited to 120 characters in length. Comments and docstrings
are limited to 80 characters in length.


Blank Lines
-----------

Top-level constructs, such as classes, functions, etc, are preceded by two blank
lines.

Related single-line statements can be grouped or separated by single blank
lines. For example, multiple type aliases can be separated into logical groups
as follows:

.. code-block:: python

    T = TypeVar('T')
    StrOrT = Union[str, T]

    U = TypeVar('U')


Imports
-------

- Never use star-imports (i.e., imports of the form ``from <module> import *``).
- Prefer explicit imports (i.e., ``from <module> import <item1>, <item2>``).
- Whole-module imports are allowed, but generally discouraged (i.e., ``import
  <module>``).
- Place imports after the module-level dunder names (e.g., ``__all__``).

  .. note::

      This does not include ``__future__`` imports, which may only be preceded
      by the module docstring! An example is given below.

- Order imports as: standard library, third-party libraries, current library,
  with a blank line between each section.
- Place whole-module imports within a section ahead of the explicit imports from
  the same section, separated by a blank line.
- Prefer fully qualified imports instead of relative imports.

To put all that together:

.. code-block:: python

    """This module does some neat things."""


    from __future__ import annotations


    __all__ = ['Export1', 'Export2']


    import math

    from dataclasses import dataclass
    from typing import List

    import numpy

    from my_package.core_stuff import CoreThing

(Where ``my_package`` is the module in which this code appears.)


String Quotes
-------------

Prefer double quotation marks ``"`` for most strings. Single quotation marks
``'`` can be used for literal values, but we are moving away from this style.

Triple-quoted strings *always* use double quotation marks ``"``.


Trailing Commas
---------------

Prefer trailing commas in lists of items where each item appears on its own
line. For example, you may have a list of people where each ``Person`` is
defined on its own line. Leave a trailing comma after the final element:

.. code-block:: python

    people = [
        Person('Alex', 27),
        Person('Taylor', 32),
        Person('Cleopatra', 2091),
    ]


Comments
--------

- *Comments are part of the code.* If you change some code in a way that renders
  the comment incorrect, your code is now incorrect. Update comments whenever
  you change the code the comment is documenting.
- Comments should be written in complete sentences, with grammatical
  consistency, correct spelling, punctuation, etc.
- Separate sentences with one space, not two.


Block Comments, Inline Comments, and Documentation Strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Block comments* are lines consisting of only comment material, written as one
or more lines of (possibly indented) text written after a leading ``#`` on each
line.

*Inline comments* are comments placed on the same line as some code. We strongly
discourage the use of inline comments, except where they are used for providing
information to a static type-checker or a linter.

*Documentation strings*, generally called "docstrings", are triple-quoted
strings that adorn functions, classes, and modules. There are extra rules about
docstrings, found in :ref:`the reST style guide <rest_style_guide>`.

To put all these into an example:

.. code-block:: python

    def some_function(arg1: Type1, arg2: Type2) -> ReturnType:
        """This is the *docstring* that documents the :func:`.some_function`
        function.

        ... (the rest of the docstring)
        """
        # Keep track of a sentinel. (This is a single-line block comment.)
        sentinel = False
        for thing in generator_of_things():
            # Check each `thing` for some cool property.
            #
            # This is an example of a block comment with multiple paragraphs,
            # which can come in handy sometimes.
            #
            # NOTE: Sometimes you'll find notes in the code. These are useful
            #       because most editors will highlight the capitalized NOTE. We
            #       use these in block comments, but not in docstrings where we
            #       would instead use the `note` directive. Note that the
            #       subsequent lines of text are indented to the level of the
            #       first line of the note, leaving a margin on the side.
            if has_cool_property(thing):
                return ReturnType('cool')  # This would be an inline comment.
            else:
                return ReturnType('boring')


Type-Checking or Linting Overrides
----------------------------------

Sometimes, the type-checkers or linters we use are wrong about something,
possibly due to a bug or insufficiency. In these cases, they can be disabled on
a line-by-line basis using specific inline comment forms.

To disable mypy checking, simply add ``# type: ignore`` at the end of a line
that mypy is complaining about.

To disable pylint warnings, prefer to explicitly disable the warning raised on a
given name by doing ``pylint: disable=CHECK-TO-DISABLE``.

In all such cases, we strongly encourage placing a ``NOTE``-style block comment
on the preceding line explaining why the check was disabled. This should usually
point to a documented issue to support the choice.

For example, the two subclasses of :class:`.Level` (:class:`.SimpleLevel` and
:class:`.DerivedLevel`) override the :mod:`dataclasses`-implemented
``__post_init__`` methods with signatures that deviate from that of the base
:class:`.Level` class. This is usually disallowed by the `Liskov Substitution
Principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`_, which
says that subclasses should have compatible method signatures with their
parents. But this is a special case where such deviation is perfectly reasonable
and, in fact, necessary, so we had to disable type-checking and linting on those
lines. The :class:`.SimpleLevel` definition looks like this, as of this writing
(with some unimportant parts abridged for clarity):

.. code-block:: python

    @dataclass(eq=False)
    class SimpleLevel(Level):
        """... (Docstring removed for this example.)"""

        weight: InitVar[int] = 1

        # NOTE: The __post_init__ method is a special case where we can ignore the
        #       Liskov substitution property. This is addressed in
        #       python/mypy#9254:
        #           https://github.com/python/mypy/issues/9254
        def __post_init__(self, weight: int):  # type: ignore # pylint: disable=arguments-differ
            super().__post_init__()
            self._weight = weight

Note that this is also a case where comments may reach beyond the 80-character
limit.

.. tip::

    Combining the check-disabling directives can sometimes be confusing, but it
    seems that the mypy ``# type: ignore`` has to come first, and PyLint's ``#
    pylint: diable=CHECK-TO-DISABLE`` has to come last.
