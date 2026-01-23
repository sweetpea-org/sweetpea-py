"""
Here, we have mini-block design where congruency of the words
is counterbalanced within each mini-block and the task switch frequency
between mini-blocks is balanced
"""


import sweetpea as sp


def main():
    # **** Mini-block balancing (within mini-block counterbalancing) **** #
    # Here we balance the appearance of congruent and incongruent trials in each mini block

    # ** Regular Factors ** #
    color = sp.Factor(name='color', initial_levels=['red', 'green', 'blue', 'yellow'])
    word = sp.Factor(name='word', initial_levels=['RED', 'GREEN', 'BLUE', 'YELLOW'])

    # ** Derived Factors ** #

    # * Congruency * #

    # predicates
    def is_congruent(_color, _word):
        return _color.lower() == _word.lower()
    is_incongruent = lambda _color, _word: not is_congruent(_color, _word)

    # levels
    congruent = sp.DerivedLevel(name='congruent', window=sp.WithinTrial(is_congruent, [color, word]))
    incongruent = sp.DerivedLevel(name='incongruent', window=sp.WithinTrial(is_incongruent, [color, word]))

    # factor
    congruency = sp.Factor(name='congruency', initial_levels=[congruent, incongruent])

    # ** Experimental design ** #
    mb_design = [color, word, congruency]
    mb_crossing = [color, congruency]#, [word]]
    mini_block = sp.CrossBlock(design=mb_design, crossing=mb_crossing, constraints=[])


    _mb_exp = sp.synthesize_trials(mini_block, 1, sp.CMSGen)
    sp.print_experiments(mini_block, _mb_exp)

    # **** Nesting the mini blocks **** #
    # Here, we nest the mini blocks into blocks of tasks and counterbalance:
    #   (1) The number of blocks where the task is `word naming` and `color naming`
    #   (2) The number blocks where the task switches from the previous block versus repeats

    # ** Regular Factors ** #
    task = sp.Factor(name='task', initial_levels=['word_naming', 'color_naming'])
    
    # predicates
    def is_repeat(_task):
        return _task[-1] == _task[0]
    is_switch = lambda x : not is_repeat(x)

    # levels
    repeat = sp.DerivedLevel(name='repeat_block', window=sp.Transition(is_repeat, [task]))
    switch = sp.DerivedLevel(name='switch_block', window=sp.Transition(is_switch, [task]))

    # factor
    task_transition = sp.Factor(name='task_transition', initial_levels=[repeat, switch])

    # ** Experimental design ** #
    design = [task, task_transition, mini_block]
    crossing = [task, task_transition]

    block = sp.NestedBlock(design=design, crossing=crossing, constraints=[])


    experiments = sp.synthesize_trials(block, 1, sp.CMSGen)
    sp.print_experiments(block, experiments)

    
    size       = sp. Factor("size",  ["large", "small"])
    color      = sp.Factor("color", ["red", "blue"]) 
    design       = [size, color]
    crossing     = [size, color]
    block        = sp.CrossBlock(design, crossing, [])

    task = sp.Factor(name='task', initial_levels=['word_naming', 'color_naming'])
    
    # predicates
    def is_repeat(_task):
        return _task[-1] == _task[0]
    is_switch = lambda x : not is_repeat(x)

    # levels
    repeat = sp.DerivedLevel(name='repeat_block', window=sp.Transition(is_repeat, [task]))
    switch = sp.DerivedLevel(name='switch_block', window=sp.Transition(is_switch, [task]))

    task_transition = sp.Factor(name='task_transition', initial_levels=[repeat, switch])

    nested_design = [task, task_transition, block]
    nested_cross = [task, task_transition, block]
    permuted_block2 = sp.NestedBlock(nested_design, nested_cross, [])

    experiments  = sp.synthesize_trials(permuted_block2, 1)#, CMSGen)
    sp.print_experiments(permuted_block2, experiments)

    return

if __name__ == '__main__':
    main()
