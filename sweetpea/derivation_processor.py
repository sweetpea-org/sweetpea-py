import operator as op

from typing import Dict, List, Tuple, Union, Any, cast
from functools import reduce
from itertools import product

from sweetpea.primitives import DerivedLevel, WithinTrial, Transition, Window, get_external_level_name, SimpleLevel
from sweetpea.blocks import Block
from sweetpea.constraints import Derivation
from sweetpea.internal import chunk_list, get_all_levels


class DerivationProcessor:
    """
    Useage::
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
    @staticmethod
    def generate_derivations(block: Block) -> List[Derivation]:
        derived_factors = list(filter(lambda f: f.is_derived(), block.design))
        accum = []

        for fact in derived_factors:
            according_level : Dict[Tuple[Any, ...], DerivedLevel] = {} 
            # according_level = {}
            for level in fact.levels:
                level_index = block.first_variable_for_level(fact, level)
                x_product = level.get_dependent_cross_product()

                # filter to valid tuples, and get their idxs
                valid_tuples = []
                for tup in x_product:
                    args = DerivationProcessor.generate_argument_list(level, tup)
                    fn_result = level.window.fn(*args)

                    # Make sure the fn returned a boolean
                    if not isinstance(fn_result, bool):
                        raise ValueError('Derivation function did not return a boolean! factor={} level={} fn={} return={} args={} '.format(
                            fact.factor_name,
                            get_external_level_name(level),
                            level.window.fn,
                            fn_result,
                            args))

                    # If the result was true, add the tuple to the list
                    if fn_result:
                        valid_tuples.append(tup)
                        if tup in according_level.keys():
                            raise ValueError('Factor={} matches both level={} and level={} with assignment={}'.format(
                                fact.factor_name,
                                according_level[tup],
                                get_external_level_name(level),
                                args))
                        else:
                            according_level[tup] = get_external_level_name(level)

                if not valid_tuples:
                    print('WARNING: There is no assignment that matches factor={} level={}'.format(fact.factor_name, get_external_level_name(level)))

                valid_idxs = [[block.first_variable_for_level(pair[0], pair[1]) for pair in tup_list] for tup_list in valid_tuples]
                shifted_idxs = DerivationProcessor.shift_window(valid_idxs, level.window, block.variables_per_trial())
                accum.append(Derivation(level_index, shifted_idxs, fact))

        return accum

    @staticmethod
    def generate_argument_list(level: DerivedLevel, tup: Tuple) -> List:
        # User-supplied string level names are the arguments for the user-supplied derivation functions
        level_strings = list(map(lambda t: get_external_level_name(t[1]), tup))
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
    def shift_window(idxs: List[List[int]],
                     window: Union[WithinTrial, Transition, Window],
                     trial_size:int) -> List[List[int]]:
        if window.width == 1:
            return idxs

        shifted_idxs = cast(List[List[int]], [])
        shifted_sublists = cast(List[List[int]], [])
        argc = 1 if window.argc == None else window.argc
        for idx_list in idxs:
            sublist_size = len(idx_list) // argc
            sublists = chunk_list(idx_list, sublist_size)
            shifted_sublists = [reduce(lambda l, idx: l + [idx + len(l) * trial_size], idx_list, []) for idx_list in sublists]
            shifted_idxs.append(list(reduce(op.add, shifted_sublists, [])))

        return shifted_idxs
