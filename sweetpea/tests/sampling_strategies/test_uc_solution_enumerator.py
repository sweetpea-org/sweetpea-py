import operator as op

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.sampling_strategies.uniform_combinatoric import UCSolutionEnumerator


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

crossing = [color, text]
design = [color, text]
block = fully_cross_block(design, crossing, [])


def test_generate_crossing_instances():
    enumerator = UCSolutionEnumerator(block)

    assert enumerator._UCSolutionEnumerator__generate_crossing_instances() == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]


def test_generate_source_combinations():
    block = fully_cross_block(design, [congruency], [])
    enumerator = UCSolutionEnumerator(block)

    assert enumerator._UCSolutionEnumerator__get_source_combinations() == [
        {'color': 'red', 'text': 'red'},
        {'color': 'red', 'text': 'blue'},
        {'color': 'blue', 'text': 'red'},
        {'color': 'blue', 'text': 'blue'}
    ]
