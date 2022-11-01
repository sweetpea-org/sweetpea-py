from email.mime import application
from mimetypes import init
from time import time
from pulp import *

from sympy.stats import UniformSum, sample
import numpy as np
import gurobipy as gp

# class RandomPermutation(object):
#     def __init__(self, row_values, num_trials):
#         self.used_permutations = set()
#         self.row_values = np.array(row_values)
#         self.num_trials = num_trials
    
#     def next(self):
#         rnd_indices = np.random.choice(len(self.row_values), self.num_trials, replace=False)
#         p = self.row_values[rnd_indices]
#         while str(rnd_indices) in self.used_permutations:
#             rnd_indices = np.random.choice(len(self.row_values), self.num_trials, replace=False)
#             p = self.row_values[rnd_indices]
#         self.used_permutations.add(str(rnd_indices))
#         return list(p)

# def GenerateCrossings(simple_factors, num_trials):
#     row_values = [[x] for x in range(simple_factors[0][1])]
#     for j in range(1, len(simple_factors)):
#         row_values = [x + [y] for x in row_values for y in range(simple_factors[j][1])]

#     factor_values = RandomPermutation(row_values, num_trials)

#     # for i in row_trials:
#     #     if not factor_values:
#     #         factor_values = row_values
#     #     else:
#     #         factor_values = [x + y for x in factor_values for y in row_values]
#     return factor_values

# def SolveP(prob, e, simple_factors):
#     num_trials = len(e)
#     for n in range(num_trials):
#         row = list(e[n])
#         for l in range(len(row)):
#             factor = simple_factors[l][0]
#             prob += factor[row[l]][n] == 1
    
#     prob.solve(PULP_CBC_CMD(msg=0))

#     status = LpStatus[prob.status]
#     if status == 'Infeasible':
#         return False
#     return True

# def SampleExperiment(prob, crossings, simple_factors):
#     e = crossings.next()
#     solution = False
#     while not solution:
#         temp_prob = prob.copy()
#         solution = SolveP(temp_prob, e, simple_factors)
#         if solution:
#             prob = temp_prob.copy() 
#             return prob

#     # no crossing is valid!
#     raise Exception()

# Notes from meeting:
#
# rejection sampling
# (1) no repeats and achieves every solution
# (2) might be 2^n at worst
#
# unit tests
# 1 factor 4 levels (each experiment 1/4 of time)
# 1 factor 4 levels + constraint (no level 0) (each experiment 1/3)
# 1 factor 2 trials + constraint (never repeats) (each experiment 1/12 since 16 - 4)


# Consistency constraint
#   prob = lpProblem
#   input_factor = lpVariable being constrained
#   row_levels = number of levels in range form (e.g. range(num_c)))
#   row_trials = number of trials in range form (e.g. range(num_trials)))
#
# e.g. Consistency(prob, color, row_c, row_trials)
def Consistency(prob, input_factor, num_levels, num_trials, is_complex = False, applicable_trials = []):
    row_levels = range(num_levels)
    if not is_complex:
        for n in range(num_trials):
            prob += lpSum([input_factor[r][n] for r in row_levels]) == 1
    else:
        if not applicable_trials:
            applicable_trials = range(num_trials)
        for n in applicable_trials:
            prob += lpSum([input_factor[r][n] for r in row_levels]) == 1

