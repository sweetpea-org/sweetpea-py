"""This module provides the fundamental primitives used by the SweetPea
domain-specific language.

A Note on Deprecations
''''''''''''''''''''''

A number of functions, classes, methods, and attributes in this file are marked
as *deprecated*. These are preserved for backwards compatibility, but will
eventually be removed in favor of alternative forms.
"""


# NOTE: This import allows for forward references in type annotations.
from __future__ import annotations


__all__ = [
    'Level', 'SimpleLevel', 'DerivedLevel', 'ElseLevel',
    'Factor', 'SimpleFactor', 'DerivedFactor',
    'DerivationWindow', 'WithinTrialDerivationWindow', 'TransitionDerivationWindow',
    # Backwards compatibility:
    'get_external_level_name', 'get_internal_level_name',
    'WithinTrial', 'Transition', 'Window',
    'simple_level', 'derived_level', 'else_level', 'factor', 'within_trial', 'transition', 'window',
]


from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from itertools import product
from random import randint
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, cast


###############################################################################
##
## Levels
##


"""

TODO: REMOVE

Level weights are relative. They are positive integer values*, where the value
represents the number of variables devoted to that level. If we imagine two
factors with a few levels, all with the default weight of 1:

    f0 = Factor('color', ['red', 'blue', 'green'])
    f1 = Factor('text', ['red', 'blue'])

and convert them into a CNF formula, we will have one variable per level:

    (1 ∨ 2 ∨ 3) ∧ (4 ∨ 5 ∨ 6)

If we adjust one of the `color` levels to have a weight of `2`, though:

    f0 = Factor('color', ['red', SimpleLevel('blue', 2), 'green'])
    f1 = Factor('text', ['red', 'blue'])

The formula would instead look like:

    (1 ∨ 2 ∨ 3 ∨ 4) ∧ (5 ∨ 6 ∨ 7)

The `blue` level now has two variables: `3` and `4`. When sampling, this gives
that level two opportunities to be chosen for every one time either of the
other levels could be chosen.

* They don't have to be positive integers forever. Eventually, they can support
varieties of values for greater configuration, but for the moment we'll stick
with the integers.

"""


@dataclass
class Level:
    """A discrete value that a :class:`.Factor` can hold.

    .. note::

        Do not directly instantiate :class:`.Level`. Instead, construct one of
        the subclasses:

        - :class:`.SimpleLevel`
        - :class:`.DerivedLevel`
        - :class:`.ElseLevel`

    For more on levels, consult :ref:`the guide <guide_factorial_levels>`.
    """

    #: The name of the level.
    name: str

    # TODO: I think we can get rid of `Level.internal_name` and replace it with
    #       some other mechanism. See the TODO notes in `Level.__post_init__`.
    #: The internal name, which is meant to be unique among levels.
    #:
    #: .. deprecated:: 0.1.0
    #:
    #:     This attribute will be removed. It should not be used outside of
    #:     this module.
    internal_name: str = field(init=False)

    # TODO: There is probably a way to make this smoother. As it stands,
    #       factors are responsible for registering themselves with their
    #       levels. Perhaps factors could be the only way to create levels?
    #: The factor to which this level belongs.
    factor: Factor = field(init=False, repr=False)

    # NOTE: Because of the way dataclasses work, a base class (e.g., `Level`)
    #       cannot provide an attribute with a default value if a subclass
    #       (e.g., `DerivedLevel`) provides additional non-default values. This
    #       means the base class cannot provide a `weight` field with a default
    #       value of `1`, which is what we want to achieve. (Additionally,
    #       we'd prefer the `weight` to always be the last field of a level's
    #       initialization parameters.)
    #           The solution is to have the base class implement a hidden
    #       attribute, and provide access to it via a `@property`. Then, the
    #       child classes must add a `weight` `InitVar` field with a default
    #       value after their other fields, and use the `__post_init__` to set
    #       `_weight`. This looks something like:
    #
    #           @dataclass
    #           class NewLevel(Level):
    #               ...
    #               weight: InitVar[int] = 1
    #
    #               def __post_init__(self, ..., weight: int):
    #                   ...
    #                   self._weight = weight
    #                   ...
    _weight: int = field(init=False)

    def __new__(cls, *_, **__):
        if cls == Level:
            raise ValueError(f"Cannot directly instantiate {cls.__name__}.")
        return super().__new__(cls)

    def __post_init__(self):
        # NOTE: This conversion exists for backwards compatibility.
        if not isinstance(self.name, str):
            self.name = str(self.name)
        # TODO: Using random integers seems insecure. Perhaps use UUIDs or a
        #       global (module-level) incremented counter.
        # TODO: Alternatively, because this is only used for the `__eq__`
        #       implementation, we could potentially remove this altogether and
        #       simply switch to using `is` checks (which is a more secure way
        #       of doing the same thing). The downside there is that this
        #       requires users of SweetPea to understand the distinction
        #       between `==` and `is`, which adds a bit of a barrier for an
        #       audience that is not primarily made of programmers.
        self.internal_name = self.name + f"{randint(0, 99999):05d}"

    def __hash__(self) -> int:
        return hash(self.internal_name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.internal_name == other.internal_name

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.name}>"

    @property
    def weight(self) -> int:
        """The level's weight."""
        return self._weight

    # TODO: REMOVE. (backwards compatibility)
    @property
    def external_name(self) -> str:
        """An alias for :attr:`.Level.name`.

        .. deprecated:: 0.1.0

            This property will be removed in favor of :attr:`.Level.name`.
        """
        return self.name


