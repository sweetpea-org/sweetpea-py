"""
Here, we have a mini-block design where congruency of the words
is counterbalanced within each mini-block and the task switch frequency
between mini-blocks is balanced.
"""

import sweetpea as sp


def main():
    # **** Mini-block balancing (within mini-block counterbalancing) **** #

    color = sp.Factor(name='color', initial_levels=['red', 'green', 'blue', 'yellow'])
    word = sp.Factor(name='word', initial_levels=['RED', 'GREEN', 'BLUE', 'YELLOW'])

    def is_congruent(_color, _word):
        return _color.lower() == _word.lower()
    is_incongruent = lambda _color, _word: not is_congruent(_color, _word)

    congruent = sp.DerivedLevel(name='congruent', window=sp.WithinTrial(is_congruent, [color, word]))
    incongruent = sp.DerivedLevel(name='incongruent', window=sp.WithinTrial(is_incongruent, [color, word]))
    congruency = sp.Factor(name='congruency', initial_levels=[congruent, incongruent])

    mb_design = [color, word, congruency]
    mb_crossing = [color, congruency]
    mini_block = sp.CrossBlock(design=mb_design, crossing=mb_crossing, constraints=[])

    _mb_exp = sp.synthesize_trials(mini_block, 1, sp.CMSGen)
    sp.print_experiments(mini_block, _mb_exp)

    # **** Nesting the mini blocks **** #
    # Counterbalance (1) word-naming vs color-naming blocks and
    # (2) blocks where the task switches vs repeats.

    task = sp.Factor(name='task', initial_levels=['word_naming', 'color_naming'])

    def is_repeat(_task):
        return _task[-1] == _task[0]
    is_switch = lambda x: not is_repeat(x)

    repeat = sp.DerivedLevel(name='repeat_block', window=sp.Transition(is_repeat, [task]))
    switch = sp.DerivedLevel(name='switch_block', window=sp.Transition(is_switch, [task]))
    task_transition = sp.Factor(name='task_transition', initial_levels=[repeat, switch])

    # The outer block counterbalances task and task transitions; `Nest` holds
    # each outer combination constant for one whole instance of `mini_block`.
    outer = sp.CrossBlock(design=[task, task_transition],
                          crossing=[task, task_transition],
                          constraints=[])
    block = sp.Nest(outer_block=outer,
                    inner_block=mini_block,
                    constraints=[],
                    alignment=sp.AlignmentMode.POST_PREAMBLE)

    experiments = sp.synthesize_trials(block, 1, sp.CMSGen)
    sp.print_experiments(block, experiments)

    return


if __name__ == '__main__':
    main()
