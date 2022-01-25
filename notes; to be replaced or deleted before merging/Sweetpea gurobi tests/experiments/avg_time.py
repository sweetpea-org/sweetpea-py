from os import close
import time
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.lib.type_check import isrealobj
import scipy.sparse as sp
from itertools import permutations
import math

for c_t in range(2,100):
    crossing_c = 2
    crossing_t = c_t
    num_trials = crossing_c*crossing_t
    valid_combs = math.factorial(num_trials)

    sample_count = 1
    samples_per = 1
    caching = True
    recording = False

    def check_combination(combo):
        try:
            # Create a new model
            m = gp.Model("mip1")

            # Create variables
            color = m.addMVar(shape=(num_trials,crossing_c), vtype=GRB.BINARY, name="color")
            text = m.addMVar(shape=(num_trials,crossing_t), vtype=GRB.BINARY, name="text")

            crossing = m.addMVar(shape=(num_trials,num_trials), vtype=GRB.BINARY, name="crossing")

            for i in range(0,num_trials):
                m.addConstr(color[i][combo[i][0]] == 1, name="color"+str(i+10))
                m.addConstr(text[i][combo[i][1]] == 1, name="text"+str(i+10))

            # Set contraint
            for i in range(0, num_trials):
                # consistency
                m.addConstr(color[i, :].sum() == 1, name="row"+str(i))
                m.addConstr(text[i, :].sum() == 1, name="row"+str(i))

            # fully_cross
            for i in range(0, num_trials):
                for j in range(0, num_trials):
                    m.addConstr(2*crossing[i][j] <= color[i][int(j/crossing_t)] + text[i][j%crossing_t], name="crossing"+str(i))
                    m.addConstr(crossing[i][j] - color[i][int(j/crossing_t)] - text[i][j%crossing_t] >= -1, name="crossing"+str(i))

                m.addConstr(crossing[:, i].sum() <= 1, name="row"+str(i))

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

    combs = []
    for i in range(0, crossing_c):
        for j in range(0, crossing_t):
            combs.append((i, j))

    for sample_count_i in range(0, sample_count):
        rng = np.random.default_rng()
        start = time.time()

        while True:
            if check_combination(rng.permutation(combs)):
                break

        end = time.time()
        res_str = str(num_trials) + ":" + format(end-start) + "\n\n"

        f = open("../data/avg_time.txt", "a")
        f.write(res_str)
        f.close()

    if recording:
        f = open("../data/unique_results.txt", "a")
        f.write(result_combinations + "\n")
        f.close()