@dataclass(eq=False)
class SimpleLevel(Level):
    """A simple :class:`.Level`, which only has a name.

    For example, in a simple :ref:`Stroop experiment
    <guide_factorial_example>`, a ``color`` :class:`.Factor` may consist of a
    few simple levels such as ``red``, ``blue``, and ``green``.

    :param name:
        The name of the level.
    """

    weight: InitVar[int] = 1

    # NOTE: The __post_init__ method is a special case where we can ignore the
    #       Liskov substitution property. This is addressed in
    #       python/mypy#9254:
    #           https://github.com/python/mypy/issues/9254
    def __post_init__(self, weight: int):  # type: ignore # pylint: disable=arguments-differ
        super().__post_init__()
        self._weight = weight


@dataclass(eq=False)
class DerivedLevel(Level):
    """A :class:`.Level` representing the intersection of other levels,
    potentially from different :class:`Factors <.Factor>`. These are produced
    through use of :class:`DerivationWindows <.DerivationWindow>`, which are
    constraints on level selection during trial sampling.

    For more information on when to use derived levels, consult :ref:`the
    Derivations section of the SweetPea guide <guide_factorial_derivations>`.

    :param name:
        The name of the level.

    :param window:
        A :class:`.DerivationWindow` used in producing a cross product of this
        level.
    """

    #: The derivation window corresponding to this level.
    window: DerivationWindow = field(compare=False)

    weight: InitVar[int] = 1

    # NOTE: The __post_init__ method is a special case where we can ignore the
    #       Liskov substitution property. This is addressed in
    #       python/mypy#9254:
    #           https://github.com/python/mypy/issues/9254
    def __post_init__(self, weight: int):  # type: ignore # pylint: disable=arguments-differ
        super().__post_init__()
        # NOTE: This check is for backwards compatibility. It should instead be
        #       handled by type-checking.
        if not isinstance(self.window, DerivationWindow):
            raise TypeError(f"DerivedLevel must be given a DerivationWindow; got {type(self.window).__name__}.")
        self._weight = weight
        # Verify internal factors' strides.
        for factor in self.window.factors:
            if (isinstance(factor, DerivedFactor)
                and factor.has_complex_window
                and factor.levels[0].window.stride > 1):
                raise ValueError(f"{type(self).__name__} does not accept factors with stride > 1, but factor "
                                 f"{factor.name} has window with stride {factor.first_level.window.stride}.")
        # Expand the factors. Each factor gets duplicated according to the
        # derivation window width.
        # TODO: Why is `DerivedLevel` manipulating the internal state of
        #       `DerivationWindow`? This should probably be moved to a
        #       `DerivationWindow` method.
        # TODO: This could probably be handled a different way, too.
        # FIXME: Okay, this is becoming a nuisance.
        #        In the original code, this expansion modifies the
        #        `window.args` --- but it does not modify the `window.argc`
        #        that was set on object initialization. This `window.argc`
        #        value is then used in `DerivationProcessor.shift_window`. This
        #        means that we need to preserve the *initial* count of factors
        #        when we expand the factor list.
        #            The takeaway is that this is an awful way to handle this,
        #        because we are clearly not meant to be *actually* expanding
        #        the factors. We need a less confusing --- and more
        #        semantically consistent --- way of managing this information.
        expanded_factors: List[Factor] = []
        for factor in self.window.factors:
            expanded_factors.extend([factor] * self.window.width)
        self.window.factors = expanded_factors

    def get_dependent_cross_product(self) -> List[Tuple[Level, ...]]:
        """Produces a list of n-tuples, where each tuple represents a unique
        combination of :class:`.Level` selections among all possibilities.

        For instance, if we have two :class:`Factors <.Factor>`, each with some
        :class:`Levels <.Level>`:

        ======  ================
        Factor  Levels
        ======  ================
        color   red, blue, green
        value   1, 2
        ======  ================

        Then the following list of tuples is returned::

          [(red, 1),
           (red, 2),
           (blue, 1),
           (blue, 2),
           (green, 1),
           (green, 2)]

        .. tip::

            You can access a :class:`.Level`'s corresponding :class:`.Factor`
            via the :attr:`.Level.factor` attribute.

        :rtype: typing.List[typing.Tuple[.Level, ...]]
        """
        return list(product(*(factor.levels for factor in self.window.factors)))