# Fully cross constraint
#   prob = lpProblem
#   input_factors = lpVariables being crossed
#   num_factors = number of levels in each factor
#   row_trials = number of trials in range form (e.g. range(num_trials)))
#
# e.g. FullyCross
def FullyCross(prob, crossing, input_factors, num_trials, is_complex = False, applicable_trials = []):
    factor_count = len(input_factors)
    row_trials = range(num_trials) if not is_complex else applicable_trials
    for i in row_trials:
        current_levels = factor_count * [0]
        for j in row_trials:
            #   General AND(n amount of variables 1) -> AND(m amount of variables 2):
            #       -m(sum of variables 1) + (sum of variables 2) >= m(1 - n)
            sum_of_input_factors = lpSum([input_factors[r][0][current_levels[r]][i] for r in range(factor_count)])
            # input factors (n) imply crossing (m = 1)
            prob += -sum_of_input_factors + crossing[i][j] >= 1 - factor_count
            # crossing (n = 1) implies input factors (m)
            prob += -factor_count * crossing[i][j] + sum_of_input_factors >= 0
            # increment current
            # this keeps track to make sure that every crossing is reached
            # e.g. if num_levels = [4, 4, 2], current level would change in the following way
            #   [0, 0, 0]
            #   [0, 0, 1]
            #   [0, 1, 0]
            #   [0, 1, 1]
            #   [0, 2, 0]
            #   ...
            c = factor_count - 1
            current_levels[c] += 1
            current_levels[c] = current_levels[c] % input_factors[c][1]
            while(current_levels[c] == 0):
                c -= 1
                current_levels[c] += 1
                current_levels[c] = current_levels[c] % input_factors[c][1]

        prob += lpSum([crossing[n][i] for n in row_trials]) == 1
        
# Derived levels
#   prob = lpProblem
#   derived_factor = lpVariable being edited
#   factor_name = name of factor for internal workings
#   input_factors = lpVariables being inputted
#   derived_level = derived level being added
#   dependent_idx = parameters that result in the level being true
#   row_trials = number of trials in range form (e.g. range(num_trials)))
#
# e.g. AddDerivedLevel(prob, congruency, "Congruency", [color, text] , 0, dependent_idxs_con, row_trials)
def AddDerivedLevel(prob, derived_factor, factor_name, input_factors, derived_level, dependent_idxs, num_trials):
    factor_count = len(input_factors)
    valid_idx_count = len(dependent_idxs)
    intermediate_variables = LpVariable.dicts("_hidden" + factor_name + str(derived_level), (range(valid_idx_count), range(num_trials)), cat="Binary")
    for n in range(num_trials):
        for i in range(valid_idx_count):
            # Intermediate_variable is true IFF dependent_factors are all true.
            # These fit a general form for AND implications:
            #   General AND(n amount of variables 1) -> AND(m amount of variables 2):
            #       -m(sum of variables 1) + (sum of variables 2) >= m(1 - n)
            # Hence we can plug in our specific case where there is only one intermediate variable
            #   input_factors (n = # of factors) -> intermediate variable (m = 1 variable):
            #       -(sum of input factors) + (intermediate variable) >= 1 - n
            #   intermediate variable (n = 1 variable) -> input factors (m = # of factors):
            #       -m(intermediate variable) + (sum of input factors) >= 0
            #
            # e.g. -(color[0][n] + text[0][n]) + intermediate[0][n] >= -1
            #      -2*intermediate[0][n] + (color[0][n] + text[0][n]) >= 0

            sum_of_input_factors = lpSum([input_factors[r][dependent_idxs[i][r]][n] for r in range(factor_count)])
            
            # First, n = factor_count and m = 1
            prob += -sum_of_input_factors + intermediate_variables[i][n] >= 1 - factor_count
            # Next, n = 1 and m = factor_count
            prob += -factor_count * intermediate_variables[i][n] + sum_of_input_factors >= 0

        # Derived level is true IFF intermediate variables are all true.
        # These fit another general form for OR implications:
        #   General OR(n amount of variables 1) -> OR(m amount of variables 2):
        #       -(sum of variables 1) + n*(sum of variables 2) >= 0
        # Hence we can plug in our specific case where there is only one derived level
        #   intermediate variables (n = # of intermediate variables) -> derived level:
        #       -(sum of intermediate variables) + n*(derived level) >= 0
        #   derived level (n = 1 variable) -> intermediate variables:
        #       -(derived level) + (sum of intermediate variables) >= 0
        #
        # e.g. -(intermediate[0][n] + intermediate[1][n]) + 2*derived_factor[0][n] >= 0
        #      -derived_factor[0][n] + (intermediate[0][n] + intermediate[1][n]) >= 0

        sum_of_intermediate_variables = lpSum([intermediate_variables[r][n] for r in range(valid_idx_count)])

        # First, n = valid_idx_count
        prob += -sum_of_intermediate_variables + valid_idx_count*derived_factor[derived_level][n] >= 0
        # Next, n = 1
        prob += -derived_factor[derived_level][n] + sum_of_intermediate_variables >= 0

