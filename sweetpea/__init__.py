import docker
import json
import os
import requests
import shutil
import subprocess
import tempfile
import time

from ascii_graph import Pyasciigraph
from functools import reduce, partial
from collections import namedtuple
from datetime import datetime
from itertools import islice, repeat, product, chain, tee, accumulate
from typing import Any, Dict, List, Union, Tuple, Iterator, Iterable, cast
from sweetpea.logic import Iff, And, Or, Not, to_cnf, cnf_to_json


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         Example program (simple stroop)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import operator as op

color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
conFactor = Factor("congruent?", [conLevel, incLevel])

design       = [color, text, conFactor]

# k = 1
# constraints = [LimitRepeats(k, conLevel)]

crossing     = [color, text]
experiment   = fully_cross_block(design, crossing, []) # constraints)
(nVars, cnf) = synthesize_trials(experiment)
"""



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         Named Tuples
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO field validation, ie
# 1. levels should be non-empty
# 2. length of window args should match the number of args that func wants
# 3. length of window args for transition must be 2, and for withinTrial must be 1
# 4. types for the boolean functions (ie the args to And is a list of boolean functions)

# Everything the user interacts with
Factor       = namedtuple('Factor', 'name levels')
Window       = namedtuple('Window', 'func args stride')
Window.__new__.__defaults__ = (None, None, 1) # type: ignore

WithinTrial  = namedtuple('WithinTrial', 'func args')
Transition   = namedtuple('Transition', 'func args')
DerivedLevel = namedtuple('DerivedLevel', 'name window')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Everything from the frontend

HLBlock = namedtuple('HLBlock', 'design xing hlconstraints')
ILBlock = namedtuple('ILBlock', 'startAddr endAddr design xing constraints')

# constraints
FullyCross = namedtuple('FullyCross', '')
Consistency = namedtuple('Consistency', '')
Derivation = namedtuple('Derivation', 'derivedIdx dependentIdxs')

NoMoreThanKInARow = namedtuple('NoMoreThanKInARow', 'k levels')

# output
Request = namedtuple('Request', 'equalityType k booleanValues')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         "Front End" transformations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ~~~~~~~~~~ Helper functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Helper function which grabs names from derived levels;
    if the level is non-derived the level *is* the name
"""
def __get_level_name(level: Any) -> Any:
    if isinstance(level, DerivedLevel):
        return level.name
    return level


"""
Usage::
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue", "green"])
    >>> get_all_level_names([color, text])
    [('color', 'red'), ('color', 'blue'), ('text', 'red'), ('text', 'blue')]

"""
def __get_all_level_names(design: List[Factor]) -> List[Tuple[Any, Any]]:
    return [(factor.name, __get_level_name(level)) for factor in design for level in factor.levels]


"""
A full crossing is the product of the number of levels
in all the factors in the xing.

Usage::
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue", "green"])
    >>> fully_cross_size([color, text])
    6

:param xing: A list of Factor namedpairs ``Factor(name, levels)``.
:rtype: Int
"""
def __fully_cross_size(xing: List[Factor]) -> int:
    acc = 1
    for fact in xing:
        acc *= len(fact.levels)
    return acc


"""
Analogous to __fully_cross_size:
>>> __design_size([color, text])
4
"""
def __design_size(design: List[Factor]) -> int:
    return sum([len(f.levels) for f in design])


"""
Usage::
    >>> __get_dep_x_product(conLevel)
[(('color', 'red'), ('text', 'red')),
 (('color', 'red'), ('text', 'blue')),
 (('color', 'blue'), ('text', 'red')),
 (('color', 'blue'), ('text', 'blue'))]
:param level: A derived level which we want to get the crossing of
:rtype: list of tuples of tuples of strings which represent the crossing
** Careful! The length of the (outer) tuple depends on how many terms are part of the derivation! That's why there isn't a mypy annotation on the return type!
"""
def __get_dep_x_product(level: DerivedLevel) -> List[Tuple[Any, ...]]:
    return list(product(*[[(depFact.name, x) for x in depFact.levels] for depFact in level.window.args]))


