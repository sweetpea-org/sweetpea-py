# Everything in `__all_` is exported from the `sweetpea` module.

__all__ = [
    'synthesize_trials',

    'print_experiments', 'tabulate_experiments', 
    'save_experiments_csv', 'experiments_to_tuples',

    'Block', 'CrossBlock', 'MultiCrossBlock',
    
    'Factor', 'Level', 'DerivedLevel', 'ElseLevel',

    'Derivation', 'WithinTrial', 'Transition', 'Window',

    'Constraint',
    'Exclude', 'Pin', 'MinimumTrials', 'ExactlyK',
    'AtMostKInARow', 'AtLeastKInARow',
    'ExactlyKInARow',

    'Gen', 'RandomGen', 'IterateSATGen', 
    'CMSGen', 'UniGen', 'IterateILPGen',
    'UniformGen', 'IterateGen'
]

from functools import reduce
from typing import Dict, List, Optional, Tuple, Any, Union, cast
from itertools import product
import csv

from sweetpea._internal.block import Block
from sweetpea._internal.cross_block import MultiCrossBlock, CrossBlock
from sweetpea._internal.primitive import (
    Factor, SimpleFactor, DerivedFactor, Level, SimpleLevel, DerivedLevel, ElseLevel,
    Window, WithinTrial, Transition,
    HiddenName
)
from sweetpea._internal.constraint import (
    Consistency, Constraint, Derivation,
    Exclude, Pin, MinimumTrials,
    ExactlyK, AtMostKInARow, AtLeastKInARow, ExactlyKInARow
)
from sweetpea._internal.sampling_strategy.base import Gen
from sweetpea._internal.sampling_strategy.uniform import UniformGen
from sweetpea._internal.sampling_strategy.iterate import IterateGen
from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
from sweetpea._internal.sampling_strategy.unigen import UniGen
from sweetpea._internal.sampling_strategy.cmsgen import CMSGen
from sweetpea._internal.sampling_strategy.random import RandomGen
from sweetpea._internal.sampling_strategy.iterate_ilp import IterateILPGen
from sweetpea._internal.server import build_cnf
from sweetpea._internal.core.cnf import Var
from sweetpea._internal.argcheck import argcheck, make_islistof


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _experiments_to_tuples(experiments: List[dict],
                           keys: List[str]):
    """Converts a list of experiments into a list of lists of tuples, where
    each tuple represents a crossing in a given experiment.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to the synthesis function :func:`.synthesize_trials`.

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
        calls to synthesis function :func:`.synthesize_trials`.
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
        a call to :func:`.synthesize_trials`.

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
        if (not isinstance(block, MultiCrossBlock)) or len(block.crossings) != 1:
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
        a call to :func:`.synthesize_trials`.

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

def save_experiments_csv(block: Block,
                         experiments: List[dict],
                         file_prefix: str = "experiment"):
    return _experiments_to_csv(experiments, [cast(str, f.name) for f in __filter_hidden(block.design)], file_prefix)

def synthesize_trials(block: Block,
                      samples: int = 10,
                      sampling_strategy = IterateGen
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
        :class:`.NonUniformGen`.

    :returns:
        A :class:`list` of trial sets. Each set is represented as a
        :class:`dictionary <dict>` mapping each factor name to a list of
        levels, where each such list contains to one level per trial.
    """
    def starting(who: Any) -> None:
        nonlocal samples
        print(f"Sampling {samples} trial sequences using {who}.")
    if isinstance(sampling_strategy, type):
        assert issubclass(sampling_strategy, Gen)
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
