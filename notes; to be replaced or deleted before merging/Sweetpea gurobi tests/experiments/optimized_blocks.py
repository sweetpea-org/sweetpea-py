from os import close
import time
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.lib.type_check import isrealobj
import scipy.sparse as sp

dict_ind = {}
next_ind = 0

def check_combination(combo):
    try:
        # Create a new model
        m = gp.Model("mip1")

        # Create variables
        color = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="color")
        text = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="text")

        cong = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="cong")
        crossing = m.addMVar(shape=(4,4), vtype=GRB.BINARY, name="crossing")

        for i in range(0,4):
            m.addConstr(color[i][combo[i][0]] == 1, name="color"+str(i+10))
            m.addConstr(text[i][combo[i][1]] == 1, name="text"+str(i+10))

        # # Set contraint
        for i in range(0, 4):
            # consistency
            m.addConstr(color[i][0]+color[i][1] == 1, name="color"+str(i))
            m.addConstr(text[i][0]+text[i][1] == 1, name="text"+str(i))
            m.addConstr(cong[i][0]+cong[i][1] == 1, name="cong"+str(i))

            m.addConstr(cong[i][0] == 0, name="cong"+str(i))

            if i > 0:
                m.addConstr(color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1] >= 4*cong[i][0], name="congruency"+str(i))
                m.addConstr(cong[i][0] + 3 >= color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1], name="congruency"+str(i))

            # fully_cross
            for j in range(0, 4):
                m.addConstr(2*crossing[i][j] <= color[i][int(j/2)%2] + text[i][j%2], name="crossing"+str(i))
                m.addConstr(crossing[i][j] - color[i][int(j/2)%2] - text[i][j%2] >= -1, name="crossing"+str(i))

            m.addConstr(crossing[0][i] + crossing[1][i] + crossing[2][i] + crossing[3][i] >= 1, name="crossing3"+str(i))

        # Optimize model
        m.Params.OutputFlag=0
        m.optimize()

        if m.SolCount == 0:
            return False
        else:
            return True

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))

    except AttributeError:
        print('Encountered an attribute error')


from itertools import permutations

original_combos = list(permutations([(0,0), (0,1), (1,0), (1,1)]))

sample_count = 100
samples = 1000

for sample_c in range(0,sample_count):
    start = time.time()
    result = [0]*24
    for c in range(0, samples):
        block_rnd = np.random.gumbel(0, 1, size=(24))

        combos = [i for _,i in sorted(zip(block_rnd, original_combos))]

        count = 0
        for combo in combos:
            if check_combination(combo):
                result[original_combos.index(combo)] += 1
                break

    result = [i for i in result if i != 0]

    end = time.time()
    res_str = format(end-start)+":"+str(result)+"\n\n"

    f = open("../data/optimized_blocks.txt", "a")
    f.write(res_str)
    f.close()

f = open("../data/unique_results.txt", "a")
for i in original_combos:
    f.write(str(i)+"\n")
f.close()