"""
handy-dandy chunker from SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
"""
# TODO: add a canary print statement in case the resulting lists are not all the same length-- that is not the expected behavior (at least how it's used in desugar_fullycrossed)
def __chunk(it: Iterable[Any], size: int) -> Iterator[Tuple[Any, ...]]:
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

"""
This is a helper for getting how many directly encoded variables there are in the experiment.
For instance, if we have the simple stoop experiment (at the bottom of this page) then
    we have 4 trials, each of which encode state for 6 levels
    (this is because not all the factors are part of the full crossing)
    so there are 24 encoding variables
"""
def __encoding_variable_size(design: List[Factor], xing: List[Factor]) -> int:
    return __design_size(design) * __fully_cross_size(xing)

""" Simple helper to make process_derivations a tiny bit more legible
"""
def __get_derived_factors(design: List[Factor]) -> List[Factor]:
    is_derived = lambda x : isinstance(x.levels[0], DerivedLevel)
    return list(filter(is_derived, design))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~ Functions that have to do with derivations (called from fully_cross_block) ~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Useage::
    >>> import operator as op
    >>> color = Factor("color", ["red", "blue"])
    >>> text  = Factor("text",  ["red", "blue"])
    >>> conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    >>> incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
    >>> conFactor = Factor("congruent?", [conLevel, incLevel])
    >>> design = [color, text, conFactor]
    >>> xing = [color, text]
    >>> __process_derivations(design, xing)
    [Derivation(derivedIdx=4, dependentIdxs=[[0, 2], [1, 3]]), Derivation(derivedIdx=5, dependentIdxs=[[0, 3], [1, 2]])]
rtype: returns a list of tuples. Each tuple is structured as:
        (index of the derived level, list of dependent levels)
In the example above, the indicies of the design are:
    idx: level:
    0    color:red
    1    color:blue
    2    text:red
    3    text:blue
    4    conFactor:con
    5    conFactor:inc
So the tuple (4, [[0,2], [1,3]]) represents the information that
    the derivedLevel con is true iff
        (color:red && text:red) ||
        (color:blue && text:blue)
    by pairing the relevant indicies together.
"""
def __process_derivations(design: List[Factor], xing: List[Factor]) -> List[Derivation]:
    derived_factors = __get_derived_factors(design)
    all_levels = __get_all_level_names(design)
    accum = []
    for fact in derived_factors:
        for level in fact.levels:
            level_index = all_levels.index((fact.name, level.name))
            x_product = __get_dep_x_product(level)
            # filter to valid tuples, and get their idxs
            valid_tuples = [tup for tup in x_product if level.window.func(*map(lambda t: t[1], tup))]
            valid_idxs = [[all_levels.index(level) for level in tup] for tup in valid_tuples]
            shifted_idxs = __shift_window(valid_idxs, level.window, __design_size(design))
            accum.append(Derivation(level_index, shifted_idxs))
    return accum


"""
This is a helper function that shifts the idxs of __process_derivations.
ie, if its a Transition(op.eq, [color, color]) (ie "repeat" color transition)
    then the indexes for the levels of color would be like (0, 0), (1, 1)
    but actually, the window size for a transition is 2, so what we really want is the indicies
    (0, 5), (1, 6) (assuming there are 4 levels in the design)