@dataclass(eq=False)
class ElseLevel(Level):
    # TODO: I'm honestly not sure what this kind of level is for, semantically.
    """A :class:`.Level` for... something.

    :param name:
        The name of the level.
    """

    weight: InitVar[int] = 1

    # NOTE: The __post_init__ method is a special case where we can ignore the
    #       Liskov substitution property. This is addressed in
    #       python/mypy#9254:
    #           https://github.com/python/mypy/issues/9254
    def __post_init__(self, weight: int):  # type: ignore # pylint: disable=arguments-differ
        super().__post_init__()
        self._weight = weight

    def derive_level_from_levels(self, other_levels: List[DerivedLevel]) -> DerivedLevel:
        """Converts the :class:`.ElseLevel` into a :class:`.DerivedLevel` by
        combining it with other specified
        :class:`DerivedLevels <.DerivedLevel>`.

        :param other_levels:
            A list of :class:`DerivedLevels <.DerivedLevel>` for use in
            constructing the new level.
        """
        if not other_levels:
            return DerivedLevel(self.name, WithinTrialDerivationWindow(lambda: False, []))
        first_level = other_levels[0]
        # TODO: This is very odd. We only take every *n*th factor from the
        #       derivation window (where *n* is the window's width). This is
        #       because the initializer for `DerivedLevel`s expands the list of
        #       factors to duplicate by the width.
        #           It seems like this should be rethought. Why go through the
        #       trouble of duplicating the factors only to de-duplicate them
        #       later? Perhaps `DerivedLevel`s need a different internal
        #       representation to avoid this real duplication.
        factors = first_level.window.factors[::first_level.window.width]
        # TODO: This exhibits the same issue as the preceding TODO.
        window = DerivationWindow(lambda *args: not any(map(lambda l: l.window.predicate(*args), other_levels)),
                                  factors,
                                  first_level.window.width,
                                  first_level.window.stride)
        return DerivedLevel(self.name, window)


###############################################################################
##
## Factors
##


