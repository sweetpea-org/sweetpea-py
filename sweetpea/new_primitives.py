"""This module provides the fundamental primitives used by the SweetPea
domain-specific language.
"""

# NOTE: This import allows forward references in type annotations.
from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from itertools import product
from random import randint
from typing import Callable, List, Sequence, Tuple, cast


__all__ = [
    'Level', 'SimpleLevel', 'DerivedLevel', 'ElseLevel',
    'Factor', 'SimpleFactor', 'DerivedFactor',
    'Derivation', 'WithinTrialDerivation', 'TransitionDerivation', 'WindowDerivation',
]


@dataclass
class Level:
    """A discrete value that a :class:`.Factor` can hold.

    Do not directly instantiate :class:`.Level`. Instead, construct one of the
    subclasses:

    - :class:`.SimpleLevel`
    - :class:`.DerivedLevel`
    - :class:`.ElseLevel`

    For more on levels, consult :ref:`the guide <guide_factorial_levels>`.
    """
    #: The name of the level.
    name: str
    _internal_name: str = field(init=False)

    def __new__(cls, *_, **__):
        if cls == Level:
            raise ValueError(f"Cannot directly instantiate {cls.__name__}.")
        return super().__new__(cls)

    def __post_init__(self):
        # TODO: Using random integers seems insecure. Perhaps use UUIDs or a
        #       global (module-level) incremented counter.
        # TODO: Alternatively, because this is only used for the `__eq__`
        #       implementation, we could potentially remove this altogether and
        #       simply switch to using `is` checks (which is a more secure way
        #       of doing the same thing). The downside there is that this
        #       requires users of SweetPea to understand the distinction
        #       between `==` and `is`, which adds a bit of a barrier for an
        #       audience that is not primarily made of programmers.
        self._internal_name = self.name + f"{randint(0, 99999):05d}"

    def __eq__(self, other) -> bool:
        # NOTE: We deliberately check type equality and not subtype relation.
        if type(other) != type(self):  # pylint: disable=unidiomatic-typecheck
            raise NotImplementedError
        return self._internal_name == other._internal_name

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.name}>"


@dataclass(eq=False)
class SimpleLevel(Level):
    """A simple :class:`.Level`, which only has a name.

    For example, in a simple :ref:`Stroop experiment
    <guide_factorial_example>`, a ``color`` :class:`.Factor` may consist of a
    few simple levels such as ``red``, ``blue``, and ``green``.

    :param name:
        The name of the level.
    """
    pass  # pylint: disable=unnecessary-pass


@dataclass(eq=False)
class DerivedLevel(Level):
    """A :class:`.Level` representing the intersection of other levels,
    potentially from different :class:`Factors <.Factor>`. These are produced
    through use of :class:`Derivations <.Derivation>`, which are constraints on
    level selection during trial sampling.

    For more information on when to use derived levels, consult :ref:`the
    Derivations section of the SweetPea guide <guide_factorial_derivations>`.

    :param name:
        The name of the level.

    :param derivation:
        A :class:`.Derivation` used in producing a cross product of this level
    """
    #: The derivation used to produce this level.
    derivation: Derivation = field(compare=False)

    def __post_init__(self):
        super().__post_init__()
        # Verify internal factors' strides.
        for factor in self.derivation.factors:
            if factor.has_complex_derivation and factor.first_level.derivation.stride > 1:
                raise ValueError(f"DerivedLevel does not accept factors with stride > 1. "
                                 f"Factor {factor.name} has derivation with stride "
                                 f"{factor.first_level.derivation.stride}.")
        # Expand the factors. Each factor gets duplicated according to the
        # derivation width.
        # TODO: Why is `DerivedLevel` manipulating the internal state of
        #       `Derivation`? This should probably be moved to a
        #       `Derivation` method.
        expanded_factors: List[Factor] = []
        for factor in self.derivation.factors:
            expanded_factors.extend([factor] * self.derivation.width)

    def get_dependent_cross_product(self) -> List[Tuple[Tuple[Factor, Level], ...]]:
        """Produces a list of n-tuples of pairs, where each pair consists of a
        :class:`.Factor` with one of its possible :class:`Levels <.Level>`, and
        each n-tuple represents a unique combination of such
        :class:`.Factor`-:class:`.Level` selections among all possibilities.

        For instance, if we have two :class:`Factors <.Factor>` each with some
        :class:`Levels <.Level>`:

        ======  ================
        Factor  Levels
        ======  ================
        color   red, blue, green
        value   1, 2
        ======  ================

        Then the following list of tuples of pairs is returned::

          [((color, red),   (value, 1)),
           ((color, red),   (value, 2)),
           ((color, blue),  (value, 1)),
           ((color, blue),  (value, 2)),
           ((color, green), (value, 1)),
           ((color, green), (value, 2))]

        :rtype: typing.List[typing.Tuple[typing.Tuple[.Factor, .Level], ...]]
        """
        # TODO: This seems like it could be rewritten with indexing of some
        #       sort. The levels are already inside the factors, so returning
        #       the factors paired with specific levels is redundant.
        #           On the other hand, it wouldn't really be more efficient and
        #       this may be considered more straightforward for users.
        factor_level_pairs = [[(factor, level) for level in factor.levels] for factor in self.derivation.factors]
        return list(product(*factor_level_pairs))