So this helper function shifts over indices that were meant to be intepretted as being in a subsequent trial.
"""
def __shift_window(idxs: List[List[int]],
                   window: Union[WithinTrial, Transition, Window],
                   trial_size:int) -> List[List[int]]:
    if isinstance(window, WithinTrial):
        return idxs
    elif isinstance(window, Transition):
        return [[pair[0], pair[1]+trial_size] for pair in idxs]
    elif isinstance(window, Window):
        return [reduce(lambda l, idx: l + [idx + len(l) * trial_size], idx_list, []) for idx_list in idxs]
    else:
        raise ValueError("Weird window encountered while processing derivations!")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~ Functions that have to do with desugaring (called from synthesize) ~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
The derivations come in looking like
    Derivation(4, [[0, 2], [1, 3]])
    (derivedLevel index; list of indicies that are dependent)
This represents:
    4 iff (0 and 2) or (1 and 3)
These indicies are used the get the corresponding trial variables. Continuing from the example in of processDerivations, the first trial is represented by variables [1-6] (notice this feels like an off-by-one: the indicies start from 0, but the boolean variables start from 1). So we would use the idxs to map onto the vars as:
    5 iff (1 and 3) or (2 and 4)
Then we convert to CNF directly, ie
    toCNF(Iff(5, Or(And(1,3), And(2,4))))
This is then done for all window-sizes, taking into account strides (which are specified only in DerivedLevels specified with a general Window rather than Transition or WithinTrial). We grab window-sized chunks of the variables that represent the trials, map the variables using the indices, and then convert to CNF. These chunks look like:
    window1: 1  2  3  4  5  6
    window2: 7  8  9  10 11 12
So, for the second trial (since the window size in this example is 1) it would be:
    11 iff (7 and 9) or (8 and 10)
90% sure this is the correct way to generalize to derivations involving 2+ levels & various windowsizes
one test is the experiment: color = ["r", "b", "g"]; text = ["r", "b"]; conFactor; fullycross(color, text) + noMoreThanKInARow 1 conLevel

returns a list of CNF clauses
"""
def __desugar_derivation(derivation:Derivation, hl_block:HLBlock, fresh: int) -> Tuple[And, int]:
    trial_size = __design_size(hl_block.design)
    cross_size = __fully_cross_size(hl_block.xing)

    iffs = []
    for n in range(cross_size):
        iffs.append(Iff(derivation.derivedIdx + (n * trial_size) + 1,
                        Or(list(And(list(map(lambda x: x + (n * trial_size) + 1, l))) for l in derivation.dependentIdxs))))

    return to_cnf(And(iffs), fresh)


"""
The "consistency" constraints ensure that only one level of each factor is 'on' at a time.
So for instance in the experiment
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    design = crossing = [color, text, conFactor]
    experiment   = fully_cross_block(design, crossing, [])
The first trial is represented by the boolean vars [1, 2, 3, 4]
    0 is true iff the trial is color:red
    1 is true iff the trial is color:blue
    2 is true iff the trial is text:red
    3 is true iff the trial is text:blue
The second trial is represented by the boolean vars [5-8], the third by [9-12], the fourth by [13-16]
So this desugaring applies the following constraints:
    sum(1, 2) EQ 1
    sum(3, 4) EQ 1
    sum(5, 6) EQ 1
    ...
    sum(15, 16) EQ 1
It is an optimization to go directly to CNF instead of calling the backend, but it'll be cleaner to let the backend deal with that optimization rather than hacking it in here.
"""
def __desugar_consistency(hl_block:HLBlock) -> List[Request]:
    requests = []
    next_var = 1
    for _ in range(__fully_cross_size(hl_block.xing)):
        for f in hl_block.design:
            number_of_levels = len(f.levels)
            requests.append(Request("EQ", 1, list(range(next_var, next_var + number_of_levels))))
            next_var += number_of_levels

    return requests


"""
Helper recipe from https://docs.python.org/3/library/itertools.html#itertools-recipes
"""
def __pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


