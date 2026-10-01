# Everything in `__all_` is exported from the `sweetpea` module.

__all__ = [
    'synthesize_trials', 'sample_mismatch_experiment',

    'auto_correlation_scores_sample_within', 'auto_correlation_scores_samples_between',

    'print_experiments', 'tabulate_experiments',
    'save_experiments_csv', 'experiments_to_tuples', 'experiments_to_dicts',

    'Block', 'CrossBlock', 'MultiCrossBlock', 
    'Repeat', 'Nest', 'Merge',
    'RepeatMode', 'AlignmentMode',

    'Factor', 'Level', 'DerivedLevel', 'ElseLevel', 'ContinuousFactor',

    'Derivation', 'WithinTrial', 'Transition', 'Window', 'ContinuousFactorWindow',

    'Constraint', 
    'Exclude', 'Pin', 'MinimumTrials', 'ExactlyK',
    'Relax',
    'AtMostKInARow', 'AtLeastKInARow',
    'ExactlyKInARow',
    'LatinSquare',
    'Sequential',
    'CoverAllCombinations',

    'Gen', 'RandomGen', 'IterateSATGen',
    'CMSGen', 'UniGen', 'IterateILPGen',
    'UniformGen', 'IterateGen',
    'SMGen',

    'UniformDistribution', 'GaussianDistribution', 
    'ExponentialDistribution', 'LogNormalDistribution', 'CustomDistribution'
]

from functools import reduce
from typing import Dict, List, Optional, Tuple, Any, Union, cast
from itertools import product
import csv, os
import time

from sweetpea._internal.block import Block
from sweetpea._internal.cross_block import (
    MultiCrossBlockRepeat, MultiCrossBlock, CrossBlock, RepeatMode, AlignmentMode,
    Repeat, Nest, Merge
)
from sweetpea._internal.primitive import (
    Factor, SimpleFactor, DerivedFactor, ContinuousFactor, Level, SimpleLevel, DerivedLevel, ElseLevel,
    Window, WithinTrial, Transition, ContinuousFactorWindow,
    HiddenName
)
from sweetpea._internal.constraint import (
    Consistency, Constraint, Derivation,
    Exclude, Pin, MinimumTrials,
    ExactlyK, AtMostKInARow, AtLeastKInARow, ExactlyKInARow,
    Relax,
    LatinSquare,
    Sequential,
    CoverAllCombinations,
    solver_relaxable, relax_budget, record_concessions
)
from sweetpea._internal.core import SolveOutcome
from sweetpea._internal.sampling_strategy.base import Gen
from sweetpea._internal.sampling_strategy.uniform import UniformGen
from sweetpea._internal.sampling_strategy.iterate import IterateGen
from sweetpea._internal.sampling_strategy.iterate_sat import IterateSATGen
from sweetpea._internal.sampling_strategy.unigen import UniGen
from sweetpea._internal.sampling_strategy.cmsgen import CMSGen
from sweetpea._internal.sampling_strategy.random import RandomGen
from sweetpea._internal.sampling_strategy.smgen import SMGen
from sweetpea._internal.sampling_strategy.iterate_ilp import IterateILPGen
from sweetpea._internal.server import build_cnf
from sweetpea._internal.core.cnf import Var
from sweetpea._internal.argcheck import argcheck, make_islistof

from sweetpea._internal.distribution import (
    UniformDistribution, GaussianDistribution, 
    ExponentialDistribution, LogNormalDistribution, CustomDistribution
)


from sweetpea._internal.auto_correlation_score import (auto_correlation_score_factor_within,
                                                       auto_correlation_score_factor_between)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _experiments_to_tuples(experiments: List[dict],
                           keys: List[str]):
    tuple_lists: List[List[Tuple[Any, ...]]] = []
    for experiment in experiments:
        tuple_lists.append(list(zip(*[experiment[key] for key in keys])))
    return tuple_lists

