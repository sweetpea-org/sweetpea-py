import json
import math
import operator as op

from sweetpea import Factor, DerivedLevel, WithinTrial, NoMoreThanKInARow, fully_cross_block, __approximate_solution_count, __encoding_variable_size, __fully_cross_size, __generate_cnf
from sweetpea.logic import to_cnf_naive, to_cnf_switching, to_cnf_tseitin

SHARPSAT_TIMEOUT = 60 * 60  # 1 hour
SHARPSAT_CACHE_LIMIT_MB = 1024 * 8   # 8 GB

colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet", "black", "white", "gray"]

# Builds a fully_cross_block with the specified number of colors and cnf_fn.
def build_block(num_colors, cnf_fn):
    color_list = colors[:num_colors]
    color = Factor("color", color_list)
    text  = Factor("text",  color_list)

    conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    incLevel  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
    conFactor = Factor("congruent?", [conLevel, incLevel])

    design       = [color, text, conFactor]
    crossing     = [color, text]

    constraints =  [NoMoreThanKInARow(1, ("congruent?", "con"))]
    return fully_cross_block(design, crossing, constraints, cnf_fn)


def get_variables_and_clauses(blk):
    cnf = __generate_cnf(blk)
    header_segments = cnf.split('\n')[0].split(' ')
    variables = int(header_segments[2])
    clauses = int(header_segments[3])
    return (variables, clauses)


data_list = []
for n in range(2, len(colors) + 1):
    print("Gathering data for stroop-" + str(n))

    data = {}
    data['stroop'] = n

    naive_blk = build_block(n, to_cnf_naive)
    data['encoding_variables'] = __encoding_variable_size(naive_blk.design, naive_blk.xing)
    fc_size = __fully_cross_size(naive_blk.xing)
    data['fully_cross_size'] = fc_size
    data['permutations'] = str(int(math.factorial(fc_size)))
    
    if n < 5:
        data['n_sat_naive'] = __approximate_solution_count(naive_blk, SHARPSAT_TIMEOUT, SHARPSAT_CACHE_LIMIT_MB)

        (variables, clauses) = get_variables_and_clauses(naive_blk)
        data['n_variables_naive'] = variables
        data['n_clauses_naive'] = clauses
    else: # Process gets killed when we try to do naive with stroop-5 or more. Probably stack overflow or something.
        data['n_sat_naive'] = 0
        data['n_variables_naive'] = 0
        data['n_clauses_naive'] = 0

    switch_blk = build_block(n, to_cnf_switching)

    if n < 4:
        data['n_sat_switching'] = __approximate_solution_count(switch_blk, SHARPSAT_TIMEOUT, SHARPSAT_CACHE_LIMIT_MB)
    else:
        # Takes too long. (10 hours still can't do it.)
        data['n_sat_switching'] = 0

    (variables, clauses) = get_variables_and_clauses(switch_blk)
    data['n_variables_switching'] = variables
    data['n_clauses_switching'] = clauses

    tseitin_blk = build_block(n, to_cnf_tseitin)
    data['n_sat_tseitin'] = __approximate_solution_count(tseitin_blk, SHARPSAT_TIMEOUT, SHARPSAT_CACHE_LIMIT_MB)

    (variables, clauses) = get_variables_and_clauses(tseitin_blk)
    data['n_variables_tseitin'] = variables
    data['n_clauses_tseitin'] = clauses

    data_list.append(data)

with open('data.json', 'w') as outfile:
    json.dump(data_list, outfile)
