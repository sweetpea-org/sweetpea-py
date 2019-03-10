import operator as op
import pytest

from sweetpea import fully_cross_block
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial
from sweetpea.design_partitions import DesignPartitions


color      = Factor("color",      ["red", "blue"])
text       = Factor("text",       ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])

design   = [color, text, congruency]
crossing = [color, congruency]
block    = fully_cross_block(design, crossing, [])


def test_get_crossed_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_crossed_factors() == crossing


def test_get_crossed_factors_derived():
    partitions = DesignPartitions(block)
    assert partitions.get_crossed_factors_derived() == [congruency]


def test_get_uncrossed_basic_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_factors() == [text]


def test_get_uncrossed_basic_source_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_source_factors() == [text]


def test_get_uncrossed_basic_independent_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_independent_factors() == []