@dataclass
class Factor:
    """An independent variable in a factorial experiment. Factors are composed
    of :class:`Levels <.Level>` and come in two flavors:

    - :class:`.SimpleFactor`
    - :class:`.DerivedFactor`

    However, both classes can be implicitly constructed by the base
    :class:`.Factor` constructor, so we recommend you always use that for
    creating factors.

    During :class:`.Factor` construction, the first :class:`.Level` in the
    :attr:`~.Factor.initial_levels` is dynamically type-checked. If it's a
    :class:`.DerivedLevel` or :class:`.ElseLevel`, a `.DerivedFactor` will be
    initialized. Otherwise, a `.SimpleFactor` will be initialized.

    In all cases, the :attr:`~.Factor.initial_levels` will be processed. This
    step ensures that all of a factor's :attr:`~.Factor.levels` will always be
    :class:`Levels <.Level>`. The levels are processed according to these
    rules:

    1. A :class:`.Level` instance is left alone.

    2. A :class:`str` instance is converted into a :class:`.SimpleLevel`.

    3. A :class:`tuple` or :class:`list` consisting of exactly one :class:`str`
       followed by one :class:`int` will be converted into a
       :class:`.SimpleLevel` with the :class:`str` as its name and the
       :class:`int` as its weight.

    4. Anything else is converted into a :class:`.SimpleLevel` by using its
       string representation as a level name.

    .. note::

        The :class:`.DerivedFactor` subclass does additional processing after
        these steps.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor. The list can be made of anything,
        but any values in the list that are not instances of :class:`.Level` or
        one of its subclasses will be converted into :class:`.SimpleLevel`
        instances by using their string representation, as determined by
        ``SimpleLevel(str(value))``.
    :type initial_levels: typing.Sequence[Any]

    :rtype: .Factor

    .. tip::

        See :ref:`the Factorial Experiment Design section of the SweetPea guide
        <guide_factorial_design>` for more about factors, levels, and how to
        use them.
    """

    #: The name of this factor.
    name: str

    #: The levels used during factor initialization.
    initial_levels: InitVar[Sequence[Any]]

    #: The discrete values that this factor can have.
    levels: Sequence[Level] = field(init=False)

    #: A mapping from level names to levels for constant-time lookup.
    _level_map: Dict[str, Level] = field(init=False, default_factory=dict)

    def __new__(cls, name: str, initial_levels: Sequence[Any], *_, **__) -> Factor:
        # Ensure we got a string for a name. This requirement is imposed for
        # backwards compatibility, but it should be handled by type-checking.
        if not isinstance(name, str):
            raise ValueError(f"Factor name not a string: {name}.")
        # Check if we're initializing this from `Factor` directly or one of its
        # subclasses.
        if cls != Factor:
            # It's a subclass, so we do nothing special.
            return super().__new__(cls)
        # Otherwise, we have to check whether to return a subclass instance.
        # This requires there to be at least 1 initial level.
        if not initial_levels:
            raise ValueError(f"Expected at least one level for factor {name}.")
        first_level = initial_levels[0]
        if isinstance(first_level, (DerivedLevel, ElseLevel)):
            instance = super().__new__(DerivedFactor)
        else:
            instance = super().__new__(SimpleFactor)
        return instance

    def __post_init__(self, initial_levels: Sequence[Any]):
        # First, we convert the given initial levels into actual `Level`s. To
        # ensure the input list is untouched, we copy any levels that came in.
        real_levels: List[Level] = []
        for level in initial_levels:
            if isinstance(level, Level):
                pass
            elif isinstance(level, str):
                level = SimpleLevel(level)
            elif (isinstance(level, (tuple, list))
                  and len(level) == 2
                  and isinstance(level[0], str)
                  and isinstance(level[1], int)):
                for i in range(level[1]):
                    current_level = SimpleLevel(level[0], level[1])
                    real_levels.append(current_level)
                continue
            else:
                level = SimpleLevel(str(level))
            real_levels.append(level)
        # Then we do any necessary post-processing of the levels.
        self.levels = self._process_initial_levels(real_levels)
        # Lastly, ensure all the levels have distinct names. We also use this
        # step to initialize the internal level map, which allows for constant-
        # time lookup of levels by name.
        for level in self.levels:
            level.factor = self
            # This used to have the following error inside of the if statement:
            #   raise ValueError(f"Factor {self.name} instantiated with
            #                   duplicate level {level.name}.")
            # This error prevented any levels from sharing the same name. It
            # was removed with the the goal of adding weights to factors. The
            # dictionary only seems to need access to one of the copies of
            # a level because they are all the same. 
            if level.name in self._level_map:
                continue
            self._level_map[level.name] = level

    # NOTE: Subclasses of `Factor` must override this method!
    # NOTE: This method cannot be decorated `@abstractmethod` because the
    #       `abc.ABC` class does not play well with `@dataclass`. Additionally,
    #       `Factor` is not actually an abstract base class because the custom
    #       `__new__` implementation prevents it from ever being instantiated.
    #       There is no way to express "a class which cannot be instantiated"
    #       that I know of, so there's no way to get around this dynamic
    #       `NotImplementedError` solution.
    def _process_initial_levels(self, initial_levels: Sequence[Level]) -> Sequence[Level]:
        raise NotImplementedError

    def __deepcopy__(self, memo: Dict):
        cls = self.__class__
        new_instance = cls.__new__(cls, self.name, [])
        memo[id(self)] = new_instance
        for attr, val in self.__dict__.items():
            setattr(new_instance, attr, deepcopy(val, memo))
        return new_instance

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.name == other.name and self.levels == other.levels

    def __str__(self) -> str:
        levels_string = '[' + ', '.join(map(str, self.levels)) + ']'
        return f"{type(self).__name__}<{self.name} | {levels_string}>"

    def __hash__(self) -> int:
        return hash(self.name)

    def __getitem__(self, name: str) -> Level:
        value = self.get_level(name)
        if value is None:
            raise KeyError(f"Factor {self.name} has no level named {name}.")
        return value

    def __contains__(self, name: str) -> bool:
        return name in self._level_map

    def get_level(self, name: str) -> Optional[Level]:
        """Returns a :class:`.Level` instance corresponding to the given name,
        if it exists within this factor. Otherwise, returns ``None``.
        """
        return self._level_map.get(name)

    # TODO: This should be made private.
    @property
    def first_level(self) -> Level:
        """The first :class:`.Level` in this factor."""
        return self.levels[0]

    # TODO: Convert to a property. (backwards compatibility)
    # NOTE: Alternatively, we should maybe instead prefer an actual type check
    #       in most spots in the code since that will give accurate type
    #       checking feedback.
    def is_derived(self) -> bool:
        """Whether this factor is derived.

        .. deprecated:: 0.1.0

            Instead of using this function, we recommend doing a dynamic type
            check with :func:`isinstance`. This provides the same semantic
            information to the programmer while also providing greater type
            guarantees when using a static type checker, such as mypy.

            .. code-block:: python

                factor: Factor = ...
                if isinstance(factor, DerivedFactor):
                    # Code requiring a derived factor.
                    ...
                else:
                    # Code if it's not a derived factor.
                    ...
        """
        return isinstance(self, DerivedFactor)

    @property
    def has_complex_window(self) -> bool:
        """Whether this factor has a complex derivation window.

        A complex derivation window is a window  of derived factors whose
        first-level derivations are themselves considered complex.
        """
        if not isinstance(self, DerivedFactor):
            return False
        window = self.first_level.window
        return (window.width > 1
                or window.stride > 1
                or window.is_complex)

    def applies_to_trial(self, trial_number: int) -> bool:
        """Whether this factor applies to the given trial. For example, factors
        with :class:`.TransitionDerivation` derivations in their levels do not
        apply to trial number ``1``, but do apply to all subsequent trials.

        .. tip::

            Trials start their numbering at ``1``.
        """
        if trial_number <= 0:
            raise ValueError(f"Trial numbers must be 1 or greater; got {trial_number}.")
        if not isinstance(self, DerivedFactor):
            return True

        def acc_width(d: DerivationWindow) -> int:
            if isinstance(d.first_factor, DerivedFactor) and d.first_factor.has_complex_window:
                return d.width + acc_width(d.first_factor.first_level.window) - 1
            return d.width

        window = self.first_level.window
        return (trial_number >= acc_width(window)
                and (trial_number - window.width) % window.stride == 0)

    # TODO: REMOVE. (backwards compatibility)
    @property
    def factor_name(self) -> str:
        """An alias for :attr:`.Factor.name` for backwards compatibility.

        .. deprecated:: 0.1.0

            This property will be removed in favor of :attr:`.Factor.name`.
        """
        return self.name

    # TODO: REMOVE. (backwards compatibility)
    def has_level(self, name: str) -> bool:
        """Whether the given level name corresponds to a level in this factor.

        .. deprecated:: 0.1.0

            This method will be removed in favor of straightforward membership
            checks, such as:

            .. code-block:: python

                factor: Factor = ...
                if 'level_name' in factor:
                    ...
        """
        return name in self