def _experiments_to_dicts(experiments: List[dict],
                           keys: List[str]):
    tuple_lists: List[List[Dict[str, Any]]] = []
    for experiment in experiments:
        tuple_lists.append([dict(zip(keys, values)) for values in zip(*[experiment[key] for key in keys])])
    return tuple_lists

def simplify_experiments(experiments: List[dict]) -> List[List[tuple]]:
    """Like experiments_to_tuples, but without a block argument
    (for backward compatibility), so the factor names are inferred from the
    experiments.
    """
    return _experiments_to_tuples(experiments, list(experiments[0].keys()))

def simplify_experiments_to_dicts(experiments: List[dict]) -> List[List[dict]]:
    """Like experiments_to_tuples, but without a block argument,
    so the factor names are inferred from the experiments.
    """
    return _experiments_to_dicts(experiments, list(experiments[0].keys()))

def experiments_to_dicts(block: Block, experiments: List[dict]) -> List[List[dict]]:
    """Converts a list of experiments into a list of lists of dictionaries, where
    each dictionary represents a crossing in a given experiment.

    :param block:
        An experimental description as a :class:`.Block`.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to the synthesis function :func:`.synthesize_trials`.

    :returns:
        A list of lists of dictionaries, where each sub-list corresponds
        to one of the ``experiments``, each dictionary corresponds to a particular
        crossing, and each string is the simple surface name of a level.
    """
    return _experiments_to_dicts(experiments, [cast(str, f.name) for f in __filter_hidden(block.design)])

def experiments_to_tuples(block: Block, experiments: List[dict]) -> List[List[tuple]]:
    """Converts a list of experiments into a list of lists of tuples, where
    each tuple represents a crossing in a given experiment.

    :param block:
        An experimental description as a :class:`.Block`.

    :param experiments:
        A list of experiments as :class:`dicts <dict>`. These are produced by
        calls to the synthesis function :func:`.synthesize_trials`.

    :returns:
        A list of lists of tuples of strings, where each sub-list corresponds
        to one of the ``experiments``, each tuple corresponds to a particular
        crossing, and each string is the simple surface name of a level.
    """
    return _experiments_to_tuples(experiments, [cast(str, f.name) for f in __filter_hidden(block.design)])

def __filter_hidden(design: List[Factor]) -> List[Factor]:
    return list(filter(lambda f: not isinstance(f.name, HiddenName), design))


def __filter_hidden_keys(d: dict) -> dict:
    return {name: d[name] for name in filter(lambda name: not isinstance(name, HiddenName), d.keys())}


