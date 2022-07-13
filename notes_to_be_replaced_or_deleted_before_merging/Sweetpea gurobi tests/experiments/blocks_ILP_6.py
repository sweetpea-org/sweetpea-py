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

sample_count = 100
samples_per = 1000
caching = False
recording = False

def check(original_combos):
    try:
        # Create a new model
        m = gp.Model("mip1")

        # Create variables
        color = m.addMVar(shape=(num_trials,crossing_c), vtype=GRB.BINARY, name="color")
        text = m.addMVar(shape=(num_trials,crossing_t), vtype=GRB.BINARY, name="text")

        cong = m.addMVar(shape=(num_trials,2), vtype=GRB.BINARY, name="cong")
        crossing = m.addMVar(shape=(num_trials,num_trials), vtype=GRB.BINARY, name="crossing")

        blocks = m.addMVar(shape=(valid_combs), vtype=GRB.BINARY, name="block")

        # Set objective
        block_rnd = np.random.gumbel(0, 1, size=(valid_combs))
        block_w = np.array([1]*valid_combs)
        block_G = block_rnd+np.log(block_w)

        m.ModelSense = GRB.MAXIMIZE
        m.setObjectiveN(block_G @ blocks, 0)

        for combo_i, combo in enumerate(original_combos):
            range_t = (range(0, num_trials), list(i[1] for i in combo))
            range_c = (range(0, num_trials), list(i[0] for i in combo))

            m.addConstr(text[range_t].sum()+color[range_c].sum() >= num_trials*2*blocks[combo_i], name="blocks"+str(combo_i))
            m.addConstr(text[range_t].sum()+color[range_c].sum() <= num_trials*2-1+blocks[combo_i], name="blocks"+str(combo_i))

        # Set contraint
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

        blocks_start = num_trials*(crossing_c+crossing_t+2+num_trials)
        for i, v in enumerate(m.getVars()[blocks_start:]):
            if v.x:
                return i

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))

    except AttributeError:
        print('Encountered an attribute error')

combs = []
for i in range(0, crossing_c):
    for j in range(0, crossing_t):
        combs.append((i, j))

original_combos = list(permutations(combs))

for i in range(sample_count):
    start = time.time()
    result = [0]*valid_combs
    for i in range(samples_per):
        result[check(original_combos)]+=1
    end = time.time()

    result = [i for i in result if i != 0]
    res_str = format(end-start)+":"+str(len(result))+":"+str(result)+"\n\n"

    f = open("../data/blocks_ILP_6.txt", "a")
    f.write(res_str)
    f.close()