@dataclass
class SimpleFactor(Factor):
    """A :class:`.Factor` comprised of :class:`SimpleLevels <.SimpleLevel>`. If
    a subclass of :class:`.Level` is passed in that is not a
    :class:`SimpleLevel`, an error is raised during initialization.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor.
    :type initial_levels: typing.Sequence[.SimpleLevel]

    :rtype: .SimpleFactor
    """

    levels: Sequence[SimpleLevel] = field(init=False)

    def _process_initial_levels(self, initial_levels) -> Sequence[SimpleLevel]:
        for level in initial_levels:
            if not isinstance(level, SimpleLevel):
                raise ValueError(f"{type(self).__name__} named {self.name} must contain only SimpleLevels, but level "
                                 f"{level.name} has type {type(level).__name__}.")
        return initial_levels

    # NOTE: Pylint incorrectly labels this as a "useless super delegation"
    #       because it is unaware that dataclasses do not automatically inherit
    #       __hash__, __eq__, etc in certain cases. This is addressed in
    #       PyCQA/pylint#3934:
    #           https://github.com/PyCQA/pylint/issues/3934
    def __hash__(self) -> int:  # pylint: disable=useless-super-delegation
        return super().__hash__()

    # NOTE: See note on `SimpleFactor.__hash__`.
    def __eq__(self, other) -> bool:  # pylint: disable=useless-super-delegation
        return super().__eq__(other)

    def get_level(self, name: str) -> Optional[SimpleLevel]:
        return cast(Optional[SimpleLevel], super().get_level(name))

    @property
    def first_level(self) -> SimpleLevel:
        return cast(SimpleLevel, self.levels[0])


