import time
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.lib.type_check import isrealobj
import scipy.sparse as sp

start = time.time()

try:

    # Create a new model
    results = {}
    count = 0
    while count < 100:
        count+=1
        m = gp.Model("mip1")

        # Create variables
        color = m.addMVar(shape=(33,4), vtype=GRB.BINARY, name="color")
        text = m.addMVar(shape=(33,4), vtype=GRB.BINARY, name="text")

        cong = m.addMVar(shape=(33, 2), vtype=GRB.BINARY, name="cong")
        resp = m.addMVar(shape=(33,4), vtype=GRB.BINARY, name="resp")
        resp_trans = m.addMVar(shape=(33,2), vtype=GRB.BINARY, name="resp_trans")
        resp_trans_state = m.addMVar(shape=(33,4), vtype=GRB.BINARY, name="resp_trans_state")
        color_text = m.addMVar(shape=(33,4), vtype=GRB.BINARY, name="color_text")

        crossing = m.addMVar(shape=(33,32), vtype=GRB.BINARY, name="crossing")
        # Set objective
        color_rnd = np.random.gumbel(0, 1, size=(33,4))
        text_rnd = np.random.gumbel(0, 1, size=(33,4))

        color_w = np.array([[1]*4]*33)
        text_w = np.array([[1]*4]*33)

        color_G = color_rnd+np.log(color_w)
        text_G = text_rnd+np.log(text_w)

        m.ModelSense = GRB.MAXIMIZE

        obj_ind = 0
        for i in range(0, 33):
            m.setObjectiveN(color_G[i] @ color[i], obj_ind)
            m.setObjectiveN(text_G[i] @ text[i], obj_ind+1)
            obj_ind+=2

        # # Set contraint
        for i in range(0, 33):
            # consistency
            m.addConstr(color[i][0]+color[i][1]+color[i][2]+color[i][3] == 1, name="color"+str(i))
            m.addConstr(text[i][0]+text[i][1]+text[i][2]+text[i][3] == 1, name="text"+str(i))
            m.addConstr(resp[i][0]+resp[i][1]+resp[i][2]+resp[i][3] == 1, name="resp"+str(i))

            m.addConstr(cong[i][0]+cong[i][1] == 1, name="cong"+str(i))
            m.addConstr(resp_trans[i][0]+resp_trans[i][1] == 1, name="resp_trans"+str(i))

            for j in range(0, 4):
                # congruency
                m.addConstr(2*color_text[i][j] <= color[i][j] + text[i][j], name="color_text"+str(i))
                m.addConstr(color_text[i][j] - color[i][j] - text[i][j] >= -1, name="color_text2"+str(i))

            m.addConstr(color_text[i][0]+color_text[i][1]+color_text[i][2]+color_text[i][3] >= cong[i][0], name="congruency"+str(i))
            m.addConstr(color_text[i][0]+color_text[i][1]+color_text[i][2]+color_text[i][3] <= 4*cong[i][0], name="congruency"+str(i))

            # fully_cross
            for j in range(0, 32):
                # print(j, int(j/16), int(j/4)%4, j%4)
                m.addConstr(3*crossing[i][j] <= color[i][int(j/4)%4] + text[i][j%4] + resp_trans[i][int(j/16)], name="crossing"+str(i))
                m.addConstr(crossing[i][j] - color[i][int(j/4)%4] - text[i][j%4] - resp_trans[i][int(j/16)] >= -2, name="crossing"+str(i))

            if i < 32:
                m.addConstr(crossing[0][i] + crossing[1][i] + crossing[2][i] + crossing[3][i] + crossing[4][i] + crossing[5][i] + crossing[6][i] + crossing[7][i]
                + crossing[8][i] + crossing[9][i] + crossing[10][i] + crossing[11][i] + crossing[12][i] + crossing[13][i] + crossing[14][i] + crossing[15][i]
                + crossing[16][i] + crossing[17][i] + crossing[18][i] + crossing[19][i] + crossing[20][i] + crossing[21][i] + crossing[22][i] + crossing[23][i]
                + crossing[24][i] + crossing[25][i] + crossing[26][i] + crossing[27][i] + crossing[28][i] + crossing[29][i] + crossing[30][i] + crossing[31][i] + crossing[32][i] >= 1, name="crossing3"+str(i))


            # response factor
            for j in range(0, 4):
                m.addConstr(resp[i][j] == color[i][j], name="resp-const"+str(i))

            if i:
                for j in range(0, 4):
                    m.addConstr(2*resp_trans_state[i][j] <= resp[i-1][j] + resp[i][j], name="resp_trans_state"+str(i))
                    m.addConstr(resp_trans_state[i][j] - resp[i-1][j] - resp[i][j] >= -1, name="resp_trans_state2"+str(i))

                m.addConstr(resp_trans_state[i][0]+resp_trans_state[i][1]+resp_trans_state[i][2]+resp_trans_state[i][3] >= resp_trans[i][0], name="resp_trans"+str(i))
                m.addConstr(resp_trans_state[i][0]+resp_trans_state[i][1]+resp_trans_state[i][2]+resp_trans_state[i][3] <= 4*resp_trans[i][0], name="resp_trans"+str(i))

        # Set to find multiple solutions
        # m.Params.PoolSearchMode=2
        # m.Params.PoolSolutions=100

        # Optimize model
        m.optimize()

        sum = 0
        for v in m.getVars():
            # print('%s %g' % (v.varName, v.x))
            sum += v.x

        v = m.getVars()

        # print("-----------------------------------------------------------------------------------------------")
        curr_res = ""
        for i in range(0,33):
            c = -1
            t = -1
            con = None
            res = -1
            res_trans = None
            for j in range(0, 4):
                sum = 0
                if (v[sum+i*4+j].x):
                    c = j
                sum+=132
                if (v[sum+i*4+j].x):
                    t = j
                sum+=132
                if j < 2:
                    if (v[sum+i*2+j].x):
                        if j:
                            con = False
                        else:
                            con = True
                sum+=66
                if (v[sum+i*4+j].x):
                    res = j
                sum+=132
                if j < 2:
                    if (v[sum+i*2+j].x):
                        if j:
                            res_trans = False
                        else:
                            res_trans = True
                sum+=66
            # print("color\t", c, "|text\t", t, "|cong\t", con, "\t|resp\t", res, "\t|resp_trans\t", res_trans)
            curr_res+=str(c)
            curr_res+=str(t)
            curr_res+=str(con)
            curr_res+=str(res)
            curr_res+=str(res_trans)
        if curr_res in results:
            results[curr_res] += 1
        else:
            results[curr_res] = 1

    print(results, "\n")

    for i in results:
        print(results[i])

    end = time.time()

    print("Time: ", format(end-start))

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
