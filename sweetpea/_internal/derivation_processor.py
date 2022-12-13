"""This module provides functionality for processing derivations."""


import operator as op

from typing import Any, Dict, List, Tuple, cast
from functools import reduce

from sweetpea._internal.primitive import Window, DerivedFactor, DerivedLevel, Level
from sweetpea._internal.block import Block
from sweetpea._internal.constraint import Derivation
from sweetpea._internal.iter import chunk_list, chunk_dict
from sweetpea._internal.beforestart import BeforeStart

class DerivationProcessor:

    @staticmethod
    def generate_derivations(block: Block) -> List[Derivation]:
        """Usage::

            >>> import operator as op
            >>> color = Factor("color", ["red", "blue"])
            >>> text  = Factor("text",  ["red", "blue"])
            >>> conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
            >>> incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
            >>> conFactor = Factor("congruent?", [conLevel, incLevel])
            >>> design = [color, text, conFactor]
            >>> crossing = [color, text]
            >>> block = fully_cross_block(design, crossing, [])
            >>> DerivationProcessor.generate_derivations(block)
            [Derivation(derivedIdx=4, dependentIdxs=[[0, 2], [1, 3]]), Derivation(derivedIdx=5, dependentIdxs=[[0, 3], [1, 2]])]

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

        So the tuple ``(4, [[0,2], [1,3]])`` represents the information that
        the derivedLevel con is true iff ``(color:red && text:red) ||
        (color:blue && text:blue)`` by pairing the relevant indices together.

        :rtype:
            returns a list of tuples. Each tuple is structured as:
            ``(index of the derived level, list of dependent levels)``
        """
        # We include implied factors in `derived_factors` so we check the mapping of levels,
        # but we'll only add to `accum` if the factor is non-implied
        derived_factors: List[DerivedFactor] = [factor for factor in block.design if isinstance(factor, DerivedFactor)]
        accum = []
        for factor in derived_factors:
            according_level: Dict[Tuple[Any, ...], DerivedLevel] = {}
            for level in factor.levels:
                cross_product: List[Tuple[Level, ...]] = level.get_dependent_cross_product()
                valid_tuples: List[Tuple[Level, ...]] = []
                for level_tuple in cross_product:
                    args = [(level.name if not isinstance(level, BeforeStart) else None) for level in level_tuple]
                    if level.window.width != 1:
                        # NOTE: mypy doesn't like this, but I'm not rewriting
                        #       it right now. Need to replace `chunk_dict` with
                        #       a better version.
                        args = list(chunk_dict(args, level.window.width))  # type: ignore
                    result = level.window.predicate(*args)
                    if not isinstance(result, bool):
                        raise ValueError(f"Expected derivation predicate to return bool; got {type(result)}.")
                    if result:
                        valid_tuples.append(level_tuple)
                        if level_tuple in according_level:
                            raise ValueError(f"Factor {factor.name} matches {according_level[level_tuple].name} and "
                                             f"{level.name} with assignment {args}.")
                        according_level[level_tuple] = level

                if not valid_tuples:
                    in_crossing = block.factor_in_crossing(factor)
                    # Solvers can go wrong if a crossing level is not even possible:
                    maybe_warning = "WARNING: " if (not in_crossing) or not block.require_complete_crossing else ""
                    maybe_crossing = "crossed " if in_crossing else ""
                    not_satisfiable = "not satisfiable" if block.require_complete_crossing else "incomplete"
                    conclusion = f", which means that the crossing is {not_satisfiable}" if in_crossing else ""
                    block.errors.add(f"{maybe_warning}No matches to the {maybe_crossing}factor"
                                     f" '{factor.name}' predicate for level\n '{level.name}'{conclusion}.")

                if factor in block.act_design:
                    # A `BeforeStart` in a tuple means that it should only be used for an early trial
                    # where the corresponding level is not yet available
                    valid_indices = [[(block.first_variable_for_level(level.factor, level) if not isinstance(level, BeforeStart) else level)
                                      for level in valid_tuple]
                                     for valid_tuple in valid_tuples]
                    shifted_indices = DerivationProcessor.shift_window(valid_indices,
                                                                       level.window,
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
            return list(chunk_dict(level_strings, level.window.width))

    @staticmethod
    def shift_window(indices: List[List[object]],
                     window: Window,
                     trial_size: int
                     ) -> List[List[object]]:
        """This is a helper function that shifts the indices of
        :func:`.DerivationProcessor.generate_derivations`.

        E.g., if it's a ``Transition(op.eq, [color, color])`` (i.e., "repeat"
        color transition) then the indices for the levels of color would be
        like ``(0, 0)``, ``(1, 1)``, but actually, the window size for a
        transition is ``2``, so what we really want is the indices ``(0, 5)``,
        ``(1, 6)`` (assuming there are 4 levels in the design).

        So this helper function shifts over indices that were meant to be
        interpreted as being in a subsequent trial.
        """
        if window.width == 1:
            return indices

        # shifted_indices: List[List[int]] = []
        # shifted_sublists: List[List[int]] = []

        # factor_count = len(window.factors)

        # for index_list in indices:
        #     sublist_size = len(index_list) // factor_count
        #     sublists = chunk_list(index_list, sublist_size)
        #     shifted_sublists =

        shifted_idxs = cast(List[List[object]], [])
        shifted_sublists = cast(List[List[object]], [])
        argc = len(window.factors)
        for idx_list in indices:
            sublist_size = len(idx_list) // argc
            sublists = chunk_list(idx_list, sublist_size)
            shifted_sublists = []
            for idx_list in sublists:
                l = cast(List[object], [])
                for i, idx in enumerate(idx_list):
                    if isinstance(idx, BeforeStart):
                        l.append(BeforeStart(idx.ready_at+(len(idx_list) - i - 1)))
                    else:
                        l.append(cast(int, idx) + i * trial_size)
                shifted_sublists.append(l)
            shifted_idxs.append(list(reduce(op.add, shifted_sublists, [])))

        return shifted_idxs