def AddDerivedLevelWithComplex(prob, derived_factor, factor_name, input_factors, offsets, derived_level, dependent_idxs, num_per_trial, applicable_trials, num_trials):
    factor_count = len(input_factors)
    valid_idx_count = len(dependent_idxs)
    intermediate_variables = LpVariable.dicts("_hidden" + factor_name + str(derived_level), (range(valid_idx_count), applicable_trials), cat="Binary")
    for n in applicable_trials:
        for i in range(valid_idx_count):
            # Intermediate_variable is true IFF dependent_factors are all true.
            # These fit a general form for AND implications:
            #   General AND(n amount of variables 1) -> AND(m amount of variables 2):
            #       -m(sum of variables 1) + (sum of variables 2) >= m(1 - n)
            # Hence we can plug in our specific case where there is only one intermediate variable
            #   input_factors (n = # of factors) -> intermediate variable (m = 1 variable):
            #       -(sum of input factors) + (intermediate variable) >= 1 - n
            #   intermediate variable (n = 1 variable) -> input factors (m = # of factors):
            #       -m(intermediate variable) + (sum of input factors) >= 0
            #
            # e.g. -(color[0][n] + text[0][n]) + intermediate[0][n] >= -1
            #      -2*intermediate[0][n] + (color[0][n] + text[0][n]) >= 0

            input_factor_list = []
            for r in range(factor_count):
                current_input_factor = input_factors[r]
                current_input_level_idx = (dependent_idxs[i][r] % num_per_trial) - offsets[r]
                current_input_trial = n + int(dependent_idxs[i][r] / num_per_trial) - applicable_trials[0]
                input_factor_list += [current_input_factor[current_input_level_idx][current_input_trial]]

            sum_of_input_factors = lpSum(input_factor_list)
            
            # First, n = factor_count and m = 1
            prob += -sum_of_input_factors + intermediate_variables[i][n] >= 1 - factor_count
            # Next, n = 1 and m = factor_count
            prob += -factor_count * intermediate_variables[i][n] + sum_of_input_factors >= 0

        # Derived level is true IFF intermediate variables are all true.
        # These fit another general form for OR implications:
        #   General OR(n amount of variables 1) -> OR(m amount of variables 2):
        #       -(sum of variables 1) + n*(sum of variables 2) >= 0
        # Hence we can plug in our specific case where there is only one derived level
        #   intermediate variables (n = # of intermediate variables) -> derived level:
        #       -(sum of intermediate variables) + n*(derived level) >= 0
        #   derived level (n = 1 variable) -> intermediate variables:
        #       -(derived level) + (sum of intermediate variables) >= 0
        #
        # e.g. -(intermediate[0][n] + intermediate[1][n]) + 2*derived_factor[0][n] >= 0
        #      -derived_factor[0][n] + (intermediate[0][n] + intermediate[1][n]) >= 0

        sum_of_intermediate_variables = lpSum([intermediate_variables[r][n] for r in range(valid_idx_count)])

        # First, n = valid_idx_count
        prob += -sum_of_intermediate_variables + valid_idx_count*derived_factor[derived_level][n] >= 0
        # Next, n = 1
        prob += -derived_factor[derived_level][n] + sum_of_intermediate_variables >= 0

    for n in [i for i in range(num_trials) if i not in applicable_trials]:
        prob += derived_factor[derived_level][n] == 0

def AtMostKInARow(prob, factor, num_levels, k, num_trials):
    row_levels = range(num_levels)
    row_k = range(k + 1)
    for n in range(num_trials - k):
        for r in row_levels:
            sum_of_next_k = lpSum([factor[r][n + i] for i in row_k])
            prob += sum_of_next_k <= k

