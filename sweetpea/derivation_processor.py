import operator as op

from typing import Dict, List, Tuple, Union, Any, cast
from functools import reduce
from itertools import product

# TODO: Fix this Derivation name collision.
from sweetpea.primitives import Derivation as DerivationPrimitive, DerivedFactor, DerivedLevel, Factor, Level, WithinTrial, Transition, Window, get_external_level_name, SimpleLevel
from sweetpea.blocks import Block
from sweetpea.constraints import Derivation
from sweetpea.internal import chunk_list, get_all_levels


class DerivationProcessor:
    """
    Usage::

        >>> import operator as op
        >>> color = Factor("color", ["red", "blue"])
        >>> text  = Factor("text",  ["red", "blue"])
        >>> conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
        >>> incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
        >>> conFactor = Factor("congruent?", [conLevel, incLevel])
        >>> design = [color, text, conFactor]
        >>> crossing = [color, text]
        >>> __process_derivations(design, crossing)
        [Derivation(derivedIdx=4, dependentIdxs=[[0, 2], [1, 3]]), Derivation(derivedIdx=5, dependentIdxs=[[0, 3], [1, 2]])]

    :rtype:
        returns a list of tuples. Each tuple is structured as:
        ``(index of the derived level, list of dependent levels)``

    In the example above, the indicies of the design are:

    ===  =============
    idx  level
    ===  =============
    0    color:red
    1    color:blue
    2    text:red
    3    text:blue
    4    conFactor:con
    5    conFactor:inc
    ===  =============

    So the tuple (4, [[0,2], [1,3]]) represents the information that the
    derivedLevel con is true iff ``(color:red && text:red) || (color:blue &&
    text:blue)`` by pairing the relevant indicies together.
    """
    @staticmethod
    def generate_derivations(block: Block) -> List[Derivation]:
        derived_factors: List[DerivedFactor] = [factor for factor in block.design if isinstance(factor, DerivedFactor)]
        accum = []

        for factor in derived_factors:
            according_level: Dict[Tuple[Any, ...], DerivedLevel] = {}
            for level in factor.levels:
                cross_product: List[Tuple[Level, ...]] = level.get_dependent_cross_product()
                valid_tuples: List[Tuple[Level, ...]] = []
                for level_tuple in cross_product:
                    names = [level.name for level in level_tuple]
                    if level.derivation.width != 1:
                        # NOTE: mypy doesn't like this, but I'm not rewriting
                        #       it right now. Need to replace `chunk_list` with
                        #       a better version.
                        names = list(chunk_list(names, level.derivation.width))  # type: ignore
                    result = level.derivation.predicate(*names)
                    if not isinstance(result, bool):
                        raise ValueError(f"Expected derivation predicate to return bool; got {type(result)}.")
                    if level.derivation.predicate(*names):
                        valid_tuples.append(level_tuple)
                        if level_tuple in according_level:
                            raise ValueError(f"Factor {factor.name} matches {according_level[level_tuple].name} and "
                                             f"{level.name} with assignment {names}.")
                        according_level[level_tuple] = level

                if not valid_tuples:
                    print(f"WARNING: There is no assignment that matches factor {factor.name} with level {level.name}.")

                valid_indices = [[block.first_variable_for_level(level.factor, level) for level in valid_tuple]
                                 for valid_tuple in valid_tuples]
                shifted_indices = DerivationProcessor.shift_window(valid_indices,
                                                                   level.derivation,
                                                                   block.variables_per_trial())
                level_index = block.first_variable_for_level(factor, level)
                accum.append(Derivation(level_index, shifted_indices, factor))
        return accum

    @staticmethod
    def generate_argument_list(level: DerivedLevel, tup: Tuple[Level, ...]) -> List:
        # User-supplied string level names are the arguments for the user-supplied derivation functions
        level_strings = [level.name for level in tup]
        # For windows with a width of 1, we just pass the arguments directly, rather than putting them in lists.
        if level.window.width == 1:
            return level_strings
        else:
            return list(chunk_list(level_strings, level.window.width))


    """
    This is a helper function that shifts the idxs of __process_derivations.
    ie, if its a Transition(op.eq, [color, color]) (ie "repeat" color transition)
        then the indexes for the levels of color would be like (0, 0), (1, 1)
        but actually, the window size for a transition is 2, so what we really want is the indicies
        (0, 5), (1, 6) (assuming there are 4 levels in the design)
    So this helper function shifts over indices that were meant to be intepretted as being in a subsequent trial.
    """
    @staticmethod
    def shift_window(indices: List[List[int]],
                     derivation: DerivationPrimitive,
                     trial_size: int
                     ) -> List[List[int]]:
        if derivation.width == 1:
            return indices

        # shifted_indices: List[List[int]] = []
        # shifted_sublists: List[List[int]] = []

        # factor_count = len(derivation.factors)

        # for index_list in indices:
        #     sublist_size = len(index_list) // factor_count
        #     sublists = chunk_list(index_list, sublist_size)
        #     shifted_sublists =

        shifted_idxs = cast(List[List[int]], [])
        shifted_sublists = cast(List[List[int]], [])
        argc = derivation.initial_factor_count
        for idx_list in indices:
            sublist_size = len(idx_list) // argc
            sublists = chunk_list(idx_list, sublist_size)
            shifted_sublists = [reduce(lambda l, idx: l + [idx + len(l) * trial_size], idx_list, []) for idx_list in sublists]
            shifted_idxs.append(list(reduce(op.add, shifted_sublists, [])))

        return shifted_idxs