def print_experiments(block, experiments):
    """Displays the generated experiments in a human-friendly form.

    :param block:
        An experimental description as a :class:`.Block`.

    :param experiments:
        A :class:`list` of experiment :class:`dicts <dict>`, as produced by
        :func:`.synthesize_trials`.

        When the ``block`` includes a :class:`.LatinSquare` constraint that was
        given a ``name``, each experiment's output is divided into sections
        labeled by that name (one section per diagonal).
    """
    # Restore continuous factors for printing trials
    block.restore_continuous()

    ls_name = None
    ls_dlen = 0
    for ct in block.orig_constraints:
        if isinstance(ct, LatinSquare) and ct.name:
            ls_name = ct.name
            ls_dlen = ct.diagonal_length()

    released_from = [ct for ct in block.constraints
                     if isinstance(ct, LatinSquare) and ct.may_release]

    for message in block.applied_relaxations:
        print(message)
    print('\n{} trial sequences found.\n'.format(len(experiments)))
    for idx, e in enumerate(experiments):
        print('Experiment {}:'.format(idx))
        for ct in released_from:
            # Each experiment may release different participants.
            out = ct.released_participants(e, block)
            if out:
                print('Released from the Latin square: participant {}'.format(
                    ', '.join(str(p) for p in out)))
        e_len = len(e[next(iter(e))])
        if ls_name:
            print('')
            for i in range(0, e_len, ls_dlen):
                print('{} {}:'.format(ls_name, i // ls_dlen))
                _print_experiment_participant(block.orig_design, e, i, min(i+ls_dlen, e_len))
        else:
            _print_experiment_participant(block.orig_design, e, 0, e_len)

def _print_experiment_participant(design, e, start, end):
    """Print a single experiment/participant."""
    # Use factor-name order from the block's design so that output is consistent
    names = [f.name for f in design if not isinstance(f.name, HiddenName)]
    strs = [list(map(lambda v: name + " " + str(v), e[name][start:end])) for name in names]
    transposed = list(map(list, zip(*strs)))
    format_str = _get_column_widths(transposed)
    print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


def _get_column_widths(data):
    # Compute column widths from actual content
    columns = list(zip(*data))
    column_widths = [max(len(cell) for cell in col) for col in columns]
    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'
    return format_str


def tabulate_experiments(block: Optional[Block] = None,
                         experiments: Optional[List[Dict]] = None,
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
        if (not isinstance(block, MultiCrossBlockRepeat)) or len(block.crossings) != 1:
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
            proportion_list.append(str(proportion * 100) + '%')

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
                      sampling_strategy=IterateGen
                      ):
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
        A :class:`list` of trial sets.
    """

    def starting(who):
        # type: (Any) -> None
        print("Sampling {} trial sequences using {}.".format(samples, who))

    def run():
        if isinstance(sampling_strategy, type):
            return sampling_strategy.sample(block, samples)
        return sampling_strategy.sample_object(block, samples)

    if isinstance(sampling_strategy, type):
        assert issubclass(sampling_strategy, Gen)
        starting(sampling_strategy.class_name())
    else:
        starting(sampling_strategy)
    sampling_result = _concede_until_satisfiable(block, run(), run)

    # DW: I am not sure if I need to fix this. Need to discuss with Matthew
    raw_samples = sampling_result.samples[:samples]

    trialss = []
    for e in raw_samples:
        with_implied = block.add_implied_levels(e)
        # Run mismatch check BEFORE filtering hidden keys
        if os.getenv("SWEETPEA_CHECK_SYNTHESIZED"):
            mismatches = sample_mismatch_experiment(block, with_implied)
            if mismatches:
                print_experiments(block, [with_implied])
                print(mismatches)
                raise RuntimeError("synthesized trials has mismatches")

        # Now filter hidden keys for the returned trials
        trialss.append(__filter_hidden_keys(with_implied))

    # Sampling for ContinuousFactor
    if block.continuous_factors:
        for num_trial, trials in enumerate(trialss):
            continuous_samples = block.sample_continuous(num_trial, trialss[num_trial])
            for k in continuous_samples:
                trials[k] = continuous_samples[k]
        # Restore ContinuousFactor to the design

    if not trialss:
        print(_no_sequences_message(block, sampling_result.outcome))

    return trialss


def _concede_until_satisfiable(block, result, run):
    """The concessions the design authorized, in order: every step of a Relax
    budget, then one coverage factor at a time.

    Applied cumulatively and never taken back, so the sequence is linear in the
    number of concessions rather than a search over their combinations."""
    result = _weaken_until_satisfiable(block, result, run)
    result = _release_square_until_satisfiable(block, result, run)
    return _drop_optional_until_satisfiable(block, result, run)


def _release_square_until_satisfiable(block, result, run):
    """Let one more participant leave the Latin square, re-solving after each.

    Which participants leave is the solver's choice, so the first allowance
    that works is also the fewest participants the design can give up."""
    square = _releasable_square(block)
    if result.outcome is not SolveOutcome.UNSATISFIABLE or square is None:
        return result
    while square.can_release():
        released = square.release_one()
        print("No solution; letting up to {} participant(s) leave the Latin "
              "square.".format(released))
        result = run()
        if result.samples:
            record_concessions(block)
            return result
    return result


def _releasable_square(block):
    """The block's Latin square that may still release a participant."""
    for ct in block.constraints:
        if isinstance(ct, LatinSquare) and ct.can_release():
            return ct
    return None


def _drop_optional_until_satisfiable(block, result, run):
    """Give up one optional coverage factor at a time, last in the list first,
    resizing the block after each.

    A drop is kept whether or not it helps, so what is reported is what the
    block actually requires by the end."""
    coverage = _droppable_coverage(block)
    if result.outcome is not SolveOutcome.UNSATISFIABLE or coverage is None:
        return result
    while coverage.can_drop():
        given_up = coverage.drop_one()
        print("No solution; giving up {}.".format(given_up.name))
        # The resize records the concession, from the constraint's own state.
        block.resize_for_coverage()
        result = run()
        if result.samples:
            return result
    return result


def _droppable_coverage(block):
    """The block's coverage constraint that still has a factor to give up."""
    for ct in block.constraints:
        if isinstance(ct, CoverAllCombinations) and ct.can_drop():
            return ct
    return None


def _weaken_until_satisfiable(block, result, run):
    """Step the block's one `Relax`-authorized constraint until the design has a
    solution or its budget runs out, re-solving after each step.

    Only a definitive UNSATISFIABLE justifies this. An unknown outcome means the
    solver failed, which is no reason to alter the experiment."""
    constraint = solver_relaxable(block)
    if result.outcome is not SolveOutcome.UNSATISFIABLE or constraint is None:
        return result
    relaxation = constraint.relaxation
    written = relaxation.base_k(constraint.k)
    relaxation.original_k = written
    relaxation.applied_for = "the solver found no solution otherwise"
    for _ in range(relax_budget(constraint)):
        constraint.k += constraint.weaken_step
        # Track the value as it moves, not only when this loop is the one that
        # succeeds: a later concession can be what completes the design, and the
        # report has to name every constraint the design ended up relying on.
        relaxation.applied_k = constraint.k
        print("No solution; retrying with {}(k={}).".format(
            type(constraint).__name__, constraint.k))
        result = run()
        if result.samples:
            record_concessions(block)
            return result
    # The steps stay: concessions accumulate so that a later one starts from
    # what the earlier ones bought. Nothing is written to the block's report
    # here, so a run that never produces a design reports nothing.
    return result


def _no_sequences_message(block, outcome) -> str:
    """Why nothing came back, taken from the solver's answer rather than
    inferred from the empty list."""
    from sweetpea._internal.constraint import _KInARow
    if outcome is SolveOutcome.UNKNOWN:
        return ("No trial sequences found: the solver gave no answer, so this "
                "reports a solver failure rather than the design.")
    relaxed = solver_relaxable(block)
    if relaxed is not None:
        return ("No trial sequences found: the design has no solution, and "
                "weakening {} by up to {} was not enough."
                .format(type(relaxed).__name__, relaxed.relaxation.by))
    cacs = [ct for ct in block.orig_constraints if isinstance(ct, CoverAllCombinations)]
    if not cacs:
        return "No trial sequences found: the design has no solution."
    # Coverage auto-sizing cannot account for ordering constraints or
    # LatinSquare, so name those as the likely conflict.
    msg = ("No trial sequences found: the constraints could not be satisfied "
           "together with " + " and ".join(repr(ct) for ct in cacs) + ".")
    unmodeled = sorted(set(type(ct).__name__ for ct in block.orig_constraints
                           if isinstance(ct, (_KInARow, LatinSquare))))
    if unmodeled:
        msg += (" Constraints of kind " + ", ".join(unmodeled)
                + " are not folded into coverage auto-sizing; a MinimumTrials"
                  " constraint can provide additional trials.")
    return msg

def sample_mismatch_experiment(block: Block, sample: dict) -> dict:
    """Given an experiment described with a :class:`.Block`, tests if :class:`list`
    of trials meets the factors, constraints and crossings of the described experiment.


    This function should be used on the :class:`.Block` produced by either
    :func:`.fully_cross_block` or :func:`.multiple_cross_block`. Using that
    :class:`.Block`, :func:`.synthesize_trials`.

    :param block:
        An experimental description as a :class:`.Block`.

    :param sample:
        A sample in the form of a :class:`list`.

    :returns:
        A :class:`dict` describing the mismatches. The entries of the dictionary lists the
        mismatches in the categories factors, constraints and crossings
    """
    res = {}
    for key in sample:
        if len(sample[key]) != block._trials_per_sample():
            res['trial_count'] = [key, len(sample[key]), block._trials_per_sample()]
    if not res:
        factor_errors = block.sample_mismatch_factors(sample)
        if factor_errors:
            res['factors'] = factor_errors
        constraint_errors = block.sample_mismatch_constraints(sample)
        if constraint_errors:
            res['constraints'] = constraint_errors
        crossing_errors = block.sample_mismatch_crossing(sample)
        if crossing_errors:
            res['crossings'] = crossing_errors
    return res


def auto_correlation_scores_samples_between(samples: list, factor_names: List[str] = [],
                                            number_trials: int = 10, starts: int = 10) -> dict:
    """Given a number of samples given as :class:`list` of trial sets, calculates
    a auto correlation score representing if a level can be predicted from the k
    proceeding levels. This is done by creating a neural network that is trained on
    predicting a factor based on the levels in all factors of the preceding trials.
    The number of preceding trials taken into account is the minimum between number_trials
    and half the sequence length.


    :param samples:
        A :class:`list` of trial sets. Each set is represented as a :class:`dictionary <dict>`
        mapping each factor name to a list of levels, where each such list contains
        to one level per trial.
    :param factor_names:
        A :class`list` of string. The factors to be tested (if None, all factors in samples are tested)
    :param number_trials:
        A :class int that indicates how many trials before the predicted trial to use for the prediction
    :param starts:
        A :class int that indicates how many times a new neural network is created. The final score is the
        max prediction score of theses networks.
    :returns:
        A :class:`dict` describing the auto correlation of each factor.
    """
    res = {}
    if not factor_names:
        for f in samples[0].keys():
            res[f] = auto_correlation_score_factor_between(samples, f, k=number_trials, starts=starts)
    else:
        for f in factor_names:
            res[f] = auto_correlation_score_factor_between(samples, f, k=number_trials, starts=starts)
    return res


def auto_correlation_scores_sample_within(sample: dict, factor_names: List[str] = [],
                                          number_trials: int = 10, starts: int = 10) -> dict:
    """Given a samples given as :class:`dict` of a trial set, calculates
    a auto correlation score representing if a level can be predicted from the k
    proceeding levels. This is done by creating a neural network that is trained on
    predicting a factor based on the levels in all factors of the preceding trials.
    The number of preceding trials taken into account is the minimum between number_trials
    and half the sequence length.


    :param sample:
        A :class:`dict` mapping each factor name to a list of levels, where each such list contains
        to one level per trial.
    :param factor_names:
        A :class`list` of string. The factors to be tested (if None, all factors in samples are tested)
    :param number_trials:
        A :class int that indicates how many trials before the predicted trial to use for the prediction
    :param starts:
        A :class int that indicates how many times a new neural network is created. The final score is the
        max prediction score of theses networks.
    :returns:
        A :class:`dict` describing the auto correlation of each factor.
    """
    res = {}
    if not factor_names:
        for f in sample.keys():
            res[f] = auto_correlation_score_factor_within(sample, f, k=number_trials, starts=starts)
    else:
        for f in factor_names:
            res[f] = auto_correlation_score_factor_within(sample, f, k=number_trials, starts=starts)
    return res


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
    return cnf.as_unigen_string(sampled_variables=[Var(n) for n in block.support_variables()])
