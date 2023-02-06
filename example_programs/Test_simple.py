from sweetpea import synthesize_trials, print_experiments, save_experiments_csv, CrossBlock, \
    MultiCrossBlock, Factor, DerivedLevel, WithinTrial, Transition, MinimumTrials, Exclude, sample_mismatch_experiment

target_side_list = ['R', 'L']
target_side = Factor(name='target side', initial_levels=target_side_list)
trial_constraints = MinimumTrials(trials=50)
design = [target_side]
crossing = [target_side]
constraints = [trial_constraints]
block = CrossBlock(design, crossing, constraints)

sequence = {'target side': ['L', 'L', 'L', 'R', 'R', 'R']}

print(sample_mismatch_experiment(block, sequence))