"""
We represent the fully crossed constraint by allocating additional boolean variables to represent each unique state. Only factors in xing will contribute to the number of states (there may be factors in the design that aren't in the xing).
Continuing with example from __desugar_consistency we will represent the states:
    (color:red, text:red)
    (color:red, text:blue)
    (color:blue, text:red)
    (color:blue, text:blue)
-- 1. Generate Intermediate Vars
Using the fresh var counter, allocate numTrials * numStates new vars
-- 2. Entangle them w/ block vars
Add to the CNF queue: toCNF(Iff(newVar, And(levels)))
    ie, if the variable 1 indicates color:red, the var 3 indicates text:red, and the var 25 represents (color:red, text:red):
        toCNF(Iff(25, And([1, 3])))
-- 3. 1 hot the *states* ie, 1 red circle, etc
same as __desugar_consistency above, collect all the state vars that represent each state & enforce that only one of those states is true, ie
    sum(25, 29, 33, 37) EQ 1
    (and 3 more of these for each of the other states).
This function returns BOTH some cnf clauses and some reqs.
"""
def __desugar_full_crossing(fresh:int, hl_block:HLBlock) -> Tuple[int, And, List[Request]]:
    numStates = __fully_cross_size(hl_block.xing) # same as number of trials in fully crossing
    numEncodingVars = __encoding_variable_size(hl_block.design, hl_block.xing)

    # Step 1:
    numStateVars = numStates * numStates
    stateVars = list(range(fresh, fresh+numStateVars))

    fresh += numStateVars

    # Step 2:
    states = list(__chunk(stateVars, numStates))
    transposed = list(map(list, zip(*states)))
    chunked_trials = list(__chunk(list(range(1, numEncodingVars + 1)), __design_size(hl_block.design)))

    # 1. group chunked_trials into factor shaped subchunks
    # ie, [[1, 2], [3, 4], [5, 6]], [[7, 8], ...
    delimiters = list(accumulate([0] + list(map(lambda i: len(hl_block.design[i].levels), range(len(hl_block.design))))))
    slices = list(__pairwise(delimiters))
    subchunked_trials = [[list(l[s[0]:s[1]]) for s in slices] for l in chunked_trials]

    # 2. grab the subchunks which correspond to levels in the xing
    # ie, [[1, 2], [3, 4]], [[7, 8], [9, 10]], [[...
    factor_dict = {factor.name: factor_index for factor_index, factor in enumerate(hl_block.design)}
    keep_factor_indices = [factor_dict[factor.name] for factor in hl_block.xing]
    subchunk_levels = [[chunked_trial[idx] for idx in keep_factor_indices] for chunked_trial in subchunked_trials]

    # 3. for each trial, take the itertools product of all the subchunks
    # ie, [[1, 3], [1, 4], [2, 3], [2, 4]], ...
    products = [list(product(*subchunks)) for subchunks in subchunk_levels]
    flattened_products = list(chain(*products))

    # 4. get those into an Iff w/ the state variables; ie Iff(25, And([1,3])) & then toCNF that & stash it on the queue.
    iffs = [Iff(stateVars[n], And(list(flattened_products[n]))) for n in range(len(stateVars))]

    # Step 3:
    # 5. make Requests for each transposed list that add up to k=1.
    requests = list(map(lambda l: Request("EQ", 1, l), transposed))

    (cnf, new_fresh) = to_cnf(And(iffs), fresh)
    return (new_fresh, cnf, requests)


"""
This desugars pretty directly into the llrequests.
The only thing to do here is to collect all the boolean vars that match the same level & pair them up according to k.
Continuing with the example from __desugar_consistency:
    say we want NoMoreThanKInARow 1 ("color", "red")
    then we need to grab all the vars which indicate color-red : [1, 7, 13, 19]
    and then wrap them up so that we're making requests like:
        sum(1, 7)  LT 1
        sum(7, 13)  LT 1
        sum(13, 19) LT 1
    if it had been NoMoreThanKInARow 2 ("color", "red") the reqs would have been:
        sum(1, 7, 13)  LT 2
        sum(7, 13, 19) LT 2
TODO: off-by-one errors?
"""
def __desugar_nomorethankinarow(k:int, level:Tuple[str, str], hl_block:HLBlock) -> List[Request]:
    # Generate a list of (factor name, level name) tuples from the block
    level_tuples = [list(map(lambda level: (f.name, level if isinstance(level, str) else level.name), f.levels)) for f in hl_block.design]
    flattened_tuples = list(chain(*level_tuples))

    # Locate the specified level in the list
    first_variable = flattened_tuples.index(level) + 1

    # Build the variable list
    design_var_count = __design_size(hl_block.design)
    num_trials = __fully_cross_size(hl_block.xing)
    var_list = list(accumulate(repeat(first_variable, num_trials), lambda acc, _: acc + design_var_count))

    # Break up the var list into overlapping lists where len == k.
    raw_sublists = [var_list[i:i+k+1] for i in range(0, len(var_list))]
    sublists = list(filter(lambda l: len(l) == k + 1, raw_sublists))

    # Build the requests
    return list(map(lambda l: Request("LT", k, l), sublists))


