from typing import Any, Type, List, Tuple, Union, cast
from itertools import product, chain, repeat
import random


# TODO: Why do these functions exist? Just... do `level.internal_name` and
#       `level.external_name`? These don't seem helpful.
def get_internal_level_name(level: Any) -> Any:
    """Returns the internal name of a level.

    :param level:
        The level of which to get the internal name.

    :returns:
        The internal name of the ``level``.
    """
    return level.internal_name


def get_external_level_name(level: Any) -> Any:
    """Returns the external name of a level.

    :param level:
        The level of which to get the external name.

    :returns:
        The external name of the ``level``.
    """
    return level.external_name


# TODO: This class provides absolutely nothing useful whatsoever.
class __Primitive:
    def require_type(self, label: str, type: Type, value: Any):
        if not isinstance(value, type):
            raise ValueError(label + ' must be a ' + str(type) + '.')

    def require_non_empty_list(self, label: str, value: Any):
        self.require_type(label, List, value)
        if len(value) == 0:
            raise ValueError(label + ' must not be empty.')

    def __str__(self):
        raise Exception("Attempted implicit string cast of primitive")


# TODO: Factor out the common bits of the Level classes into a `BaseLevel`.
# TODO: Simplify this.
class SimpleLevel(__Primitive):
    def __init__(self, name: Any):
        self.external_name = str(name)
        # TODO: Is random the way to go here? Maybe a UUID would be better, or
        #       a global counter that increments each time?
        self.internal_name = str(name) + "{:05d}".format(random.randint(0, 99999))
        # TODO: Inline.
        self.__validate()

    def __validate(self):
        # TODO: Does this do anything? The `object` type implements `__eq__`
        #       trivially, so this should never fail.
        if not (hasattr(self.external_name, "__eq__")):
            raise ValueError("Level names must be comparable, but received "
                             + str(self.external_name))

    def __str__(self):
        # TODO: There's no guarantee that this is the result of an *implicit*
        #       conversion.
        raise Exception("Attempted implicit string cast of simple level")

    # TODO: Remove.
    def set_factor(self, factor):
        self.factor = factor

    def __eq__(self, other):
        # TODO: This should probably be `isinstance`, not `type(__) ==`.
        if (type(other) != SimpleLevel):
            print("Attempted to compare a simple level to another type, " + str(type(other)))
        return other.internal_name == self.internal_name

    # TODO: This makes multiple instances of `DerivedLevel` with the same name
    #       indistinguishable. Is this behavior desirable?
    # TODO: Do we actually need `__hash__` support? Maybe check that.
    def __hash__(self):
        return hash(self.internal_name)


# TODO: DOC
# TODO: I really dislike these functions. They're just aliases for the class
#       constructors, which seems not-so-helpful. If we keep them, these should
#       be moved to `__init__.py` and provide some useful default values or
#       something.
def simple_level(name) -> SimpleLevel:
    return SimpleLevel(name)


class DerivedLevel(__Primitive):
    def __init__(self, name, window):
        # TODO: I think we should just require `name` to be a string when it
        #       comes in, leaving it to the client to determine how that
        #       happens.
        self.external_name = str(name)
        # TODO: Same as SimpleLevel: is random the way to go here?
        self.internal_name = str(name) + "{:05d}".format(random.randint(0, 99999))
        self.window = window
        # TODO: Inline.
        self.__validate()
        # TODO: Inline.
        self.__expand_window_arguments()

    def __validate(self):
        # TODO: The `external_name` is set equal to the result of `str` in
        #       `__init__`, so how can this ever fail?
        self.require_type('DerivedLevel.external_name', str, self.external_name)
        # TODO: Simplify.
        # TODO: Maybe also save this somewhere as an attribute?
        window_type = type(self.window)
        allowed_window_types = [WithinTrial, Transition, Window]
        if window_type not in allowed_window_types:
            raise ValueError('DerivedLevel.window must be one of ' + str(allowed_window_types) + ', but was ' + str(window_type) + '.')
        for f in self.window.args:
            if f.has_complex_window() and f.levels[0].window.stride > 1:
                raise ValueError('DerivedLevel can not take factors with stride > 1, found factor with stride = ' + str(f.levels[0].window.stride) + '.')

    # TODO: Inline.
    def __expand_window_arguments(self) -> None:
        # TODO: Rewrite as list comprehension and simplify.
        self.window.args = list(chain(*[list(repeat(arg, self.window.width)) for arg in self.window.args]))

    # TODO: This return type seems almost entirely useless.
    def get_dependent_cross_product(self) -> List[Tuple[Any, ...]]:
        # TODO: Use a list comprehension instead of this list/product business.
        return list(product(*[[(dependent_factor, x) for x in dependent_factor.levels] for dependent_factor in self.window.args]))

    # TODO: Remove.
    def set_factor(self, factor):
        self.factor = factor

    def __eq__(self, other):
        # TODO: This should probably be `isinstance`, not `type(__) ==`.
        if (type(other) != DerivedLevel):
            print("Attempted to compare a derived level to another type, " + str(type(other)))
        # TODO: This works the same as SimpleLevel. Maybe one should subclass
        #       the other?
        return self.internal_name == other.internal_name

    # TODO: Same comments as `SimpleLevel.__hash__`.
    def __hash__(self):
        return hash(self.internal_name)

    def __repr__(self):
        # TODO: This should be `repr`, not `str`, probably.
        # TODO: Not sure the pervasive use of `self.__dict__` is a good idea.
        #       It's... everywhere in this module, though.
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def derived_level(name, derivation) -> DerivedLevel:
    """Creates a :class:`.DerivedLevel`, which depends on the levels of other
    factors in a design.

    :param name:
        The level's name, which can be any printable value.

    :param derivation:
        A condition on other factors' levels. See
        :ref:`guide_factorial_derivations`.

    :returns:
        A :class:`.DerivedLevel` with the indicated ``name`` and
        ``derivation``.
    """
    return DerivedLevel(name, derivation)