@dataclass
class DerivedFactor(Factor):
    """A :class:`.Factor` composed of :class:`DerivedLevels <.DerivedLevel>`.

    After doing the level processing described by :class:`.Factor`, an
    additional step is taken: all :class:`ElseLevels <.ElseLevel>` are
    converted into :class:`DerivedLevels <.DerivedLevel>`. This is done by
    calling :func:`.ElseLevel.derive_level_from_levels`, supplying all the
    natural :class:`DerivedLevels <.DerivedLevel>` that were passed in.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor. The levels may be instances of
        either :class:`DerivedLevels <.DerivedLevel>` or
        :class:`ElseLevels <.ElseLevel>`.

        .. note::

            Any given :class:`.ElseLevel` will be converted to a
            :class:`.DerivedLevel` by way of
            :func:`.ElseLevel.derive_level_from_levels`, so that the
            :attr:`.Factor.levels` list will only contain
            :class:`DerivedLevels <DerivedLevel>`.
    :type initial_levels: typing.Sequence[typing.Union[.DerivedLevel, .ElseLevel]]

    :rtype: .DerivedFactor
    """

    levels: Sequence[DerivedLevel] = field(init=False)

    def _process_initial_levels(self, initial_levels: Sequence[Level]) -> Sequence[DerivedLevel]:
        # First, we construct the list of `DerivedLevel`s.
        adjusted_levels: List[DerivedLevel] = []
        initial_derived_levels: List[DerivedLevel] = [level for level in initial_levels
                                                      if isinstance(level, DerivedLevel)]
        for level in initial_levels:
            if isinstance(level, ElseLevel):
                adjusted_levels.append(level.derive_level_from_levels(initial_derived_levels))
            elif isinstance(level, DerivedLevel):
                adjusted_levels.append(level)
            else:
                raise ValueError(f"Cannot use {type(level).__name__} to create a {type(self).__name__}. "
                                 f"Only DerivedLevels and ElseLevels are allowed.")
        # Then, we do some validation.
        expected_size = adjusted_levels[0].window.size
        for level in adjusted_levels[1:]:
            if level.window.size != expected_size:
                raise ValueError(f"Expected all DerivedLevels' derivations in factor {self.name} to have size "
                                 f"{expected_size}, but level {level.name} has a derivation window of size "
                                 f"{level.window.size}.")
        expected_factors = adjusted_levels[0].window.factors
        for level in adjusted_levels[1:]:
            if level.window.factors != expected_factors:
                raise ValueError(f"Expected all DerivedLevels' derivations in factor {self.name} to use factors "
                                 f"{expected_factors}, but level {level.name}'s derivation window uses factors "
                                 f"{level.window.factors}.")
        return adjusted_levels

    # NOTE: See note on `SimpleFactor.__hash__`.
    def __hash__(self) -> int:  # pylint: disable=useless-super-delegation
        return super().__hash__()

    # NOTE: See note on `SimpleFactor.__hash__`.
    def __eq__(self, other) -> bool:  # pylint: disable=useless-super-delegation
        return super().__eq__(other)

    def get_level(self, name: str) -> Optional[DerivedLevel]:
        return cast(Optional[DerivedLevel], super().get_level(name))

    @property
    def first_level(self) -> DerivedLevel:
        return cast(DerivedLevel, self.levels[0])


###############################################################################
##
## Derivation Windows
##


