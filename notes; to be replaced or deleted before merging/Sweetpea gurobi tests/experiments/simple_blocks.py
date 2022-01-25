from os import close
import time
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.lib.type_check import isrealobj
import scipy.sparse as sp

dict_ind = {}
next_ind = 0

try:
    sample_size = 2
    count_size = 100
    while sample_size > 0:
        sample_size -= 1
        # Create a new model
        start = time.time()
        results = [0]*next_ind
        count = 0
        while count < count_size:
            count+=1
            m = gp.Model("mip1")

            # Create variables
            color = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="color")
            text = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="text")

            cong = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="cong")
            blocks = m.addMVar(shape=(24), vtype=GRB.BINARY, name="text")

            crossing = m.addMVar(shape=(4,4), vtype=GRB.BINARY, name="crossing")

            # Set objective
            block_rnd = np.random.gumbel(0, 1, size=(24))
            block_w = np.array([1]*24)
            block_G = block_rnd+np.log(block_w)

            m.ModelSense = GRB.MAXIMIZE
            m.setObjectiveN(block_G @ blocks, 0)

            def func(avail, selected, num, m, blocks, text, color):
                if not avail:
                    # contstr
                    m.addConstr(text[0][selected[0][0]]+text[1][selected[1][0]]+text[2][selected[2][0]]+text[3][selected[3][0]] \
                    +color[0][selected[0][1]]+color[1][selected[1][1]]+color[2][selected[2][1]]+color[3][selected[3][1]] \
                     >= 8*blocks[num], name="blocks"+str(num))
                    m.addConstr(blocks[num]+7 >=
                    text[0][selected[0][0]]+text[1][selected[1][0]]+text[2][selected[2][0]]+text[3][selected[3][0]]
                    +color[0][selected[0][1]]+color[1][selected[1][1]]+color[2][selected[2][1]]+color[3][selected[3][1]], name="blocks1"+str(num))
                    return
                f = np.math.factorial(len(avail)-1)
                for ind, i in enumerate(avail):
                    func(avail[:ind] + avail[ind+1:], selected+[i], num+f*ind, m, blocks, text, color)

            func([(0,0), (0,1), (1,0), (1,1)], [], 0, m, blocks, text, color)

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

            count_1 = 0
            while count_1 < 1:
                m.Params.SolutionNumber=count_1
                count_1+=1
                sum = 0
                for v in m.getVars():
                    sum += v.x

                v = m.getVars()

                curr_res = ""
                for i in range(0,4):
                    c = -1
                    t = -1
                    con = None
                    for j in range(0, 2):
                        sum = 0
                        if (v[sum+i*2+j].x):
                            c = j
                        sum+=8
                        if (v[sum+i*2+j].x):
                            t = j
                        sum+=8
                        if j < 2:
                            if (v[sum+i*2+j].x):
                                if j:
                                    con = False
                                else:
                                    con = True
                        sum+=8
                    # print("color\t", c, "|text\t", t, "|cong\t", con)
                    curr_res+=str(c)
                    curr_res+=str(t)
                    curr_res+=str(con)
                if curr_res not in dict_ind:
                    dict_ind[curr_res] = next_ind
                    next_ind+=1
                if next_ind > len(results):
                    results.append(0)
                results[dict_ind[curr_res]] += 1

        end = time.time()
        res_str = format(end-start)+": ["

        for i in results:
            res_str += str(i) + ", "
        res_str+="]\n\n"

        f = open("../data/optimized_blocks.txt", "a")
        f.write(res_str)
        f.close()

    res_str = ""
    for i, j in enumerate(dict_ind):
        res_str += str(i) + ":\t" + str(j) + "\n"

    f = open("../data/unique_results.txt", "a")
    f.write(res_str)
    f.close()

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