# TODO: This name doesn't make sense. Replace it?
# TODO: Actually, it seems that `ElseLevel`s are just eventually translated
#       into `DerivedLevel`s. What's up with that?
class ElseLevel():
    def __init__(self, name):
        self.name = name

    # TODO: Remove.
    def set_factor(self, factor):
        self.factor = factor

    # TODO: Wait, hang on, `ElseLevel` is callable? But... why? This seems like
    #       an inconsistent API, which could lead to confusion.
    def __call__(self, other_levels: List[DerivedLevel]) -> DerivedLevel:
        if other_levels is None:
            return DerivedLevel(self.name, WithinTrial(lambda: False, []))
        some_level = other_levels[0]
        # TODO: This... is never used?
        other_functions = list(map(lambda dl: dl.window.fn, other_levels))
        args = some_level.window.args[::some_level.window.width]
        window = Window(lambda *args: not any(map(lambda l: l.window.fn(*args), other_levels)), args, *some_level.window.size())
        return DerivedLevel(self.name, window)

    # TODO: Why does ElseLevel not implement the other methods that SimpleLevel
    #       and DerivedLevel do?


def else_level(name) -> ElseLevel:
    return ElseLevel(name)


class Factor(__Primitive):
    """In factorial experimental design, a *factor* is an independent variable
    under examination. Factors have a ``name`` and are composed of *levels*,
    where each level corresponds to a discrete value a factor can assume as
    part of the experiment.
    """

    def __init__(self, name: str, levels):
        """
        :param name:
            The name of the :class:`.Factor`.

        :param levels:
            The possible values the :class:`.Factor` can assume. The ``levels``
            can be given as an iterable of either elements produced by calls to
            :func:`.derived_level` or just plain :class:`strs <str>`.

            When the levels are instances produced by :func:`.derived_level`,
            they must all be distinct, mutually exclusive, and cover all cases.
            This is the preferred mechanism for specifying levels.

            When the levels are all :class:`strs <str>`, they will be
            internally converted into levels like those produced by
            :func:`.derived_level`. Multiple instances of equivalent strings
            are considered as distinct levels.

            .. WARNING::
                Because the resulting levels will have identical names, using
                the name of those levels in constraints or deriving other
                factors from this :class:`.Factor` will treat that name as an
                accessor for all matching levels. Be careful!
        """
        self.factor_name = name
        # TODO: Inline.
        self.levels = self.__make_levels(levels)
        # TODO: Inline.
        self.__validate()

    def __make_levels(self, levels):
        out_levels = []
        # TODO: Inline.
        self.require_non_empty_list('Factor.levels', levels)
        # TODO: I think we should re-evaluate the handling of `ElseLevel`. This
        #       is super weird.
        for level in levels:
            if isinstance(level, ElseLevel):
                out_levels.append(level(list(filter(lambda l: isinstance(l, DerivedLevel), levels))))
            elif isinstance(level, DerivedLevel):
                out_levels.append(level)
            else:
                out_levels.append(SimpleLevel(level))
        for level in out_levels:
            level.set_factor(self)
        return out_levels

    def __validate(self):
        # TODO: Convert to type hint.
        self.require_type('Factor.factor_name', str, self.factor_name)
        # TODO: This is used elsewhere... so it should just be an attribute.
        level_type = type(self.levels[0])
        # TODO: Simplify.
        if level_type not in [SimpleLevel, DerivedLevel]:
            raise ValueError('Factor.levels must be either SimpleLevel or DerivedLevel')

        # TODO: Simplify.
        # TODO: Rename.
        for l in self.levels:
            if type(l) != level_type:
                raise ValueError('Expected all levels to be ' + str(level_type) +
                    ', but found ' + str(type(l)) + '.')

        # TODO: Don't love this.
        if level_type == DerivedLevel:
            window_size = self.levels[0].window.size()
            for dl in self.levels:
                if dl.window.size() != window_size:
                    raise ValueError('Expected all DerivedLevel.window sizes to be ' +
                        str(window_size) + ', but found ' + str(dl.window.size()) + '.')
            window_args = self.levels[0].window.args
            for dl in self.levels:
                if dl.window.args != window_args:
                    raise ValueError('Expected all DerivedLevel.window args to be ' +
                            str(list(map(lambda x: x.factor_name, window_args))) + ', but found ' + str(list(map(lambda x:x.factor_name, dl.window.args))) + '.')

    # TODO: Make this a property.
    def is_derived(self) -> bool:
        # TODO: Use new level type attribute.
        return isinstance(self.levels[0], DerivedLevel)

    def has_complex_window(self) -> bool:
        if not self.is_derived():
            return False

        # TODO: We only check the window in the first level? Is that right?
        window = self.levels[0].window
        return window.width > 1 or window.stride > 1 or window.args[0].has_complex_window()

    def get_level(self, level_name: str) -> Union[SimpleLevel, DerivedLevel]:
        # TODO: Rename.
        for l in self.levels:
            if l.internal_name == level_name:
                return l
        # TODO: This cast makes no sense --- it undermines the type system.
        return cast(SimpleLevel, None)

    def has_level(self, level: Any) -> bool:
        # TODO: Is this why all the levels are hashable? Is this it? I'd rather
        #       have an explicit dictionary mapping level names to levels. This
        #       would also admit an O(1) lookup in `Factor.get_level`, which
        #       seems worth it.
        return (level in self.levels)

    # TODO: Do `Factor`s need to be hashable?
    def __hash__(self):
        return(hash(self.factor_name))

    def applies_to_trial(self, trial_number: int) -> bool:
        """Determines whether this :class:`.Factor` applies to the given trial
        number. For example, :class:`Factors <.Factor>` with
        :class:`.Transition` windows in derived levels do not apply to trial
        ``1``, but do apply to all subsequent trials.

        .. TIP::
            Trials start their numbering at ``1``.
        """
        # TODO: Simplify this implementation.
        if trial_number <= 0:
            raise ValueError('Trial numbers may not be less than 1')

        if not self.is_derived():
            return True

        def acc_width(w) -> int:
            return w.width + (acc_width(w.args[0].levels[0].window)-1 if w.args[0].has_complex_window() else 0)

        window = self.levels[0].window

        return trial_number >= acc_width(window) and (trial_number - window.width) % window.stride == 0

    # TODO: Oh I really don't like this. Rewrite.
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        # TODO: This should probably be `repr`, not `str`.
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def factor(name: str, levels) -> Factor:
    """Creates a plain :class:`.Factor` for use in an experimental design.

    :param name:
        The name of the :class:`.Factor` to create.

    :param levels:
        The :class:`.Factor`'s possible values.

    :returns:
        A :class:`.Factor` with the indicated ``name`` and ``levels``.
    """
    return Factor(name, levels)


