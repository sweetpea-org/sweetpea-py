from pulp import *

prob = LpProblem("2*2")

# init
crossing_c = 2
crossing_t = 2
num_trials = crossing_c*crossing_t

row_c = range(0, crossing_c)
row_t = range(0, crossing_t)
num_trials = range(0, num_trials)

# variables
color = LpVariable.dicts("Color", (row_c, num_trials), cat="Binary")
text = LpVariable.dicts("Text", (row_t, num_trials), cat="Binary")

crossing = LpVariable.dicts("Crossing", (num_trials, num_trials), cat="Binary")

# consistency
for n in num_trials:
    prob += lpSum([color[r][n] for r in row_c]) == 1
for n in num_trials:
    prob += lpSum([text[r][n] for r in row_t]) == 1

# complete crossing
for i in num_trials:
    for j in num_trials:
        prob += 2*crossing[i][j] <= color[int(j/crossing_t)][i] + text[j%crossing_t][i]
        prob += crossing[i][j] - color[int(j/crossing_t)][i] - text[j%crossing_t][i] >= -1

    prob += lpSum([crossing[n][i] for n in num_trials]) == 1

prob.writeLP("2*2_pulp.lp")

prob.solve()

print("Status: ", LpStatus[prob.status])

for n in num_trials:
    print(n)
    # for r in row_c:
    #     print(n, "\tColor_",r,":\t", value(color[r][n]), "\tText_",r,"\t", value(text[r][n]))
    for r in row_c:
        if value(color[r][n]) == 1:
            print("\tColor: ", r)
    for r in row_t:
        if value(text[r][n]) == 1:
            print("\tText: ", r)

prob.writeLP("2*2_pulp.lp")
