"""The :mod:`sweetpea` module provides the SweetPea domain-specific programming
language. :ref:`The SweetPea language <home>` allows for the specification of
randomized experimental designs and the synthesis of trial sequences from those
designs.
"""


__all__ = [
    'synthesize_trials',

    'print_experiments', 'tabulate_experiments', 
    'save_experiments_csv', 'experiments_to_tuples',

    'Block', 'CrossBlock', 'MultiCrossBlock',
    
    'Factor', 'Level', 'DerivedLevel', 'ElseLevel',

    'Derivation', 'WithinTrial', 'Transition', 'AcrossTrials',

    'Constraint',
    'Exclude', 'Pin', 'MinimumTrials', 'ExactlyK',
    'AtMostKInARow', 'AtLeastKInARow',
    'ExactlyKInARow',

    'Gen', 'RandomGen', 'IterateGen', 
    'CMSGen', 'UniGen',

    # --------------------------------------------------
    # For backward compatibility:

    'Window', 'SimpleLevel', 'DerivationWindow', 'WithinTrialDerivationWindow', 'TransitionDerivationWindow',

    'at_most_k_in_a_row', 'at_least_k_in_a_row', 'exactly_k', 'exactly_k_in_a_row', 'exclude', 'minimum_trials',

    'fully_cross_block', 'multiple_cross_block',
    'simplify_experiments', 'experiment_to_csv', 'save_cnf',
    'synthesize_trials_uniform', 'synthesize_trials_non_uniform',

    'NonUniformSamplingStrategy', 'UniformCombinatoricSamplingStrategy', 'UnigenSamplingStrategy'
]


from functools import reduce
from typing import Dict, List, Optional, Tuple, Any, Union, cast
from itertools import product, chain
import csv

