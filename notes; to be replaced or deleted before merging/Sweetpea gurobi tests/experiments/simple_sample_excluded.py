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
    sample_size = 100
    count_size = 1000
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

            cong = m.addMVar(shape=(4, 2), vtype=GRB.BINARY, name="cong")
            color_text = m.addMVar(shape=(4,2), vtype=GRB.BINARY, name="color_text")

            crossing = m.addMVar(shape=(4,4), vtype=GRB.BINARY, name="crossing")
            # Set objective
            color_rnd = np.random.gumbel(0, 1, size=(4,2))
            text_rnd = np.random.gumbel(0, 1, size=(4,2))

            color_w = np.array([[1]*2]*4)
            text_w = np.array([[1]*2]*4)

            color_G = color_rnd+np.log(color_w)
            text_G = text_rnd+np.log(text_w)

            m.ModelSense = GRB.MAXIMIZE

            obj_ind = 0
            for i in range(0, 4):
                m.setObjectiveN(color_G[i] @ color[i], obj_ind)
                m.setObjectiveN(text_G[i] @ text[i], obj_ind+1)
                obj_ind+=2

            # for i in range(1, 4):
            #     m.addConstr(color[i-1][1] + text[i-1][1] + color[i][0] + text[i][0]  <= 3, name="color"+str(i))

            # correct
            # for i in range(1, 4):
            #     m.addConstr(color[i-1][1] + text[i-1][1] + color[i][0] + text[i][0]  >= 1, name="color"+str(i))

            # # Set contraint
            for i in range(0, 4):
                # consistency
                m.addConstr(color[i][0]+color[i][1] == 1, name="color"+str(i))
                m.addConstr(text[i][0]+text[i][1] == 1, name="text"+str(i))
                m.addConstr(cong[i][0]+cong[i][1] == 1, name="cong"+str(i))

                m.addConstr(cong[i][0] == 0, name="cong"+str(i))
                # for j in range(0, 2):
                #     # congruency
                #     m.addConstr(2*color_text[i][j] <= color[i][j] + text[i][j], name="color_text"+str(i))
                #     m.addConstr(color_text[i][j] - color[i][j] - text[i][j] >= -1, name="color_text2"+str(i))

                # m.addConstr(color_text[i][0]+color_text[i][1] >= cong[i][0], name="congruency"+str(i))
                # m.addConstr(color_text[i][0]+color_text[i][1] <= 2*cong[i][0], name="congruency"+str(i))

                if i > 0:
                    m.addConstr(color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1] >= 4*cong[i][0], name="congruency"+str(i))
                    m.addConstr(cong[i][0] + 3 >= color[i-1][0] + text[i-1][0] + color[i][1] + text[i][1], name="congruency"+str(i))

                # fully_cross
                for j in range(0, 4):
                    m.addConstr(2*crossing[i][j] <= color[i][int(j/2)%2] + text[i][j%2], name="crossing"+str(i))
                    m.addConstr(crossing[i][j] - color[i][int(j/2)%2] - text[i][j%2] >= -1, name="crossing"+str(i))

                m.addConstr(crossing[0][i] + crossing[1][i] + crossing[2][i] + crossing[3][i] >= 1, name="crossing3"+str(i))

            # Optimize model
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

        f = open("simple_sample_excluded_exact_data1.py", "a")
        f.write(res_str)
        f.close()

    res_str = ""
    for i, j in enumerate(dict_ind):
        res_str += str(i) + ":\t" + str(j) + "\n"

    f = open("simple_sample_excluded_exact_data1.py", "a")
    f.write(res_str)
    f.close()

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