"""
TODO: not sure how 'balance' needs to be expressed given the current derivations. Ask Sebastian for a motivating example experiment.
"""
def __desugar_balance(fresh:int, factor_to_balance:Any, hl_block:HLBlock):
    print("WARNING THIS IS NOT YET IMPLEMENTED")
    return []


"""
Goal is to produce a json structure like:
    { "fresh" : 18,
         "requests" : [{
           "equalityType" : "EQ",
           "k" : 2,
           "booleanValues" : [1, 3, 5]
         },
         {
           "equalityType" : "LT",
           "k" : 1,
           "booleanValues" : [2, 4, 6]
         }
         ]
       }
Passing along the "fresh" variable counter & a list of reqs to the backend
Important! The backend is expecting json with these exact key names; if the names are change the backend Parser.hs file needs to be updated.
"""
def __jsonify(fresh:int, cnfs: List[And], ll_calls: List[Request], support: int) -> str:
    cnfList = cnf_to_json(cnfs)
    requests = list(map(lambda r: {'equalityType': r.equalityType, 'k': r.k, 'booleanValues': r.booleanValues}, ll_calls))

    return json.dumps({ "fresh" : fresh,
                        "cnfs" : cnfList,
                        "requests" : requests,
                        "unigen" : {
                            "support" : support,
                            "arguments" : [
                                "--verbosity=0",
                                "--samples=100"
                            ]
                        }})


"""
We desugar constraints in 2 ways; directly to CNF and by
    creating Requests to the backend. The requests are
    namedTuples that represent lowlevel requests:
A request is: namedtuple('Request', 'equalityType k booleanValues')
    options for equality-type are "EQ", "LT" & "GT"
We start keeping track of a "fresh" variable counter here; it starts at numTrials*numLevels+1. The convention is you use the fresh variable, and then update it. So fresh is like an always available new boolean variable.
Recall an HLBlock is: namedtuple('HLBlock', 'design xing hlconstraints')
"""
def __desugar(hl_block: HLBlock) -> Tuple[int, List[And], List[Request]]:
    fresh = 1 + __encoding_variable_size(hl_block.design, hl_block.xing)
    cnfs_created = []
    reqs_created = []
    # -----------------------------------------------------------
    # These go directly to CNF
    # filter the constraints to route to the correct processesors
    derivations = list(filter(lambda x: isinstance(x, Derivation), hl_block.hlconstraints))
    for d in derivations:
        (cnfs, fresh) = __desugar_derivation(d, hl_block, fresh)
        cnfs_created.append(cnfs)

    # -----------------------------------------------------------
    # These create lowlevel requests
    reqs_created.extend(__desugar_consistency(hl_block))

    # filter for any NoMoreThanKInARow constraints in hl_block.hlconstraints
    constraints = list(filter(lambda c: isinstance(c, NoMoreThanKInARow), hl_block.hlconstraints))
    for c in constraints:

        # Apply the constraint to each level in the factor.
        if isinstance(c.levels, Factor):
            levels = c.levels.levels  # Get the actual levels out of the factor.
            level_names = list(map(lambda l: __get_level_name(l), levels))
            level_tuples = list(map(lambda l_name: (c.levels.name, l_name), level_names))
            requests = list(map(lambda t: __desugar_nomorethankinarow(c.k, t, hl_block), level_tuples))
            reqs_created.extend(list(chain(*requests)))

        # Should be a Tuple containing the factor name, and the level name.
        elif isinstance(c.levels, tuple) and len(c.levels) == 2:
            reqs_created.extend(__desugar_nomorethankinarow(c.k, cast(Tuple[str, str], c.levels), hl_block))

        else:
            print("Error: unrecognized levels specification in NoMoreThanKInARow constraint: " + c.levels)

    # -----------------------------------------------------------
    # This one does both...
    (new_fresh, cnf, reqs) = __desugar_full_crossing(fresh, hl_block)
    cnfs_created.append(cnf)
    reqs_created.extend(reqs)

    return (new_fresh, cnfs_created, reqs_created)