def AtLeastKInARow(prob, factor, num_levels, k, num_trials):
    row_levels = range(num_levels)
    row_k = range(k - 1)
    #   General AND(n amount of variables 1) -> AND(m amount of variables 2):
    #       -m(sum of variables 1) + (sum of variables 2) >= m(1 - n)
    # corner cases 
    for r in row_levels:
        prob += -(k - 1) * factor[r][0] + lpSum([factor[r][1 + k] for k in row_k]) >= 0
        prob += -(k - 1) * factor[r][num_trials - 1] + lpSum([factor[r][num_trials - 2 - k] for k in row_k]) >= 0
    for n in range(num_trials - k - 1):
        for r in row_levels:
            prob += -(k - 1) * lpSum([(1 - factor[r][n]), factor[r][n + 1]]) + lpSum([factor[r][n + 2 + k] for k in row_k]) >= -(k - 1)

def ExactlyKInARow(prob, factor, num_levels, k, num_trials):
    AtLeastKInARow(prob, factor, num_levels, k, num_trials)
    AtMostKInARow(prob, factor, num_levels, k, num_trials)

def RunProgram(prob):
    # init
    num_c = 4
    num_t = 4
    # num_third = 3
    num_con = 2    #Congruency
    num_resp = 4
    num_trans = 2  #Transition

    num_crossing = [num_t, num_c, num_trans]
    num_trials = np.product(num_crossing) + 1

    # num_noncomplex = num_c + num_t
    num_per_trial = num_c + num_t + num_con + num_resp + num_trans
    # num_noncomplex = num_c + num_t + num_con + num_resp

    row_c = range(num_c)
    row_t = range(num_t)
    # row_third = range(num_third)
    row_con = range(num_con)
    row_resp = range(num_resp)
    row_trans = range(num_trans)
    row_trials = range(num_trials)

    # Variables
    color = LpVariable.dicts("Color", (row_c, row_trials), cat="Binary")
    text = LpVariable.dicts("Text", (row_t, row_trials), cat="Binary")
    # third = LpVariable.dicts("Third", (row_third, row_trials), cat="Binary")
    congruency = LpVariable.dicts("Congruency", (row_con, row_trials), cat="Binary")
    response = LpVariable.dicts("Response", (row_resp, row_trials), cat="Binary")
    transition = LpVariable.dicts("response_transition", (row_trans, row_trials), cat="Binary")

    simple_factors = [(color, num_c), (text, num_t)]
    derived_factors = [(congruency, num_con), (response, num_resp), (transition, num_trans)]
    var_crossing = [(color, num_c), (text, num_t), (transition, num_trans)]

    # Setup the color and text variables
    Consistency(prob, color, num_c, num_trials)
    Consistency(prob, text, num_t, num_trials)
    # Consistency(prob, third, num_third, num_trials)

    # Setup a congruency derived level aimed at modeling the following functions
    # def congruent(color, word):
    #     return color == word
    # def incongruent(color, word):
    #     return not congruent(color, word)
    dependent_idxs_con = [[0, 0], [1, 1], [2, 2], [3, 3]]
    dependent_idxs_incon = [[0, 1], [0, 2], [0, 3], [1, 0], [1, 2], [1, 3], [2, 0], [2, 1], [2, 3], [3, 0], [3, 1], [3, 2]]

    AddDerivedLevel(prob, congruency, "Congruency", [color, text], 0, dependent_idxs_incon, num_trials)
    AddDerivedLevel(prob, congruency, "Congruency", [color, text], 1, dependent_idxs_con, num_trials)
    Consistency(prob, congruency, num_con, num_trials)

    # Setup another derived level for the response
    # def response_up(color):
    #     return color == "red"
    # def response_down(color):
    #     return color == "blue"
    # def response_left(color):
    #     return color == "green"
    # def response_right(color):
    #     return color == "brown"
    dependent_idxs_red = [[0]]
    dependent_idxs_blue = [[1]]
    dependent_idxs_green = [[2]]
    dependent_idxs_brown = [[3]]

    AddDerivedLevel(prob, response, "Response", [color], 0, dependent_idxs_red, num_trials)
    AddDerivedLevel(prob, response, "Response", [color], 1, dependent_idxs_blue, num_trials)
    AddDerivedLevel(prob, response, "Response", [color], 2, dependent_idxs_green, num_trials)
    AddDerivedLevel(prob, response, "Response", [color], 3, dependent_idxs_brown, num_trials)
    Consistency(prob, response, num_resp, num_trials)

    # def response_repeat(response):
    #     return response[0] == response[1]
    # def response_switch(response):
    #     return not response_repeat(response)
    dependent_idxs_repeat = [[10, 26], [11, 27], [12, 28], [13, 29]]
    dependent_idxs_switch = [[10, 27], [10, 28], [10, 29], [11, 26], [11, 28], [11, 29], [12, 26], [12, 27], [12, 29], [13, 26], [13, 27], [13, 28]]
    applicable_trials = range(1, num_trials)
    k = 7

    AddDerivedLevelWithComplex(prob, transition, "Transition", [response, response], [10, 10], 0, dependent_idxs_repeat, num_per_trial, applicable_trials, num_trials)
    AddDerivedLevelWithComplex(prob, transition, "Transition", [response, response], [10, 10], 1, dependent_idxs_switch, num_per_trial, applicable_trials, num_trials)
    Consistency(prob, transition, num_trans, num_trials, True, applicable_trials)
    AtMostKInARow(prob, transition, num_trans, k, num_trials)

    # complete crossing
    crossing = LpVariable.dicts("Crossing", (row_trials, row_trials), cat="Binary")
    FullyCross(prob, crossing, var_crossing, num_trials, True, applicable_trials)

    return simple_factors, derived_factors, num_trials

