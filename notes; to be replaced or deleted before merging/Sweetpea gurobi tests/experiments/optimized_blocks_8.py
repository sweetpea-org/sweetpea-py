from os import close
import time
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.lib.type_check import isrealobj
import scipy.sparse as sp
from itertools import permutations
import math

crossing_c = 2
crossing_t = 3
num_trials = crossing_c*crossing_t
valid_combs = math.factorial(num_trials)

sample_count = 1
samples_per = 1000
caching = False
recording = False

def check_combination(combo):
    try:
        # Create a new model
        m = gp.Model("mip1")

        # Create variables
        color = m.addMVar(shape=(num_trials,crossing_c), vtype=GRB.BINARY, name="color")
        text = m.addMVar(shape=(num_trials,crossing_t), vtype=GRB.BINARY, name="text")

        cong = m.addMVar(shape=(num_trials,2), vtype=GRB.BINARY, name="cong")
        crossing = m.addMVar(shape=(num_trials,num_trials), vtype=GRB.BINARY, name="crossing")

        for i in range(0,num_trials):
            m.addConstr(color[i][combo[i][0]] == 1, name="color"+str(i+10))
            m.addConstr(text[i][combo[i][1]] == 1, name="text"+str(i+10))

        # # Set contraint
        for i in range(0, num_trials):
            # consistency
            m.addConstr(color[i, :].sum() == 1, name="row"+str(i))
            m.addConstr(text[i, :].sum() == 1, name="row"+str(i))
            m.addConstr(cong[i, :].sum() == 1, name="row"+str(i))


            if i > 1:
                m.addConstr(color[i-2][1] + text[i-2][2] + color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1] >= 6*cong[i][0], name="congruency"+str(i))
                m.addConstr(cong[i][0] + 5 >= color[i-2][1] + text[i-2][2] + color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1], name="congruency"+str(i))

        m.addConstr(cong[0][0] == 0, name="row"+str(i))
        m.addConstr(cong[1][0] == 0, name="row"+str(i))
        m.addConstr(cong[:, 0].sum() == 1, name="row"+str(i))

        # fully_cross
        for i in range(0, num_trials):
            for j in range(0, num_trials):
                m.addConstr(2*crossing[i][j] <= color[i][int(j/crossing_t)] + text[i][j%crossing_t], name="crossing"+str(i))
                m.addConstr(crossing[i][j] - color[i][int(j/crossing_t)] - text[i][j%crossing_t] >= -1, name="crossing"+str(i))

            # m.addConstr(crossing[0][i] + crossing[1][i] + crossing[2][i] + crossing[3][i] >= 1, name="crossing3"+str(i))
            m.addConstr(crossing[:, i].sum() <= 1, name="row"+str(i))


        # Optimize model
        m.Params.OutputFlag=0
        m.optimize()

        # for v in m.getVars():
        #     print(v)

        if m.SolCount == 0:
            return False
        else:
            return True

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))

    except AttributeError:
        print('Encountered an attribute error')

# check_combination([(0,0),(1,1),(0,1),(1,0),(1,2),(0,2)])

combs = []
for i in range(0, crossing_c):
    for j in range(0, crossing_t):
        combs.append((i, j))

original_combos = list(permutations(combs))

print(len(original_combos))
result_combinations = ""

for sample_count_i in range(0, sample_count):
    start = time.time()
    result = [0]*valid_combs
    valid = set()
    invalid = set()
    for samples_per_i in range(0, samples_per):
        block_rnd = np.random.gumbel(0, 1, size=(valid_combs))

        combos = [i for _,i in sorted(zip(block_rnd, original_combos))]

        count = 0
        for combo in combos:
            if caching:
                if combo in valid:
                    result[original_combos.index(combo)] += 1
                    if recording:
                        result_combinations += str(combo)+"\n"
                    break
                elif combo in invalid:
                    continue
                elif check_combination(combo):
                    result[original_combos.index(combo)] += 1
                    if recording:
                        result_combinations += str(combo)+"\n"
                    break
                else:
                    invalid.add(combo)
            else:
                if check_combination(combo):
                    result[original_combos.index(combo)] += 1
                    if recording:
                        result_combinations += str(combo)+"\n"
                    break

    end = time.time()

    result = [i for i in result if i != 0]
    res_str = format(end-start)+":"+str(len(result))+":"+str(result)+"\n\n"

    f = open("../data/test.txt", "a")
    f.write(res_str)
    f.close()

if recording:
    f = open("../data/unique_results.txt", "a")
    f.write(result_combinations + "\n")
    f.close()