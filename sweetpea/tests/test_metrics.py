import pytest

from typing import List

from sweetpea.blocks import Block
from sweetpea.constraints import AtMostKInARow
from sweetpea.metrics import __count_solutions
from sweetpea.primitives import Factor
from sweetpea import fully_cross_block


color_list = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
direction_list = ["up", "down", "left", "right", "stuck"]


def __build_stroop_design(color_count: int) -> List[Factor]:
    color = Factor("color", color_list[:color_count])
    text = Factor("text", color_list[:color_count])

    return [color, text]

def __build_stroop_block(color_count: int) -> Block:
    design = __build_stroop_design(color_count)

    return fully_cross_block(design, design, [])


@pytest.mark.parametrize('color_count,solution_count', [
    (2, 24),
    (3, 362880),
    (4, 20922789888000),
    (5, 15511210043330985984000000),
    (6, 371993326789901217467999448150835200000000),
    (7, 608281864034267560872252163321295376887552831379210240000000000)
])
def test_correct_solution_count_for_basic_stroops(color_count, solution_count):
    blk = __build_stroop_block(color_count)

    assert __count_solutions(blk) == solution_count


def __build_stroop_blk_with_direction(color_count: int, direction_count: int) -> Block:
    color = Factor("color", color_list[:color_count])
    text = Factor("text", color_list[:color_count])
    direction = Factor("direction", direction_list[:direction_count])

    design = [color, text, direction]
    crossing = [color, text]

    return fully_cross_block(design, crossing, [])


@pytest.mark.parametrize('color_count,direction_count,solution_count', [
    (2, 2, 384),
    (3, 2, 185794560),
    (4, 2, 1371195958099968000),
    (2, 3, 1944),
    (2, 4, 6144),
    (3, 5, 708750000000)
])
def test_correct_solution_count_with_uncrossed_factor(color_count, direction_count, solution_count):
    blk = __build_stroop_blk_with_direction(color_count, direction_count)

    assert __count_solutions(blk) == solution_count


@pytest.mark.skip
@pytest.mark.parametrize('color_count,solution_count', [
    (2, 12),
    (3, 151200)
])
def test_correct_solution_count_with_single_constraint(color_count, solution_count):
    design = __build_stroop_design(color_count)
    blk = fully_cross_block(design, design, [AtMostKInARow(1, ("color", "red"))])

    assert __count_solutions(blk) == solution_count
