from itertools import repeat
from functools import reduce

from sweetpea.primitives import get_external_level_name
from sweetpea.internal import get_all_external_level_names
from sweetpea.blocks import Block


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
def print_encoding_diagram(blk: Block) -> None:
    print(__generate_encoding_diagram(blk))


def __generate_encoding_diagram(blk: Block) -> str:
    diagram_str = ""

    design_size = blk.variables_per_trial()
    num_trials = blk.trials_per_sample()
    num_vars = blk.variables_per_sample()

    largest_number_len = len(str(num_vars))

    header_widths = []
    row_format_str = '| {:>7} |'
    for f in blk.design:
        # length of all levels concatenated for this factor
        level_names = list(map(get_external_level_name, f.levels))
        level_name_widths = [max(largest_number_len, l) for l in list(map(len, level_names))]

        level_names_width = sum(level_name_widths) + len(level_names) - 1 # Extra length for spaces in between names.
        factor_header_width = max(len(f.factor_name), level_names_width)
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
    factor_names = list(map(lambda f: f.factor_name, blk.design))
    header_str = header_format_str.format(*["Trial"] + factor_names)
    row_width = len(header_str)

    # First line
    diagram_str += ('-' * row_width) + '\n'

    # Header
    diagram_str += header_str + '\n'

    # Level names
    all_level_names = [ln for (fn, ln) in get_all_external_level_names(blk.design)]
    diagram_str += row_format_str.format(*['#'] + all_level_names) + '\n'

    # Separator
    diagram_str += ('-' * row_width) + '\n'

    # Variables
    for t in range(num_trials):
        args = [str(t + 1)]
        for f in blk.design:
            if f.applies_to_trial(t + 1):
                variables = [blk.first_variable_for_level(f, l) + 1 for l in f.levels]
                if f.has_complex_window():
                    def acc_width(w) -> int:
                        return w.width + (acc_width(w.args[0].levels[0].window)-1 if w.args[0].has_complex_window() else 0)
                    width = acc_width(f.levels[0].window)
                    stride = f.levels[0].window.stride
                    stride_offset = (stride - 1) * int(t / stride)
                    offset = t - width + 1 - stride_offset
                    variables = list(map(lambda n: n + len(variables) * offset, variables))
                else:
                    variables = list(map(lambda n: n + design_size * t, variables))

                args += list(map(str, variables))
            else:
                args += list(repeat('', len(f.levels)))

        diagram_str += row_format_str.format(*args) + '\n'

    # Footer
    diagram_str += ('-' * row_width) + '\n'
    return diagram_str


def __number_of_columns(block: Block):
    return sum([len(factor.levels) for factor in block.design])
