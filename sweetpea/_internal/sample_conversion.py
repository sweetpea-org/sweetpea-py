from typing import List
from sweetpea._internal.primitive import Factor, Level


def _convert_from_name_to_factor(name: str, design: List[Factor]) -> Factor:
    """
    given a design, convert a string that indicates the name of a factor to the matching Factor in the design
    """
    # get factor names from design
    for f in design:
        if name == f.name:
            return f
    raise Exception(f'Error while converting {name}: The given factor name is not in the list of Factors')


def _convert_form_name_to_level(name: str, factor: Factor) -> Level:
    """
    given a factor, convert a string that indicates the name of a level to the matching level of the Factor
    """
    if not name:
        return Level('')
    for l in factor.levels:
        if name == l.name:
            return l
    raise Exception(f'Error while converting {name}: The given level name is not a Factor level')


def convert_sample_from_names_to_objects(sample: dict, design: List[Factor]) -> dict:
    """
    given a design, converts a sample formatted in factor names and level names into factor objects and level objects
    """
    new_dict = {}
    for factor_name in sample.keys():
        factor = _convert_from_name_to_factor(factor_name, design)
        value = [_convert_form_name_to_level(level_name, factor) for level_name in sample[factor_name]]
        new_dict[factor] = value
    return new_dict