# TODO: Maybe change this to `Derivation` for consistency?
class __BaseWindow():
    # TODO: Rename some of these fields.
    def __init__(self, fn, args, width: int, stride: int) -> None:
        self.fn = fn
        self.args = args
        self.argc = len(args)
        self.width = width
        self.stride = stride
        # TODO: Inline.
        self.__validate()

    def __validate(self):
        # TODO: I'm unsure about checking all these things. I'd rather leave
        #       all this up to type annotations and mypy.
        if not callable(self.fn):
            raise ValueError('Derivation function should be callable, but found ' + str(self.fn) + '.')
        for f in self.args:
            if not isinstance(f, Factor):
                raise ValueError('Derivation level should be derived from factors, but found ' + str(f) + '.')
        if self.width < 1:
            raise ValueError('Window width must be at least 1, but found ' + str(self.width) + '.')
        if self.stride < 1:
            raise ValueError('Window width must be at least 1, but found ' + str(self.stride) + '.')

        if len(set(map(lambda f: f.factor_name, self.args))) != self.argc:
            raise ValueError('Factors should not be repeated in the argument list to a derivation function.')


# TODO: This is a bad name, honestly. It's not consistent with the other
#       `__BaseWindow` subclass names.
# TODO: Also, why do each of the `__BaseWindow` subclasses also inherit from
#       `__Primitive` instead of just making `__BaseWindow` a subclass of
#       `__Primitive` directly?
class WithinTrial(__Primitive, __BaseWindow):
    """A description of a level that is selected depending on levels from other
    factors, all within the same trial.
    """

    def __init__(self, fn, args):
        super().__init__(fn, args, 1, 1)

    # TODO: This method should have a base implementation in the superclass.
    def size(self):
        return (1, 1)

    # TODO: Don't love this. Rewrite.
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        # TODO: This should probably be `repr`, not `str`.
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def within_trial(fn, args) -> WithinTrial:
    """Creates a :class:`.WithinTrial` derivation. (See the guide's page on
    :ref:`derivations <guide_factorial_derivations>`.)

    :param fn:
        A function that takes as many level names as factors in ``args``. The
        function should be a predicate that returns ``True`` if the combination
        of levels implies the result derivation.

    :param args:
        A list of factors whose levels determine whether a level with the
        returned derivation is selected.

    :returns:
        A :class:`.WithinTrial` derivation.
    """
    return WithinTrial(fn, args)