"""
Decodes a single solution into a dict of this form:
{
  '<factor name>': ['<trial 1 label>', '<trial 2 label>, ...]
  ...
}
"""
def __decode(hl_block: HLBlock, solution: List[int]) -> dict:
    num_encoding_vars = __encoding_variable_size(hl_block.design, hl_block.xing);
    vars_per_trial = __design_size(hl_block.design)

    # Looks like [[2, 4, 6], [8, 10, 12], [14, 16, 18], [20, 22, 23]]
    trial_assignments = list(map(lambda l: list(filter(lambda n: n > 0, l)),
                                 list(__chunk(solution[:num_encoding_vars], vars_per_trial))))

    transposed = cast(List[List[int]], list(map(list, zip(*trial_assignments))))
    assignment_indices = [list(map(lambda n: (n - 1) % vars_per_trial, s)) for s in transposed]

    factor_names = list(map(lambda f: f.name, hl_block.design))
    factors = list(zip(factor_names, assignment_indices))

    level_names = list(map(lambda tup: tup[1], __get_all_level_names(hl_block.design)))

    experiment = {c: list(map(lambda idx: level_names[idx], v)) for (c,v) in factors}

    return experiment


def __generate_json_data(hl_block: HLBlock) -> str:
    (fresh, cnfs, reqs) = __desugar(hl_block)
    support = __encoding_variable_size(hl_block.design, hl_block.xing)
    return __jsonify(fresh - 1, cnfs, reqs, support)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~ Top-Level functions ~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Returns a fully crossed block that we'll process with synthesize!