@dataclass(eq=False)
class ElseLevel(Level):
    # TODO: I'm honestly not sure what this kind of level is for, semantically.
    """A :class:`.Level` for... something.

    :param name:
        The name of the level.
    """

    def derive_level_from_levels(self, other_levels: List[DerivedLevel]) -> DerivedLevel:
        """Converts the :class:`.ElseLevel` into a :class:`.DerivedLevel` by
        combining it with other specified
        :class:`DerivedLevels <.DerivedLevel>`.

        :param other_levels:
            A list of :class:`DerivedLevels <.DerivedLevel>` for use in
            constructing the new level.
        """
        if not other_levels:
            return DerivedLevel(self.name, WithinTrialDerivation(lambda: False, []))
        first_level = other_levels[0]
        # TODO: This is very odd. We only take every *n*th factor from the
        #       derivation (where *n* is the derivation width). This is because
        #       the initializer for `DerivedLevel`s expands the list of factors
        #       to duplicate by the width.
        #           It seems like this should be rethought. Why go through the
        #       trouble of duplicating the factors only to de-duplicate them
        #       later? Perhaps `DerivedLevel`s need a different internal
        #       representation to avoid this real duplication.
        factors = first_level.derivation.factors[::first_level.derivation.width]
        # TODO: This exhibits the same issue as the preceding TODO.
        derivation = WindowDerivation(lambda *args: not any(map(lambda l: l.derivation.predicate(*args), other_levels)),
                                      factors,
                                      first_level.derivation.width,
                                      first_level.derivation.stride)
        return DerivedLevel(self.name, derivation)