class Transition(__Primitive, __BaseWindow):
    """A description of a level that is selected depending on a combination of
    levels from other factors in the current trial and the immediately
    preceding trial.
    """

    def __init__(self, fn, args):
        super().__init__(fn, args, 2, 1)

    # TODO: Implement in superclass.
    def size(self):
        return (2, 1)

    # TODO: Rewrite.
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        # TODO: This should probably be `repr`, not `str`.
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def transition(fn, args) -> Transition:
    """Creates a :class:`.Transition` derivation. (See the guide's page on
    :ref:`derivations <guide_factorial_derivations>`.)

    :param fn:
        A function that takes as many level lists as factors in ``factors``. In
        each list, the first element is the level value for the previous trial,
        and the second element is the level value for the current trial. The
        function should return ``True`` if the combination of levels implies
        the result derivation, and ``False`` otherwise.

    :param args:
        A list of factors whose levels across trials determine whether a level
        with the returned derivation is selected.

    :returns:
        A :class:`.Transition` derivation.
    """
    return Transition(fn, args)


class Window(__Primitive, __BaseWindow):
    """Describes a level that is selected depending on a combination of levels
    from other factors in the current trial and multiple preceding trials.

    A :class:`.Window` is a generalization of a :class:`.Transition`
    derivation that selects a level depending on multiple trials, and where
    preceding trials are separated by ``stride - 1`` intervening trials.
    """

    def __init__(self, fn, args, width, stride):
        super().__init__(fn, args, width, stride)

    # TODO: Implement in superclass.
    def size(self):
        return (self.width, self.stride)

    # TODO: Rewrite.
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        # TODO: This should probably be `repr` instead of `str.`
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def window(fn, args, width, stride) -> Window:
    """Creates a :class:`.Window` derivation. (See the guide's page on
    :ref:`derivations <guide_factorial_derivations>`.)

    The :func:`.window` function is a generalization of the :func:`.transition`
    function that selects a level depending on multiple trials, and where
    preceding trials are separated by ``stride - 1`` intervening trials.

    :param fn:
        A function that takes as many level lists as factors in ``factors``. In
        each list, the first element is the level value for the earliest of
        ``width`` trials, and so on. The function should return ``True`` if
        the combination of levels implies the result derivation, and ``False``
        otherwise.

    :param args:
        A list of factors whose levels across trials determine whether a level
        with the returned derivation is selected.

    :param width:
        The number of trials of ``factors`` to consider when selecting the new,
        derived level.

    :param stride:
        One more than the number of trials to skip between the trials that are
        considered when selecting the new, derived level.

    :returns:
        A :class:`.Window` derivation.
    """
    return Window(fn, args, width, stride)
