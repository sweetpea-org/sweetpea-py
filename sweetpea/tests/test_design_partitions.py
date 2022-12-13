import operator as op
import pytest

from sweetpea import CrossBlock
from sweetpea._internal.primitive import Factor, DerivedLevel, WithinTrial
from sweetpea._internal.design_partition import DesignPartitions
from sweetpea._internal.constraint import Reify


color      = Factor("color",      ["red", "blue"])
text       = Factor("text",       ["red", "blue"])
congruency = Factor("congruency", [
    DerivedLevel("congruent",   WithinTrial(op.eq, [color, text])),
    DerivedLevel("incongruent", WithinTrial(op.ne, [color, text]))
])
color_red  = Factor("color red", [
    DerivedLevel("yes", WithinTrial(lambda c: c == "red", [color])),
    DerivedLevel("no",  WithinTrial(lambda c: c != "red", [color]))
])

design   = [color, text, congruency, color_red]
crossing = [color, congruency]
block    = CrossBlock(design, crossing, list(map(Reify, design)))

def test_get_crossed_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_crossed_noncomplex_factors() == crossing


def test_get_crossed_factors_derived():
    partitions = DesignPartitions(block)
    assert partitions.get_crossed_noncomplex_derived_factors() == [congruency]


def test_get_uncrossed_basic_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_factors() == [text]


def test_get_uncrossed_basic_source_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_source_factors() == [text]


def test_get_uncrossed_basic_independent_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_basic_independent_factors() == []


def test_get_uncrossed_derived_factors():
    partitions = DesignPartitions(block)
    assert partitions.get_uncrossed_derived_and_complex_derived_factors() == [color_red]