@dataclass
class Factor:
    """An independent variable in a factorial experiment. Factors are composed
    of :class:`Levels <.Level>` and come in two flavors:
    :class:`SimpleFactors <.SimpleFactor>`, composed of only
    :class:`SimpleLevels <.SimpleLevel>`, and
    :class:`DerivedFactors <.DerivedFactor>`, composed of
    :class:`DerivedLevels <.DerivedLevel>` and
    :class:`ElseLevels <.ElseLevel>`. See :ref:`the Factorial Experiment Design
    section of the SweetPea guide <guide_factorial_design>` for more.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor.
    :type initial_levels: typing.Sequence[.Level]

    :rtype: .Factor
    """
    #: The name of the factor.
    name: str
    # The `initial_levels` list will be passed to the class's `__new__`. This
    # is then checked to determine what subclass to instantiate. Following
    # object instantiation, the subclass's `__init__` will be called with
    # `initial_levels` as an argument, and then the `__post_init__` will also
    # receive it.
    # NOTE: It is the responsibility of each subclass to implement a
    #       `__post_init__` method which takes `initial_levels` as an argument
    #       and then initializes the instance's `levels` field.
    initial_levels: InitVar[Sequence[Level]]
    #: The levels that comprise this factor.
    levels: Sequence[Level] = field(init=False)

    def __post_init__(self, initial_levels: Sequence[Level]):
        self.levels = initial_levels

    def __new__(cls, name: str, initial_levels: Sequence[Level]) -> Factor:
        # All factors must define levels.
        if not initial_levels:
            raise ValueError(f"Expected at least one level for factor {name}.")
        # We instantiate the factor based on the first level in the list.
        # NOTE: It is the responsibility of the subclasses to validate inputs.
        if isinstance(initial_levels[0], SimpleLevel):
            instance = super().__new__(SimpleFactor)
        elif isinstance(initial_levels[0], (DerivedLevel, ElseLevel)):
            instance = super().__new__(DerivedFactor)
        else:
            instance = super().__new__(Factor)
        return instance

    @property
    def first_level(self) -> Level:
        """The first level in :attr:`.levels`.

        :rtype: .Level
        """
        return self.levels[0]

    @property
    def has_complex_derivation(self) -> bool:
        """Determines whether this factor has a complex :class:`.Derivation`
        according to :func:`.Derivation.is_complex`.

        :rtype: bool
        """
        return False


@dataclass
class SimpleFactor(Factor):
    """A :class:`.Factor` comprised of :class:`SimpleLevels <.SimpleLevel>`.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor.
    :type initial_levels: typing.Sequence[.SimpleLevel]

    :rtype: .SimpleFactor
    """
    levels: Sequence[SimpleLevel] = field(init=False)

    def __post_init__(self, initial_levels: Sequence[Level]):
        for level in initial_levels:
            if not isinstance(level, SimpleLevel):
                raise ValueError(f"Cannot use {type(level).__name__} in factors made of SimpleLevels.")
        self.levels = cast(Sequence[SimpleLevel], initial_levels)

    @property
    def first_level(self) -> SimpleLevel:
        """The first level in :attr:`.levels`.

        :rtype: .SimpleLevel
        """
        return cast(SimpleLevel, super().first_level)


@dataclass
class DerivedFactor(Factor):
    """A :class:`.Factor` composed of :class:`DerivedLevels <.DerivedLevel>`.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor. The levels may be instances of
        either :class:`DerivedLevels <.DerivedLevel>` or
        :class:`ElseLevels <.ElseLevel>`.

        .. NOTE::
            Any given :class:`.ElseLevel` will be converted to a
            :class:`.DerivedLevel` by way of
            :func:`.ElseLevel.derive_level_from_levels`, so that the
            :attr:`.Factor.levels` list will only contain
            :class:`DerivedLevels <DerivedLevel>`.
    :type initial_levels: typing.Sequence[typing.Union[.DerivedLevel, .ElseLevel]]

    :rtype: .DerivedFactor
    """
    levels: Sequence[DerivedLevel] = field(init=False)

    def __post_init__(self, initial_levels: Sequence[Level]):
        adjusted_levels: List[DerivedLevel] = []
        # Only the `DerivedLevel`s are used in `ElseLevel` derivation.
        derived_levels: List[DerivedLevel] = [level for level in initial_levels
                                              if isinstance(level, DerivedLevel)]
        for level in initial_levels:
            if isinstance(level, ElseLevel):
                adjusted_levels.append(level.derive_level_from_levels(derived_levels))
            elif isinstance(level, DerivedLevel):
                adjusted_levels.append(level)
            else:
                raise ValueError(f"Cannot use {type(level).__name__} in factors made of DerivedLevels and ElseLevels.")
        self.levels = adjusted_levels

    @property
    def first_level(self) -> DerivedLevel:
        """The first level in :attr:`.levels`.

        :rtype: .DerivedLevel
        """
        return cast(DerivedLevel, super().first_level)

    @property
    def has_complex_derivation(self) -> bool:
        return self.first_level.derivation.is_complex


