# NOTE: This import allows for forward references in type annotations.
from __future__ import annotations


__all__ = [
    'Level', 'SimpleLevel', 'DerivedLevel', 'ElseLevel',
    'Factor', 'SimpleFactor', 'DerivedFactor',
    'DerivationWindow', 'WithinTrialDerivationWindow', 'TransitionDerivationWindow',
    'WithinTrial', 'Transition', 'Window',
    'simple_level', 'derived_level', 'else_level', 'factor', 'within_trial', 'transition', 'window',
]


from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from itertools import product, chain
from random import randint
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast

from sweetpea.internal.iter import chunk_list
from sweetpea.internal.beforestart import BeforeStart


###############################################################################
##
## Levels
##


@dataclass
class Level:
    """A discrete value that a :class:`.Factor` can hold.

    For more on levels, consult :ref:`the guide <guide_factorial_levels>`.
    """

    #: The name of the level.
    name: str

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
    #                   self.weight = weight
    #                   ...
    _weight: int = field(init=False)

    _synthesized: bool = field(init=False)

    def __new__(cls, *_, **__):
        if cls == Level:
            return super().__new__(SimpleLevel)
        else:
            return super().__new__(cls)

    def __post_init__(self):
        self._synthesized = False

    def __str__(self) -> str:
        return f"Level<{self.name}>"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        # only equal when it's the same object:
        return id(self) == id(other)

    @property
    def weight(self) -> int:
        """The level's weight."""
        return self._weight

    def uses_factor(self, factor):
        return False

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
        self.weight = weight # type: ignore

    def __repr__(self) -> str:
        return self.__str__()

    def desugar_weight(self, replacements: dict):
        levels = [Level(self.name) for i in range(self.weight)]
        # Multiple levels with the same name only create trouble for constraints
        # that refer to levels. When we desugar, the generated levels will not
        # have been referenced by constraints (and any reference to the old level
        # is replaced to a reference to a derived level), so duplicates are ok:
        for l in levels:
            l._synthesized = True
        return levels

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
        self.weight = weight # type: ignore
        # Verify internal factors' strides.
        for factor in self.window.factors:
            if (isinstance(factor, DerivedFactor)
                and factor.has_complex_window
                and factor.levels[0].window.stride > 1):
                raise ValueError(f"{type(self).__name__} does not accept factors with stride > 1, but factor "
                                 f"{factor.name} has window with stride {factor.first_level.window.stride}.")
        # Depth helps order of filling in levels when derived factors depend
        # on other derived factors
        self._depth = max(map(lambda f: f._get_depth(), self.window.factors))

    def get_dependent_cross_product(self) -> List[Tuple[Level, ...]]:
        """Produces a list of n-tuples, where each tuple represents a unique
        combination of :class:`.Level` selections among all possibilities.
        If a the derived level's start implies that not enough values are
        ready, then a ``BeforeStart`` is included in the possibilities.

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
        def levels_of(factor, i):
            ready_at = 0
            if isinstance(factor, DerivedFactor) and factor.has_complex_window:
                ready_at = factor.first_level.window.start
            else:
                ready_at = 0
            if ready_at > self.window.start - self.window.width + i + 1:
                return factor.levels + [BeforeStart(ready_at)]
            else:
                return factor.levels
        return list(product(*(levels_of(factor, i) for factor in self.window.factors for i in range(self.window.width))))

    def uses_factor(self, f: Factor):
        return any(list(map(lambda wf: wf.uses_factor(f), self.window.factors)))

    def _trial_arguments(self, sample: dict, i :int) -> list:
        """Check whether trial i (zero-based) in the sample matches this level's predicate."""
        window = self.window
        args = []
        for f in window.factors:
            levels = sample[f]
            for j in range(window.width):
                idx = i-(window.width-1)+j
                if idx >= 0:
                    args.append(levels[idx].name)
                else:
                    args.append(None)
        if window.width > 1:
            args = list(chunk_list(args, window.width))
        return args

    def __repr__(self) -> str:
        return "Derived" + self.__str__()

    def desugar_for_weights(self, replacements: dict):
        l = DerivedLevel(self.name,
                         DerivationWindow(self.window.predicate,
                                          [replacements.get(f, [f, f])[0] for f in self.window.factors],
                                          self.window.width,
                                          self.window.stride,
                                          self.window.start))
        replacements[self] = l
        

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
        self.weight = weight # type: ignore

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
        window = DerivationWindow(lambda *args: not any(map(lambda l: l.window.predicate(*args), other_levels)),
                                  first_level.window.factors,
                                  first_level.window.width,
                                  first_level.window.stride,
                                  first_level.window.start)
        return DerivedLevel(self.name, window, self.weight)

###############################################################################
##
## Factors
##