@dataclass
class DerivationWindow:
    """A mechanism to specify the window of a derivation. Derivation windows
    are used to inform a derivation based on levels from other factors in the
    current trial and, potentially, multiple preceding trials.

    For detailed information, see the SweetPea guide's :ref:`section on
    derivation <guide_factorial_derivations>`.

    :param predicate:
        A predicate function used during derivation. Different derivation
        windows require different forms of predicates.

        .. warning::

            The type of arguments passed to the ``predicate`` varies by
            Derivation subclass. Read their documentation carefully!
    :type predicate: typing.Callable[[Any, ....], bool]

    :param factors:
        The factors upon which this derivation window depends.
    :type factors: typing.Sequence[.Factor]

    :param width:
        The number of trials that this derivation window depends upon. The
        current trial must be included, so the number must be greater than or
        equal to ``1``.
    :type width: int

    :param stride:
        TODO DOC
    :type stride: int
    """

    # TODO: I think that, if possible, this should be changed to some other
    #       managed data structure (like an enum that correlates cases to
    #       predicates). That seems like it would be more robust and also
    #       provide an easier API for users of SweetPea.
    # TODO: Alternatively, we could just make this class-private and provide a
    #       method that takes the arguments and returns the result.
    #: The predicate used during derivation with this window.
    predicate: Callable

    #: The factors upon which this derivation depends.
    factors: List[Factor]

    # TODO: Rename this to something more clear.
    #: The width of this window.
    width: int

    #: The stride of this window.
    stride: int

    #: The number of factors that originally came in, disregarding any
    #: expansion caused by a :class:`.DerivedLevel` changing things.
    initial_factor_count: int = field(init=False)

    def __post_init__(self):
        # NOTE: We check the types for backwards compatibility, but it should
        #       be handled with type-checking.
        if not callable(self.predicate):
            raise TypeError(f"DerivationWindow expected predicate function; got {self.predicate}.")
        for factor in self.factors:
            if not isinstance(factor, Factor):
                raise TypeError(f"DerivationWindow must be composed of Factors; got {factor}.")
        # TODO: Validate the predicate accepts the same number of arguments as
        #       factors in `self.factors`.
        if self.width < 1:
            raise ValueError(f"A {type(self).__name__} derivation window must have a width of at least 1.")
        if self.stride < 1:
            raise ValueError(f"A {type(self).__name__} derivation window must have a stride of at least 1.")
        found_factor_names = set()
        for factor in self.factors:
            if factor.name in found_factor_names:
                raise ValueError(f"Derivations do not accept repeated factors. Factor repeated: {factor.name}.")
            found_factor_names.add(factor.name)
        self.initial_factor_count = len(self.factors)

    @property
    def size(self) -> Tuple[int, int]:
        """The width and stride of this derivation window as a pair.

        :rtype: typing.Tuple[int, int]
        """
        return (self.width, self.stride)

    @property
    def first_factor(self) -> Factor:
        """The first :class:`.Factor` in the internal list of Factors.

        :rtype: .Factor
        """
        return self.factors[0]

    @property
    def is_complex(self) -> bool:
        """Whether this derivation window is considered *complex*. A complex
        derivation windowis one for which at least one of the following is
        true:

        - The window's :attr:`.width` is greater than ``1``.
        - The window's :attr:`.stride` is greater than ``1``.
        - The window's :attr:`.first_factor` is a complex derived factor.

        :rtype: bool
        """
        return (self.width > 1
                or self.stride > 1
                or self.first_factor.has_complex_window)

    # TODO: REMOVE. (backwards compatibility)
    @property
    def args(self) -> List[Factor]:
        """An alias for :attr:`.DerivationWindow.factors`.

        :rtype: typing.List[.Factor]

        .. deprecated:: 0.1.0

            This property will be removed in favor of
            :attr:`.DerivationWindow.factors`.
        """
        return self.factors

    # TODO: REMOVE. (backwards compatibility)
    @property
    def fn(self) -> Callable:
        """An alias for :attr:`.DerivationWindow.predicate`.

        :rtype: Callable

        .. deprecated:: 0.1.0

            This property will be removed in favor of
            :attr:`.DerivationWindow.predicate`.
        """
        return self.predicate


@dataclass
class WithinTrialDerivationWindow(DerivationWindow):
    """A derivation window that depends on levels from other factors, all
    within the same trial.

    :param predicate:
        A predicate that takes as many :class:`strs <str>` as factors in this
        derivation window, where each :class:`str` will be the name of a
        factor.
    :type predicate: typing.Callable[[str, ....], bool]

    :param factors:
        The factors upon which this derivation window depends.
    :type factors: typing.Sequence[.Factor]
    """

    width: int = field(default=1, init=False)
    stride: int = field(default=1, init=False)


@dataclass
class TransitionDerivationWindow(DerivationWindow):
    """A derivation window that depends on levels from other factors in the
    current trial and the immediately preceding trial.
    :class:`TransitionDerivations <.TransitionDerivation>` are used to
    constrain the transition points between trials.

    :param predicate:
        A predicate that takes as many lists of factors as factors in this
        derivation window.
    :type predicate: typing.Callable[[typing.Sequence[.Factor], ....], bool]

    :param factors:
        The factors upon which this derivation window depends.
    :type factors: typing.Sequence[.Factor]

    """

    width: int = field(default=2, init=False)
    stride: int = field(default=1, init=False)