from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.logic import to_cnf_tseitin
from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.blocks import CrossBlock as CrossBlock_class
from sweetpea.primitives import (
    Factor, SimpleFactor, DerivedFactor, Level, SimpleLevel, DerivedLevel, ElseLevel,
    DerivationWindow, WithinTrialDerivationWindow, TransitionDerivationWindow,
    Window, WithinTrial, Transition, AcrossTrials,
    HiddenName
)
from sweetpea.constraints import (
    Consistency, Constraint, Derivation, FullyCross, MultipleCross, MultipleCrossBlock,
    Exclude, Pin, MinimumTrials, ExactlyK, AtMostKInARow, AtLeastKInARow, ExactlyKInARow,
    at_most_k_in_a_row, at_least_k_in_a_row, exactly_k, exactly_k_in_a_row, exclude, minimum_trials
)
from sweetpea.sampling_strategies.base import SamplingStrategy, Gen
from sweetpea.sampling_strategies.non_uniform import NonUniformSamplingStrategy, IterateGen
from sweetpea.sampling_strategies.unigen import UnigenSamplingStrategy, UniGen
from sweetpea.sampling_strategies.cmsgen import CMSGenSamplingStrategy, CMSGen
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy, RandomGen
from sweetpea.server import build_cnf
from sweetpea.core.cnf import Var
from sweetpea.internal.argcheck import argcheck, make_islistof


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def CrossBlock(design: List[Factor],
               crossing: List[Factor],
               constraints: List[Constraint],
               require_complete_crossing: bool = True) -> Block:
    """Returns a fully crossed :class:`.Block` meant to be used in experiment
    synthesis. This is the preferred mechanism for describing an experiment.

    :param design:
        A :class:`list` of all the :class:`Factors <.Factor>` in the design.
        When a sequence of trials is generated, each trial will have one level
        from each factor in ``design``.

    :param crossing:
        A :class:`list` of :class:`Factors <.Factor>` used to produce
        crossings. The number of trials in each run of the experiment is
        determined as the product of the number of levels of factors in
        ``crossing``.

        If ``require_complete_crossing`` is ``False``, the ``constraints`` can
        reduce the total number of trials.

        Different trial sequences of the experiment will have different
        combinations of levels in different orders. The factors in ``crossing``
        supply an implicit constraint that every combination of levels in the
        cross should appear once. Derived factors impose additional
        constraints: only combinations of levels that are consistent with
        derivations can appear as a trial. Additional constraints can be
        manually imposed via the ``constraints`` parameter.

    :param constraints:
        A :class:`list` of :class:`Constraints <.Constraint>` that restrict the
        generated trials.

    :param require_complete_crossing:
        Whether every combination in ``crossing`` must appear in a block of
        trials. ``True`` by default. A ``False`` value is appropriate if
        combinations are excluded through an :class:`.Exclude`
        :class:`.Constraint`.
    """
    who = "CrossBlock"
    argcheck(who, design, make_islistof(Factor), "list of Factors for design")
    argcheck(who, crossing, make_islistof(Factor), "list of Factors for crossing")
    argcheck(who, constraints, make_islistof(Constraint), "list of Constraints for constraints")
    design,crossings,replacements = __desugar_factors_with_weights(design, [crossing])
    all_constraints = cast(List[Constraint], [FullyCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints, replacements) #expand the constraints into a form we can process.
    block = FullyCrossBlock(design, crossings, all_constraints, require_complete_crossing, who=who)
    block.constraints += DerivationProcessor.generate_derivations(block)
    if (not list(filter(lambda c: c.is_complex_for_combinatoric(), constraints))
          and not list(filter(lambda f: f.has_complex_window, design))):
        block.complex_factors_or_constraints = False
    return block

def fully_cross_block(design: List[Factor],
                      crossing: List[Factor],
                      constraints: List[Constraint],
                      require_complete_crossing=True) -> Block:
    return CrossBlock(design, crossing, constraints, require_complete_crossing)

def multiple_cross_block(design: List[Factor],
                         crossings: List[List[Factor]],
                         constraints: List[Constraint],
                         require_complete_crossing: bool = True) -> Block:
    return MultiCrossBlock(design, crossings, constraints, require_complete_crossing)

def MultiCrossBlock(design: List[Factor],
                    crossings: List[List[Factor]],
                    constraints: List[Constraint],
                    require_complete_crossing: bool = True) -> Block:
    """Returns a :class:`.Block` with multiple crossings, meant to be used in
    experiment synthesis. Similar to :func:`fully_cross_block`, except it can
    be configured with multiple crossings.

    :param design:
        A :class:`list` of all the :class:`Factors <.Factor>` in the design.
        When a sequence of trials is generated, each trial will have one level
        from each factor in ``design``.

    :param crossings:
        A :class:`list` of :class:`lists <list>` of :class:`Factors <.Factor>`
        representing crossings. The number of trials in each run of the
        experiment is determined by the *maximum* product among the number of
        levels in the crossings.

        Every combination of levels in each individual crossing in
        ``crossings`` appears at least once. Different crossings can refer to
        the same factors, which constrains how factor levels are chosen across
        crossings.

    :param constraints:
        A :class:`list` of :class:`Constraints <.Constraint>` that restrict the
        generated trials.

    :param require_complete_crossing:
        Whether every combination in ``crossing`` must appear in a block of
        trials. ``True`` by default. A ``False`` value is appropriate if
        combinations are excluded through an :class:`.Exclude`
        :class:`.Constraint`.
    """
    who = "MultiCrossBlock"
    argcheck(who, design, make_islistof(Factor), "list of Factors for design")
    argcheck(who, crossings, make_islistof(make_islistof(Factor)), "list of list of Factors for crossings")
    argcheck(who, constraints, make_islistof(Constraint), "list of Constraints for constraints")
    design,crossings,replacements = __desugar_factors_with_weights(design, crossings)
    all_constraints = cast(List[Constraint], [MultipleCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints, replacements) #expand the constraints into a form we can process.
    block = MultipleCrossBlock(design, crossings, all_constraints, require_complete_crossing, who="MultiCrossBlock")
    block.constraints += DerivationProcessor.generate_derivations(block)
    return block

def __desugar_factors_with_weights(design: List[Factor], crossings: List[List[Factor]]) -> Tuple[List[Factor], List[List[Factor]], dict]:
    # When a derived factor has weighted levels and is in the
    # crossing, then the weight have to be handed by sampling, because
    # it doesn't work to have multiple levels in a derived factor that
    # match the same cases. If a derived factor is not in the
    # crossing, the weights are irrelevnt, because other factors
    # chosen for a combination determine a derived level.
    #
    # For a non-derived factor, weighting is effecively the same as
    # having multiple levels with the same name. Still, as long as a
    # factor with weights is used in the crossing (all of them, in the
    # case of multiple crossings), then we leave the weights in place
    # and handling them in sampling.
    #
    # But when a non-derived factor with weights is not in (all of
    # the) crossing(s), we desugar to a factor with multiple levels
    # that have the same name. That makes the biasing effect of
    # weighting work for formula-based samplers, and it geneally means
    # that samplers do not have to handle the weights specifically.
    #
    # To desugar, we create new factors and levels, and we rewrite all
    # constraints and derived factors to refer to the new ones. Each
    # desugared factor has two replacements: a non-derived factors
    # with the weights turned into multiple levels, and a derived
    # factor that has the same level names as before. The derived
    # factor is needed in case a constraint refers to an weighted
    # level that gets expanded in the non-derived factor.
    #
    # The `replacements` dictionary maps a level to its replacement,
    # and it maps factor to a list of two factors: the derived
    # replacement and non-derived replacement.
    #
    weighted = []
    for f in design:
        if (not isinstance(f, DerivedFactor)) and any([l.weight > 1 for l in f.levels]):
            if all([not f in c for c in crossings]):
                weighted.append(f)
    if not weighted:
        # No desugaring needed
        return (design, crossings, {})
    else:
        # Desugaring needed
        replacements = cast(dict, {})
        for f in weighted:
            # Adds to `replacements`:
            cast(SimpleFactor, f).desugar_weights(replacements)
        for f in design:
            if isinstance(f, DerivedFactor):
                # Uses `replacements`:
                f.desugar_for_weights(replacements)
        # Returned `replacements` is also used for constraint desugaring
        return (list(chain.from_iterable([replacements.get(f, [f]) for f in design])),
                [[replacements.get(f, [f, f])[1] for f in c] for c in crossings],
                replacements)

def __desugar_constraints(constraints: List[Constraint], replacements: dict) -> List[Constraint]:
    desugared_constraints = []
    for c in constraints:
        desugared_constraints.extend(c.desugar(replacements))
    return desugared_constraints


def _experiments_to_tuples(experiments: List[dict],
                           keys: List[str]):
    """Converts a list of experiments into a list of lists of tuples, where
    each tuple represents a crossing in a given experiment.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to any of the synthesis functions (:func:`.synthesize_trials`,
        :func:`.synthesize_trials_non_uniform`, or
        :func:`.synthesize_trials_uniform`).

    :returns:
        A list of lists of tuples of strings, where each sub-list corresponds
        to one of the ``experiments``, each tuple corresponds to a particular
        crossing, and each string is the simple surface name of a level.
    """
    tuple_lists: List[List[Tuple[str, ...]]] = []
    for experiment in experiments:
        tuple_lists.append(list(zip(*[experiment[key] for key in keys])))
    return tuple_lists

def simplify_experiments(experiments: List[Dict]) -> List[List[Tuple[str, ...]]]:
    return _experiments_to_tuples(experiments, list(experiments[0].keys()))

def experiments_to_tuples(block: Block,
                          experiments: List[dict]):
    return _experiments_to_tuples(experiments, [cast(str, f.name) for f in __filter_hidden(block.design)])

def __filter_hidden(design: List[Factor]) -> List[Factor]:
    return list(filter(lambda f: not isinstance(f.name, HiddenName), design))

def __filter_hidden_keys(d: dict) -> dict:
    return {name: d[name] for name in filter(lambda name: not isinstance(name, HiddenName), d.keys())}

def print_experiments(block: Block, experiments: List[dict]):
    """Displays the generated experiments in a human-friendly form.

    :param block:
        An experimental description as a :class:`.Block`.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to any of the synthesis functions (:func:`.synthesize_trials`,
        :func:`.synthesize_trials_non_uniform`, or
        :func:`.synthesize_trials_uniform`).
    """
    nested_assignment_strs = [list(map(lambda l: cast(str, f.name) + " " + str(l.name), f.levels)) for f in __filter_hidden(block.design)]
    column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

    print('\n{} trial sequences found.\n'.format(len(experiments)))
    for idx, e in enumerate(experiments):
        print('Experiment {}:'.format(idx))
        strs = [list(map(lambda v: name + " " + str(v), values)) for (name,values) in e.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))

def tabulate_experiments(block: Block = None,
                         experiments: List[Dict] = None,
                         factors: Optional[List[Factor]] = None,
                         trials: Optional[List[int]] = None):
    """Tabulates and prints the given experiments in a human-friendly form.
    Outputs a table that shows the absolute and relative frequencies of
    combinations of factor levels.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to any of the synthesis functions (:func:`.synthesize_trials`,
        :func:`.synthesize_trials_non_uniform`, or
        :func:`.synthesize_trials_uniform`).

    :param factors:
        An optional, though practically needed :class:`list` of :class:`Factors <.Factor>`.
        This list selects the factors of interest that are subsets of
        the design factors. More precisely, the names of these factors
        must be a subset of the design factor's names. (Given that :func:`.syntheseize_trials`
        reports results in terms of factor and level names, the design's factor and
        level objects no longer matter).

    :param trials:
        An optional :class:`list` of :class:`ints <int>` that specifies the indices of trials to
        be tabulated with the same indices being applied for every sequence. The paramater's
        default is to include all trials in the tabulation.
    """
    if factors is None and block is None:
        raise RuntimeError("tabulate_experiments: expected a `block` or `factors` argument")

    if factors is None:
        if (not isinstance(block, CrossBlock_class)) or len(block.crossings) != 1:
            raise RuntimeError("tabulate_experiments: expected block with one crossing")
        factors = block.crossings[0]

    if experiments is None:
        raise RuntimeError("tabulate_experiments: need experiments")

    for exp_idx, e in enumerate(experiments):
        tabulation: Dict[str, List[str]] = dict()
        frequency_list = list()
        proportion_list = list()
        levels: List[List[str]] = list()

        if trials is None:
            trials = list(range(0, len(e[list(e.keys())[0]])))

        num_trials = len(trials)

        # initialize table
        for f in factors:
            tabulation[cast(str, f.name)] = list()
            factor_levels: List[str] = list()
            for l in f.levels:
                factor_levels.append(l.name)
            levels.append(factor_levels)

        max_combinations = 0
        # Each `element` is an n-tuple (s1, s2, ..., sn) where n is the number
        # of levels and each element is a level name.
        for element in product(*levels):
            max_combinations += 1

            # add factor combination
            for idx, factor_name in enumerate(tabulation.keys()):
                tabulation[factor_name].append(element[idx])

            # compute frequency
            frequency = 0
            for trial in trials:
                valid_condition = True
                for idx, factor in enumerate(tabulation.keys()):
                    if e[factor][trial] != element[idx]:
                        valid_condition = False
                        break
                if valid_condition:
                    frequency += 1

            proportion = frequency / num_trials

            frequency_list.append(str(frequency))
            proportion_list.append(str(proportion*100) + '%')

        tabulation["frequency"] = frequency_list
        tabulation["proportion"] = proportion_list

        frequency_factor = Factor("frequency", list(set(frequency_list)))
        proportion_factor = Factor("proportion", list(set(proportion_list)))

        design = list()
        for f in factors:
            design.append(f)
        design.append(frequency_factor)
        design.append(proportion_factor)

        # print tabulation
        nested_assignment_strs = [list(map(lambda l: cast(str, f.name) + " " + l.name, f.levels)) for f
                                  in design]
        column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

        format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

        print('Experiment {}:'.format(exp_idx))
        strs = [list(map(lambda v: name + " " + v, values)) for (name, values) in tabulation.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


def _experiments_to_csv(experiments: List[dict],
                        csv_columns: List[str],
                        file_prefix: str = "experiment"):
    """Exports a list of experiments to CSV files. Each experiment will be
    saved to a separate ``.csv`` file.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to any of the synthesis functions (:func:`.synthesize_trials`,
        :func:`.synthesize_trials_non_uniform`, or
        :func:`.synthesize_trials_uniform`).

    :param file_prefix:
        A prefix to attach to each output ``.csv`` file.
    """
    for idx, experiment in enumerate(experiments):

        dict = experiment
        num_rows = len(dict[csv_columns[0]])

        csv_file = file_prefix + "_" + str(idx) + ".csv"
        try:
            with open(csv_file, 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(csv_columns)
                for row_idx in range(num_rows):
                    row = list()
                    for column in csv_columns:
                        row.append(dict[column][row_idx])
                    writer.writerow(row)
        except IOError:
            print("I/O error")

# For backward compatibility:
def experiment_to_csv(experiments: List[dict], file_prefix: str = "experiment"):
    return _experiments_to_csv(experiments, list(experiments[0].keys()), file_prefix)

def save_experiments_csv(block: Block,
                         experiments: List[dict],
                         file_prefix: str = "experiment"):
    return _experiments_to_csv(experiments, [cast(str, f.name) for f in __filter_hidden(block.design)], file_prefix)

def synthesize_trials_non_uniform(block: Block, samples: int) -> List[dict]:
    """Synthesizes experimental trials with non-uniform sampling. See
    :func:`.synthesize_trials` for more information.

    .. note::

        This function is built to circumvent some shortcomings in the Unigen
        solving engine. Specifically, it works by taking the following steps:

            #. Find a solution to the given formula.
            #. Add that solution to the formula to exclude the solution in
               subsequent attempts.
            #. Repeat as needed.

        This is not an ideal method of handling this problem, so it should be
        replaced at some point if we find a better way around Unigen's
        limitations.

    :param block:
        An experimental description as a :class:`.Block`.

    :param samples:
        The number of trial sets to generate.

    :returns:
        A :class:`list` of trial sets. Each set is represented as a
        :class:`dictionary <dict>` mapping each factor name to a list of
        levels, where each such list contains to one level per trial.
    """
    if block.complex_factors_or_constraints:
        return synthesize_trials(block, samples, sampling_strategy=NonUniformSamplingStrategy)
    else:
        return synthesize_trials(block, samples, sampling_strategy=UniformCombinatoricSamplingStrategy)


def synthesize_trials_uniform(block: Block, samples: int) -> List[dict]:
    """Synthesizes experimental trials with uniform sampling. See
    :func:`.synthesize_trials` for more information.

    :param block:
        An experimental description as a :class:`.Block`.

    :param samples:
        The number of trial sets to generate.

    :returns:
        A :class:`list` of trial sets. Each set is represented as a
        :class:`dictionary <dict>` mapping each factor name to a list of
        levels, where each such list contains to one level per trial.
    """
    if block.complex_factors_or_constraints:
        return synthesize_trials(block, samples, sampling_strategy=UnigenSamplingStrategy)
    else:
        return synthesize_trials(block, samples, sampling_strategy=UniformCombinatoricSamplingStrategy)


def synthesize_trials(block: Block,
                      samples: int = 10,
                      sampling_strategy = NonUniformSamplingStrategy
                      ) -> List[dict]:
    """Given an experiment described with a :class:`.Block`, randomly generates
    multiple sets of trials for that experiment.

    The number of trials in each set is determined by the experiment's
    crossing. Each trial is a combination of levels, subject to constraints
    imposed both implicitly and explicitly in the experimental description.

    This function should be used on the :class:`.Block` produced by either
    :func:`.fully_cross_block` or :func:`.multiple_cross_block`. Using that
    :class:`.Block`, :func:`.synthesize_trials` will produce a single cohesive
    CNF formula that will be solved with Unigen. The result of this solution is
    then decoded into something that is both human-readable and compatible with
    `PsyNeuLink <https://princetonuniversity.github.io/PsyNeuLink/>`_.

    .. warning::

        Effective uniform sampling is a work in progress, so straightforward
        use of this function may result in non-termination. If this happens,
        you can try to get some initial results via
        :func:`.synthesize_trials_non_uniform`.

    :param block:
        An experimental description as a :class:`.Block`.

    :param samples:
        The number of trial sets to generate. For example, a value of ``1``
        produces a :class:`list` of length ``1``, which contains a single set
        of trials with a random ordering of the crossings that satisfies the
        given constraints.

        Default is ``10``.

    :param sampling_strategy:
        The strategy to use for trial generation. The default is
        :class:`.NonUniformSamplingStrategy`.

    :returns:
        A :class:`list` of trial sets. Each set is represented as a
        :class:`dictionary <dict>` mapping each factor name to a list of
        levels, where each such list contains to one level per trial.
    """
    def starting(who: Any) -> None:
        nonlocal samples
        print(f"Sampling {samples} trial sequences using {who}.")
    if isinstance(sampling_strategy, type):
        assert issubclass(sampling_strategy, SamplingStrategy)
        starting(sampling_strategy.class_name())
        sampling_result = sampling_strategy.sample(block, samples)
    else:
        starting(sampling_strategy)
        sampling_result = sampling_strategy.sample_object(block, samples)

    return list(map(lambda e: __filter_hidden_keys(block.add_implied_levels(e)), sampling_result.samples))


# TODO: This function isn't called anywhere, so it should be removed.
def save_cnf(block: Block, filename: str):
    """Generates a CNF formula from a :class:`.Block` and then writes that CNF
    formula to the indicated file in the Unigen-specific DIMACS format.

    :param block:
        A description of a CNF formula as a :class:`.Block`.

    :param filename:
        The name of the file to write the CNF formula to.
    """
    cnf_str = __generate_cnf(block)
    with open(filename, 'w') as f:
        f.write(cnf_str)


# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO: This should be a method in Block.
def __generate_cnf(block: Block) -> str:
    """Converts a :class:`.Block` into a CNF formula and renders that CNF
    formula in the Unigen-specific DIMACS format.

    :param block:
        A description of a CNF formula as a :class:`.Block`.

    :returns:
        The given :class:`.Block` rendered as a Unigen-specific
        DIMACS-formatted string.
    """
    cnf = build_cnf(block)
    return cnf.as_unigen_string(sampled_variables = [Var(n) for n in block.support_variables()])
