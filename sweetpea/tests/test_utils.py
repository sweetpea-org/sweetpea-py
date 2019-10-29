from sweetpea.primitives import Factor, DerivedLevel, SimpleLevel


def get_level_from_name(factor, name):
    for level in factor.levels:
        if level.external_name == name:
            return level
    return None