# Problem
prob = LpProblem("Example_ILP", LpMaximize)

# Program
simple_factors, derived_factors, num_trials = RunProgram(prob)

# Solve and Print

# Idea: .opb files
prob.writeLP("Example_ILP.lp")
times = []
for i in range(1):
    start = time()
    prob.solve(apis.GUROBI())
    end = time()
    times += [end - start]

    print("Status: ", LpStatus[prob.status])
    
    if LpStatus[prob.status] != 'Infeasible':
        for n in range(num_trials):
            print(n, end='\t')
            def translate_factor(r):
                if r == 0:
                    return "red"
                elif r == 1:
                    return "blue"
                elif r == 2:
                    return "green"
                elif r == 3:
                    return "brown"
            color = simple_factors[0][0]
            for r in range(simple_factors[0][1]):
                if value(color[r][n]) == 1:
                    print(f'Color: {translate_factor(r):10}| ', end='')
            text = simple_factors[1][0]
            for r in range(simple_factors[1][1]):
                if value(text[r][n]) == 1:
                    print(f'Text: {translate_factor(r):10}| ', end='')

            # third = simple_factors[2][0]
            # for r in range(simple_factors[2][1]):
            #     if value(third[r][n]) == 1:
            #         print(f'Third: {r:10}| ', end='')

            congruency = derived_factors[0][0]
            def translate_congruency(r):
                return "inc" if r == 0 else "con"
            for r in range(derived_factors[0][1]):
                if value(congruency[r][n]) == 1:
                    print(f'Congruency: {translate_congruency(r):10}| ', end='')

            response = derived_factors[1][0]
            def translate_response(r):
                if r == 0:
                    return "up"
                elif r == 1:
                    return "down"
                elif r == 2:
                    return "left"
                elif r == 3:
                    return "right"
            for r in range(derived_factors[1][1]):
                if value(response[r][n]) == 1:
                    print(f'Response: {translate_response(r):10}| ', end='')

            transition = derived_factors[2][0]
            def translate_repeat(r):
                return "repeat" if r == 0 else "switch"
            for r in range(derived_factors[2][1]):
                if value(transition[r][n]) == 1:
                    print(f'Transition: {translate_repeat(r):10}| ', end='')

            print()

# prob.writeLP("10by10_pulp.lp")

print(sum(times) / len(times))
#print(times)