class HiddenName:
    def __init__(self, name: str):
        self.name = name

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
    :class:`.DerivedLevel` or :class:`.ElseLevel`, a :class:`.DerivedFactor` will be
    initialized. Otherwise, a :class:`.SimpleFactor` will be initialized.

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

    4. Anything else is converted into a :class:`.SimpleLevel` by using it
       as a level name.

    .. note::

        The :class:`.DerivedFactor` subclass does additional processing after
        these steps.

    :param name:
        The name of this factor.

    :param initial_levels:
        The levels comprising this factor. The list can be made of anything,
        but any values in the list that are not instances of :class:`.Level` or
        one of its subclasses will be converted into :class:`.SimpleLevel`
        instances using ``SimpleLevel(value)``.
    :type initial_levels: typing.Sequence[Any]

    :rtype: .Factor

    .. tip::

        See :ref:`the Factorial Experiment Design section of the SweetPea guide
        <guide_factorial_design>` for more about factors, levels, and how to
        use them.
    """

    #: The name of this factor. A synthesized factor may be mutated to hide its name
    name: Union[str, HiddenName]

    #: The levels used during factor initialization.
    initial_levels: InitVar[Sequence[Any]]

    #: The discrete values that this factor can have.
    levels: Sequence[Level] = field(init=False)

    #: A mapping from level names to levels for constant-time lookup.
    _level_map: Dict[str, Level] = field(init=False, default_factory=dict)

    def __new__(cls, name: Union[str, HiddenName], initial_levels: Sequence[Any], *_, **__) -> Factor:
        # Ensure we got a string for a name. This requirement is imposed for
        # backwards compatibility, but it should be handled by type-checking.
        if not isinstance(name, (str, HiddenName)):
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
        # First, we convert the given initial levels into actual `Level`s.
        real_levels: List[Level] = []
        for level in initial_levels:
            if isinstance(level, Level):
                pass
            else:
                level = SimpleLevel(level)
            real_levels.append(level)
        # Then we do any necessary post-processing of the levels.
        self.levels = self._process_initial_levels(real_levels)
        for level in self.levels:
            if hasattr(level, "factor"):
                raise ValueError(f"Level already belongs to a factor: {level.name}")
            if level.name in self._level_map and not level._synthesized:
                raise ValueError(f"Multiple levels with the same name: {level.name}")
            self._level_map[level.name] = level
            level.factor = self

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
        # only equal when it's the same object:
        return id(self) == id(other)

    def __str__(self) -> str:
        # levels_string = '[' + ', '.join(map(str, self.levels)) + ']'
        # return f"Factor<{self.name} | {levels_string}>"
        return f"Factor<{self.name}>"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.name)

    def __getitem__(self, name) -> Level:
        value = self.get_level(name)
        if value is None:
            raise KeyError(f"Factor {self.name} has no level named {name}.")
        return value

    def __contains__(self, name) -> bool:
        return name in self.levels

    def get_level(self, name) -> Optional[Level]:
        """Returns a :class:`.Level` instance corresponding to the given name,
        if it exists within this factor. Otherwise, returns ``None``.
        """
        return self._level_map.get(name)

    # TODO: This should be made private.
    @property
    def first_level(self) -> Level:
        """The first :class:`.Level` in this factor."""
        return self.levels[0]

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
                or cast(int, window.start) > 0
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

        window = self.first_level.window
        return (trial_number >= (cast(int, window.start)+1)
                and (trial_number - (cast(int, window.start)+1)) % window.stride == 0)

    def uses_factor(self, f: Factor):
        return self == f

    def _get_depth(self):
        if not isinstance(self, DerivedFactor):
            return 0
        return max(map(lambda l: cast(DerivedLevel, l)._depth, self.levels))+1

    def level_weight_sum(self):
        return sum([l.weight for l in self.levels])

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

    def __repr__(self) -> str:
        return self.__str__()

    def get_level(self, name) -> Optional[SimpleLevel]:
        return cast(Optional[SimpleLevel], super().get_level(name))

    @property
    def first_level(self) -> SimpleLevel:
        return cast(SimpleLevel, self.levels[0])

    def desugar_weights(self, replacements: dict):
        levelss = [l.desugar_weight(replacements) for l in self.levels]
        flat_f = Factor(self.name, list(chain.from_iterable(levelss)))
        names = list(map(lambda name: (name, DerivedLevel(name, WithinTrial(lambda n: n == name, [flat_f]))),
                         [l.name for l in self.levels]))
        derived_levels = {name: derived_level for name, derived_level in names}
        for l in self.levels:
            replacements[l] = derived_levels[l.name]
        derived_f = DerivedFactor(HiddenName(cast(str, self.name)), list(derived_levels.values()))
        replacements[self] = [derived_f, flat_f]

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

    def __repr__(self) -> str:
        return self.__str__()

    def get_level(self, name) -> Optional[DerivedLevel]:
        return cast(Optional[DerivedLevel], super().get_level(name))

    @property
    def first_level(self) -> DerivedLevel:
        return cast(DerivedLevel, self.levels[0])

    def uses_factor(self, f: Factor):
        return (self == f) or any(list(map(lambda l: l.uses_factor(f), self.levels)))

    def select_level_for_sample(self, i: int, sample: dict) -> Any:
        """Get level name for trial i (zero-based) depending on
        values of other factors already in the sample."""
        args = self.levels[0]._trial_arguments(sample, i)
        for l in self.levels:
            if l.window.predicate(*args):
                return l
        raise RuntimeError("no matching trial found when filling in a sample")

    def desugar_for_weights(self, replacements: dict):
        if any([any([f in replacements for f in l.window.factors]) for l in self.levels]):
            for l in self.levels:
                l.desugar_for_weights(replacements)
            f = DerivedFactor(self.name, [replacements[l] for l in self.levels])
            replacements[self] = [f, f]

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
        How often the factor is derived. With a stride of ``1`` (the default),
        the factor is derived for every trial starting with initial one. For
        a larger stride, ``stride-1`` trials are skipped before the factor is
        derived again.
    :type stride: int

    :param start:
        The first trial where this derivation applies. By default, the starting
        trial is the first trial where the factors are all defined that this one
        depends on. If the starting trial is before that, then the predicate
        must be prepared to handle ``None`` as an argument level.
    :type start: int
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

    # The starting trial, if not automatic; 0-based
    start: Optional[int] = None

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

        default_start = self.width - 1
        for factor in self.factors:
            ready_at = 0
            if isinstance(factor, DerivedFactor) and factor.has_complex_window:
                ready_at = factor.first_level.window.start
            ready_at = ready_at + self.width - 1
            if ready_at > default_start:
                default_start = ready_at
        if (self.start == None):
            self.start = default_start
        elif self.start < 0:
            raise ValueError(f"A {type(self).__name__} derivation window must have a start of at least 0.")
        self.start_delta = self.start - default_start
        found_factor_names = set()
        for factor in self.factors:
            if factor.name in found_factor_names:
                raise ValueError(f"Derivations do not accept repeated factors. Factor repeated: {factor.name}.")
            found_factor_names.add(factor.name)

    @property
    def size(self) -> Tuple[int, int, int]:
        """The width and stride of this derivation window as a pair.

        :rtype: typing.Tuple[int, int, int]
        """
        return (self.width, self.stride, cast(int, self.start))

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
    start: Optional[int] = field(default=None, init=False)


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
    start: int = field(default=1, init=False)


###############################################################################
##
## Backwards Compatibility
##
## These functions are provided to maintain compatibility with the existing
## SweetPea implementation.
##
## TODO: Rewrite SweetPea's internal implementation in order to remove these!

#### Class aliases.

#: A preferred alias for :class:`.WithinTrialDerivationWindow`.
WithinTrial = WithinTrialDerivationWindow

#: A preferred alias for :class:`.TransitionDerivationWindow`.
Transition = TransitionDerivationWindow

#: A compatibility alias for :class:`.DerivationWindow`.
Window = DerivationWindow

#: A preferred alias for :class:`.DerivationWindow`.
AcrossTrials = Window

#### Noun-form function aliases.

def simple_level(name: str, weight: Optional[int] = None) -> SimpleLevel:
    """A compatibility alias for direct instantiation of :class:`.SimpleLevel`.

    :param name:
        The name of the level.

    :param weight:
        An optional weight for the level.

    """
    if weight is None:
        return SimpleLevel(name)
    return SimpleLevel(name, weight)


def derived_level(name: str, derivation: Window, weight: Optional[int] = None) -> DerivedLevel:
    """A compatibility alias for direct instantiation of :class:`.DerivedLevel`.

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
    """A compatibility alias for direct instantiation of
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
    """A compatibility alias for direct instantiation of :class:`.Factor`.

    :param name:
        The name of the factor.

    :param levels:
        A sequence of levels for the factor.

    """
    return Factor(name, levels)


def within_trial(fn: Callable, args: List[Factor]) -> WithinTrialDerivationWindow:
    """A compatibility alias for direct instantiation of
       :class:`.WithinTrialDerivationWindow`.

    :param fn:
        A predicate function. See :class:`.WithinTrialDerivationWindow`.

    :param args:
        A list of :class:`Factors <.Factor>`. See
        :class:`.WithinTrialDerivationWindow`.

    """
    return WithinTrialDerivationWindow(fn, args)


def transition(fn: Callable, args: List[Factor]) -> TransitionDerivationWindow:
    """A compatibility alias for direct instantiation of
       :class:`.TransitionDerivationWindow`.

    :param fn:
        A predicate function. See :class:`.TransitionDerivationWindow`.

    :param args:
        A list of :class:`Factors <.Factor>`. See
        :class:`.TransitionDerivationWindow`.

    """
    return TransitionDerivationWindow(fn, args)


def window(fn: Callable, args: List[Factor], width: int, stride: int, start: int = None) -> DerivationWindow:
    """A compatibility alias for direct instantiation of
       :class:`.AcrossTrials`.

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
    return DerivationWindow(fn, args, width, stride, start)