@dataclass
class Derivation:
    """A mechanism to specify the process of derivation. For detailed
    information, see :ref:`the SweetPea guide's section on derivations
    <guide_factorial_derivations>`.

    .. NOTE::
        The :class:`.Derivation` class cannot be directly instantiated. Use one
        of the subclasses instead.

    :param predicate:
        A predicate function used during derivation. Different derivation
        mechanisms require different forms of predicates.

        .. WARNING::
            The type of arguments passed to the ``predicate`` varies by
            Derivation subclass. Read their documentation carefully!
    :type predicate: typing.Callable[[Any, ....], bool]

    :param factors:
        The factors upon which this derivation depends.
    :type factors: typing.Sequence[.Factor]

    :param width:
        The number of trials that this derivation depends upon. The current
        trial must be included, so the number must be greater than or equal to
        ``1``.
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
    #: The predicate used for producing this derivation.
    predicate: Callable
    #: The factors upon which this derivation depends.
    factors: Sequence[Factor]
    # TODO: Rename this to something more clear.
    #: The width of this derivation.
    width: int
    #: The stride of this derivation.
    stride: int

    def __new__(cls, *_, **__):
        if cls == Derivation:
            raise NotImplementedError(f"Cannot directly instantiate {cls.__name__}.")
        return super().__new__(cls)

    def __post_init__(self):
        # TODO: Validate the predicate accepts the same number of arguments as
        #       factors in `self.factors`.
        if self.width < 1:
            raise ValueError(f"A {type(self).__name__} derivation must have a width of at least 1.")
        if self.stride < 1:
            raise ValueError(f"A {type(self).__name__} derivation must have a stride of at least 1.")
        found_factor_names = set()
        for factor in self.factors:
            if factor.name in found_factor_names:
                raise ValueError(f"Derivations do not accept repeated factors. Factor repeated: {factor.name}.")

    @property
    def size(self) -> Tuple[int, int]:
        """The width and stride of this derivation.

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
        """Whether this derivation is considered *complex*. A complex
        derivation is one for which at least one of the following is true:

        - The derivation's :attr:`.width` is greater than ``1``.
        - The derivation's :attr:`.stride` is greater than ``1``.
        - The derivation's :attr:`.first_factor` is a complex derived factor.

        :rtype: bool
        """
        return (self.width > 1
                or self.stride > 1
                or self.first_factor.has_complex_derivation)


@dataclass
class WithinTrialDerivation(Derivation):
    """A derivation that depends on levels from other factors, all within the
    same trial.

    :param predicate:
        A predicate that takes as many :class:`strs <str>` as factors in this
        derivation, where each :class:`str` will be the name of a factor.
    :type predicate: typing.Callable[[str, ....], bool]

    :param factors:
        The factors upon which this derivation depends.
    :type factors: typing.Sequence[.Factor]
    """

    width: int = field(default=1, init=False)
    stride: int = field(default=1, init=False)


@dataclass
class TransitionDerivation(Derivation):
    """A derivation that depends on levels from other factors in the current
    trial and the immediately preceding trial. :class:`TransitionDerivations
    <.TransitionDerivation>` are used to constrain the transition points
    between trials.

    :param predicate:
        A predicate that takes as many lists of factors as factors in this
        derivation.
    :type predicate: typing.Callable[[typing.Sequence[.Factor], ....], bool]

    :param factors:
        The factors upon which this derivation depends.
    :type factors: typing.Sequence[.Factor]
    """

    width: int = field(default=2, init=False)
    stride: int = field(default=1, init=False)


@dataclass
class WindowDerivation(Derivation):
    """A derivation that depends on levels from other factors in the current
    trial and multiple preceding trials.

    :param predicate:
        A predicate that takes as many lists of factors as factors in this
        derivation.
    :type predicate: typing.Callable[[typing.Sequence[.Factor], ....], bool]

    :param factors:
        The factors upon which this derivation depends.
    :type factors: typing.Sequence[.Factor]

    :param width:
        The number of trials that this derivation depends upon. The current
        trial must be included, so the number must be greater than or equal to
        ``1``.
    :type width: int

    :param stride:
        TODO DOC
    :type stride: int
    """
    pass  # pylint: disable=unnecessary-pass