###############################################################################
##
## Backwards Compatibility
##
## These functions are provided to maintain compatibility with the existing
## SweetPea implementation.
##
## TODO: Rewrite SweetPea's internal implementation in order to remove these!


def get_external_level_name(level: Level) -> str:
    """Returns :attr:`.Level.name`.

    .. deprecated:: 0.1.0

        This function will be removed in favor of :attr:`.Level.name`.
    """
    return level.name


# TODO: This shouldn't be used in any other module anyway. Uses of this
#       function should instead do `==` comparison of levels.
def get_internal_level_name(level: Level) -> str:
    """Returns :attr:`.Level.internal_name`.

    .. deprecated:: 0.1.0

        This function will be removed. It should not be used outside of this
        module.
    """
    return level.internal_name


#### Class aliases.

#: An alias for :class:`.WithinTrialDerivationWindow`.
#:
#: .. deprecated:: 0.1.0
#:
#:     This class will be removed in favor of
#:     :class:`.WithinTrialDerivationWindow`.
WithinTrial = WithinTrialDerivationWindow

#: An alias for :class:`.TransitionDerivationWindow`.
#:
#: .. deprecated:: 0.1.0
#:
#:     This class will be removed in favor of
#:     :class:`.TransitionDerivationWindow`.
Transition = TransitionDerivationWindow

#: An alias for :class:`.DerivationWindow`.
#:
#: .. deprecated:: 0.1.0
#:
#:     This class will be removed in favor of
#:     :class:`.DerivationWindow`.
Window = DerivationWindow


#### Noun-form function aliases.

def simple_level(name: str, weight: Optional[int] = None) -> SimpleLevel:
    """A function alias for :class:`.SimpleLevel`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.SimpleLevel`.

    :param name:
        The name of the level.

    :param weight:
        An optional weight for the level.
    """
    if weight is None:
        return SimpleLevel(name)
    return SimpleLevel(name, weight)


def derived_level(name: str, derivation: Window, weight: Optional[int] = None) -> DerivedLevel:
    """A function alias for :class:`.DerivedLevel`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.DerivedLevel`.

    :param name:
        The name of the level.

    :param derivation:
        The derivation window for this level.

    :param weight:
        An optional weight for the level.
    """
    if weight is None:
        return DerivedLevel(name, derivation)
    return DerivedLevel(name, derivation, weight)


def else_level(name: str, weight: Optional[int] = None) -> ElseLevel:
    """A function alias for :class:`.ElseLevel`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.ElseLevel`.

    :param name:
        The name of the level.

    :param weight:
        An optional weight for the level.
    """
    if weight is None:
        return ElseLevel(name)
    return ElseLevel(name, weight)


def factor(name: str, levels: Sequence[Any]) -> Factor:
    """A function alias for :class:`.Factor`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.Factor`.

    :param name:
        The name of the factor.

    :param levels:
        A sequence of levels for the factor.
    """
    return Factor(name, levels)


def within_trial(fn: Callable, args: List[Factor]) -> WithinTrialDerivationWindow:
    """A function alias for :class:`.WithinTrialDerivationWindow`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.WithinTrialDerivationWindow`.

    :param fn:
        A predicate function. See :class:`.WithinTrialDerivationWindow`.

    :param args:
        A list of :class:`Factors <.Factor>`. See
        :class:`.WithinTrialDerivationWindow`.
    """
    return WithinTrialDerivationWindow(fn, args)


def transition(fn: Callable, args: List[Factor]) -> TransitionDerivationWindow:
    """A function alias for :class:`.TransitionDerivationWindow`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.TransitionDerivationWindow`.

    :param fn:
        A predicate function. See :class:`.TransitionDerivationWindow`.

    :param args:
        A list of :class:`Factors <.Factor>`. See
        :class:`.TransitionDerivationWindow`.
    """
    return TransitionDerivationWindow(fn, args)


def window(fn: Callable, args: List[Factor], width: int, stride: int) -> DerivationWindow:
    """A function alias for :class:`.DerivationWindow`.

    .. deprecated:: 0.1.2

        This function will be removed in favor of direct instantiation of
        :class:`.DerivationWindow`.

    :param fn:
        A predicate function. See :class:`.DerivationWindow`.

    :param args:
        A list of :class:`Factors <.Factor>`. See
        :class:`.DerivationWindow`.

    :param width:
        The width of the window.

    :param stride:
        The stride of the window.
    """
    return DerivationWindow(fn, args, width, stride)
