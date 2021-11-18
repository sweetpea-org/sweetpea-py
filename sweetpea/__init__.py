"""The :mod:`sweetpea` module provides the SweetPea domain-specific programming
language. :ref:`The SweetPea language <home>` allows for the specification of
randomized experimental designs and the synthesis of trial sequences from those
designs.
"""

from functools import reduce
from typing import Dict, List, Optional, Tuple, cast
from itertools import product

from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.logic import to_cnf_tseitin
from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.primitives import (
    Factor, SimpleLevel, DerivedLevel,
    DerivationWindow, WithinTrialDerivationWindow, TransitionDerivationWindow,
    get_external_level_name)
from sweetpea.constraints import (
    Consistency, Constraint, Derivation, FullyCross, MultipleCross, MultipleCrossBlock,
    at_most_k_in_a_row, at_least_k_in_a_row, exactly_k, exactly_k_in_a_row, exclude, minimum_trials)
from sweetpea.sampling_strategies.non_uniform import NonUniformSamplingStrategy
from sweetpea.sampling_strategies.unigen import UnigenSamplingStrategy
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy
from sweetpea.server import build_cnf
import csv


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def fully_cross_block(design: List[Factor],
                      crossing: List[Factor],
                      constraints: List[Constraint],
                      require_complete_crossing=True,
                      cnf_fn=to_cnf_tseitin) -> Block:
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

    :param cnf_fn:
        A CNF conversion function. Default is :func:`.to_cnf_tseitin`.
    """
    all_constraints = cast(List[Constraint], [FullyCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints) #expand the constraints into a form we can process.
    block = FullyCrossBlock(design, [crossing], all_constraints, require_complete_crossing, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    if not constraints and not list(filter(lambda f: f.is_derived(), crossing)) and not list(filter(lambda f: f.has_complex_window, design)):
        block.complex_factors_or_constraints = False
    return block


def multiple_cross_block(design: List[Factor],
                         crossings: List[List[Factor]],
                         constraints: List[Constraint],
                         require_complete_crossing=True,
                         cnf_fn=to_cnf_tseitin) -> Block:
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
        Whether every combination in ``crossings`` must appear in a block of
        trials. ``True`` by default. A ``False`` value is appropriate if
        combinations are excluded through an :class:`.Exclude`
        :class:`.Constraint.`

    :param cnf_fn:
        A CNF conversion function. Default is :func:`.to_cnf_tseitin`.
    """
    all_constraints = cast(List[Constraint], [MultipleCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints) #expand the constraints into a form we can process.
    block = MultipleCrossBlock(design, crossings, all_constraints, require_complete_crossing, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    return block


def __desugar_constraints(constraints: List[Constraint]) -> List[Constraint]:
    desugared_constraints = []
    for c in constraints:
        desugared_constraints.extend(c.desugar())
    return desugared_constraints


def simplify_experiments(experiments: List[Dict]) -> List[List[Tuple[str, ...]]]:
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
        tuple_lists.append(list(zip(*experiment.values())))
    return tuple_lists


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
    nested_assignment_strs = [list(map(lambda l: f.factor_name + " " + get_external_level_name(l), f.levels)) for f in block.design]
    column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

    print('{} trial sequences found.'.format(len(experiments)))
    for idx, e in enumerate(experiments):
        print('Experiment {}:'.format(idx))
        strs = [list(map(lambda v: name + " " + v, values)) for (name,values) in e.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


# TODO: Finish the documentation of this function.
def tabulate_experiments(experiments: List[Dict],
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
        An optional :class:`list` of :class:`Factors <.Factor>`...

        .. todo::

            Finish specification of this parameter.

    :param trials:
        An optional :class:`list` of :class:`ints <int>`...

        .. todo::

            Finish specification of this parameter.
    """
    if factors is None:
        factors = []

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
            tabulation[f.factor_name] = list()
            factor_levels: List[str] = list()
            for l in f.levels:
                factor_levels.append(l.external_name)
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
        nested_assignment_strs = [list(map(lambda l: f.factor_name + " " + get_external_level_name(l), f.levels)) for f
                                  in design]
        column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

        format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

        print('Experiment {}:'.format(exp_idx))
        strs = [list(map(lambda v: name + " " + v, values)) for (name, values) in tabulation.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


def experiment_to_csv(experiments: List[dict], file_prefix: str = "experiment"):
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
        csv_columns = list(dict.keys())
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
    print("Sampling {} trial sequences using the {}".format(samples, sampling_strategy))
    sampling_result = sampling_strategy.sample(block, samples)
    return sampling_result.samples


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
    return cnf.as_unigen_string()