"""
def fully_cross_block(design: List[Factor], xing: List[Factor], constraints: Any) -> HLBlock:
    derivation_constraints = cast(List[Any], __process_derivations(design, xing))
    all_constraints = [FullyCross, Consistency] + derivation_constraints + constraints
    return HLBlock(design, xing, all_constraints)


"""
Helper method to print a chart outlining the variable mappings, helpful for visualizing
the formula space. For example, for the simple stroop test:
----------------------------------------------
|   Trial |  color   |   text   | congruent? |
|       # | red blue | red blue |  con  inc  |
----------------------------------------------
|       1 |  1   2   |  3   4   |   5    6   |
|       2 |  7   8   |  9   10  |  11    12  |
|       3 | 13   14  | 15   16  |  17    18  |
|       4 | 19   20  | 21   22  |  23    24  |
----------------------------------------------
"""
def print_variable_grid(blk: HLBlock):
    design_size = __design_size(blk.design)
    num_trials = __fully_cross_size(blk.xing)
    num_vars = __encoding_variable_size(blk.design, blk.xing)

    largest_number_len = len(str(num_vars))

    header_widths = []
    row_format_str = '| {:>7} |'
    for f in blk.design:
        # length of all levels concatenated for this factor
        level_names = list(map(__get_level_name, f.levels))
        level_name_widths = [max(largest_number_len, l) for l in list(map(len, level_names))]

        level_names_width = sum(level_name_widths) + len(level_names) - 1 # Extra length for spaces in between names.
        factor_header_width = max(len(f.name), level_names_width)
        header_widths.append(factor_header_width)

        # If the header is longer than the level widths combined, then they need to be lengthened.
        diff = factor_header_width - level_names_width
        if diff > 0:
            idx = 0
            while diff > 0:
                level_name_widths[idx] += 1
                idx += 1
                diff -= 1
                if idx >= len(level_name_widths):
                    idx = 0

        # While we're here, build up the row format str.
        row_format_str = reduce(lambda a, b: a + ' {{:^{}}}'.format(b), level_name_widths, row_format_str)
        row_format_str += ' |'

    header_format_str = reduce(lambda a, b: a + ' {{:^{}}} |'.format(b), header_widths, '| {:>7} |')
    factor_names = list(map(lambda f: f.name, blk.design))
    header_str = header_format_str.format(*["Trial"] + factor_names)
    row_width = len(header_str)
    print('-' * row_width)
    print(header_str)

    all_level_names = [ln for (fn, ln) in __get_all_level_names(blk.design)]
    print(row_format_str.format(*['#'] + all_level_names))
    print('-' * row_width)

    for t in range(num_trials):
        args = [str(t + 1)] + list(map(str, range(t * design_size + 1, t * design_size + design_size + 2)))
        print(row_format_str.format(*args))

    print('-' * row_width)


"""
Display the generated experiments in human-friendly form.
"""
def print_experiments(hl_block: HLBlock, experiments: List[dict]):
    nested_assignment_strs = [list(map(lambda l: f.name + " " + __get_level_name(l), f.levels)) for f in hl_block.design]
    column_widths = list(map(lambda l: max(list(map(len, l))), nested_assignment_strs))

    format_str = reduce(lambda a, b: a + '{{:<{}}} | '.format(b), column_widths, '')[:-3] + '\n'

    for e in experiments:
        strs = [list(map(lambda v: name + " " + v, values)) for (name,values) in e.items()]
        transposed = list(map(list, zip(*strs)))
        print(reduce(lambda a, b: a + format_str.format(*b), transposed, ''))


"""
This is where the magic happens. Desugars the constraints from fully_cross_block (which results in some direct cnfs being produced and some requests to the backend being produced). Then calls unigen on the full cnf file. Then decodes that cnf file into (1) something human readable & (2) psyNeuLink readable.
"""
def synthesize_trials(hl_block: HLBlock) -> List[dict]:
    # TODO: Do this in separate thread, and output some kind of progress indicator.
    print("Generating design formula... ", end='', flush=True)
    t_start = datetime.now()
    json_data = __generate_json_data(hl_block)
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")

    solutions = cast(List[dict], [])

    docker_client = docker.from_env()

    # Make sure the local image is up-to-date.
    print("Updating docker image... ", end='', flush=True)
    try:
        t_start = datetime.now()
        docker_client.images.pull("sweetpea/server")
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")
    except:
        print("An error occurred while updating the docker image, continuing with locally-cached image.")

    # 1. Start a container for the sweetpea server, making sure to use -d and -p to map the port.
    print("Starting docker container... ", end='', flush=True)
    t_start = datetime.now()
    container = docker_client.containers.run("sweetpea/server", detach=True, ports={8080: 8080})
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")

    # Give the server time to finish starting to avoid connection reset errors.
    time.sleep(1)

    # 2. POST to /experiments/generate using the result of __jsonify as the body.
    # TOOD: Do this in separate thread, and output some kind of progress indicator.
    print("Sending formula to backend... ", end='', flush=True)
    t_start = datetime.now()
    try:
        health_check = requests.get('http://localhost:8080/')
        if health_check.status_code != 200:
            raise RuntimeError("SweetPea server healthcheck returned non-200 reponse! " + str(health_check.status_code))

        experiments_request = requests.post('http://localhost:8080/experiments/generate', data = json_data)
        if experiments_request.status_code != 200 or not experiments_request.json()['ok']:
            tmp_filename = ""
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(str.encode(json_data))
                tmp_filename = f.name

            raise RuntimeError("Received non-200 response from experiment generation! Request body saved to temp file '" +
                tmp_filename + "' status_code=" + str(experiments_request.status_code) + " response_body=" + str(experiments_request.text))

        solutions = experiments_request.json()['solutions']
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")

    # 3. Stop and then remove the docker container.
    finally:
        print("Stopping docker container... ", end='', flush=True)
        t_start = datetime.now()
        container.stop()
        container.remove()
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")

    # 4. Decode the results
    result = list(map(lambda s: __decode(hl_block, s['assignment']), solutions))

    # Dump histogram of frequency distribution, just to make sure it's somewhat even.
    print()
    print("Found " + str(len(solutions)) + " distinct solutions.")
    print()
    hist_data = [("Solution #" + str(idx + 1), sol['frequency']) for idx, sol in enumerate(solutions)]
    hist_data.sort(key=lambda tup: tup[1], reverse=True)

    graph = Pyasciigraph()
    for line in  graph.graph('Most Frequently Sampled Solutions', hist_data[:15]):
        print(line)

    return result
