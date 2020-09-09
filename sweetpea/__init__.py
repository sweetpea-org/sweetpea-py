from functools import reduce
from typing import Any, List, Union, Tuple, cast

from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.internal import chunk, get_all_levels, intersperse
from sweetpea.logic import to_cnf_tseitin
from sweetpea.blocks import Block, FullyCrossBlock
from sweetpea.docker import update_docker_image, start_docker_container, stop_docker_container, check_server_health
from sweetpea.backend import BackendRequest
from sweetpea.primitives import *
from sweetpea.constraints import *
from sweetpea.sampling_strategies.base import SamplingStrategy
from sweetpea.sampling_strategies.non_uniform import NonUniformSamplingStrategy
from sweetpea.sampling_strategies.unigen import UnigenSamplingStrategy
from sweetpea.sampling_strategies.uniform_combinatoric import UniformCombinatoricSamplingStrategy
from sweetpea.server import submit_job, get_job_result, build_cnf
import csv

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Returns a fully crossed block that we'll process with synthesize! Carries with it the function that
should be used for all CNF conversions.
"""
def fully_cross_block(design: List[Factor],
                      crossing: List[Factor],
                      constraints: List[Constraint],
                      require_complete_crossing=True,
                      cnf_fn=to_cnf_tseitin) -> Block:
    all_constraints = cast(List[Constraint], [FullyCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints) #expand the constraints into a form we can process.
    block = FullyCrossBlock(design, [crossing], all_constraints, require_complete_crossing, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    if not constraints and not list(filter(lambda f: f.is_derived(), crossing)) and not list(filter(lambda f: f.has_complex_window(), design)):
        block.complex_factors_or_constraints = False
    return block


"""
Returns a block with multiple crossings that we'll process with synthesize! Carries with it the function that
should be used for all CNF conversions.
"""
def multiple_cross_block(design: List[Factor],
                      crossing: List[List[Factor]],
                      constraints: List[Constraint],
                      require_complete_crossing=True,
                      cnf_fn=to_cnf_tseitin) -> Block:
    all_constraints = cast(List[Constraint], [MultipleCross(), Consistency()]) + constraints
    all_constraints = __desugar_constraints(all_constraints) #expand the constraints into a form we can process.
    block = MultipleCrossBlock(design, crossing, all_constraints, require_complete_crossing, cnf_fn)
    block.constraints += DerivationProcessor.generate_derivations(block)
    return block


def __desugar_constraints(constraints: List[Constraint]) -> List[Constraint]:
    desugared_constraints = []
    for c in constraints:
        desugared_constraints.extend(c.desugar())
    return desugared_constraints


"""
Display the generated experiments in human-friendly form.
"""
def print_experiments(block: Block, experiments: List[dict]):
    nested_assignment_strs = [list(map(lambda l: f.factor_name + " " + get_external_level_name(l), f.levels)) for f in block.design]
    column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

    print('{} trial sequences found.'.format(len(experiments)))
    for e in experiments:
        strs = [list(map(lambda v: name + " " + v, values)) for (name,values) in e.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


"""
Export the generated experiments to csv files. Each experiment will be exported to a separate csv file. 
"""
def experiment_to_csv(experiments: List[dict], file_prefix = "experiment"):
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


"""
This is a helper function for getting some number of unique non-uniform solutions. It invokes a separate
endpoint on the server that repeatedly computes individual solutions while updating the formula to exclude
each solution once it has been found. It's intended to give users something somewhat useful, while
we work through issues with unigen.

TODO this seems to be a bandaid for the issues unigen presents. Perhaps there is a better way?
    Currently, we have the block and the samples, and want a dictionary output. (Haskell like notation).
"""
def synthesize_trials_non_uniform(block: Block, samples: int) -> List[dict]:
    if block.complex_factors_or_constraints:
        return synthesize_trials(block, samples, sampling_strategy=NonUniformSamplingStrategy)
    else:
        return synthesize_trials(block, samples, sampling_strategy=UniformCombinatoricSamplingStrategy)


def synthesize_trials_uniform(block: Block, samples: int) -> List[dict]:
    if block.complex_factors_or_constraints:
        return synthesize_trials(block, samples, sampling_strategy=UnigenSamplingStrategy)
    else:
        return synthesize_trials(block, samples, sampling_strategy=UniformCombinatoricSamplingStrategy)

"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results
in some direct cnfs being produced and some requests to the backend being produced). Then
calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable
& (2) psyNeuLink readable.

PsyNeuLink is a software from Princeton that assists in creating block diagrams for these experiments.
"""
def synthesize_trials(block: Block, samples: int=10, sampling_strategy=UnigenSamplingStrategy) -> List[dict]:
    print("Sampling {} trial sequences using the {}".format(samples, sampling_strategy))
    sampling_result = sampling_strategy.sample(block, samples)
    return sampling_result.samples

"""
Takes the block of the provided trial and writes its preferences out to a configuration file.

"""
def save_cnf(block: Block, filename: str) -> None:
    cnf_str = __generate_cnf(block)
    with open(filename, 'w') as f:
        f.write(cnf_str)

# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""
Invokes the backend to build the final CNF formula in DIMACS format, returning it as a string.

DIMACS format: Starting lines are marked by a c to denote a comment
    after comments, there is a problem line denoted by a p. ex: (p cnf 3 4) means the problem is a cnf with 3 variables and 4 clauses.
        variables: items that may change values
        clauses: phrase containing both subject and a verb, but is not necessarily a full sentence. Longer than a phrase.
    after the problem statement, the individual clauses are listed as numbers, and 0 marks the end of each claues.
    for example, (x(9) AND y(2)) => 9 2 0, while (NOT x(9) OR y(2)) => -9 2 0.
"""
def __generate_cnf(block: Block) -> str:
    update_docker_image("sweetpea/server")
    container = start_docker_container("sweetpea/server", 8080)

    try:
        cnf_result = build_cnf(block)
    finally:
        stop_docker_container(container)

    return cnf_result['cnf_str']
