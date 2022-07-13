from builtins import list
from os import stat
import statistics
import math

def collect(input):
    f = open(input, "r")
    temp = f.read().split()
    f.close()
    time = []
    data = []
    for i, t in enumerate(temp):
        if i % 2 == 0:
            time.append(float(t[:-1]))
        else:
            data.append(list(map(lambda s: int(s), t.replace("[", "").replace("]", "").split(",")[:-1])))
    return time, data

def data_collection(temp_time, temp_data):
    print(statistics.mean(temp_time), ":", statistics.mean(list(map(lambda i: statistics.pstdev(i), temp_data))))

def data_mod(temp_time, temp_data):
    final_sum = []

    for i in range(len(temp_data[0])):
        final_sum.append([])

    for i in temp_data:
        for j, k in enumerate(i):
            final_sum[j].append(k)

    for i, j in enumerate(final_sum):
        print(i, ":\t", statistics.mean(j), "\t", statistics.stdev(j))

    entropy = []

    for t in temp_data:
        entr = 0
        for i, j in enumerate(t):
            entr -= ((j/1000)*(math.log(j/1000, 2.0)))
        entropy.append(entr)

    print(statistics.mean(entropy))

    return final_sum

def collect_ilp(input):
    f = open(input, "r")
    temp = f.read().replace(" ", "").split("\n")
    f.close()
    time = []
    data = []
    for i, t in enumerate(temp):
        if not t.split(":")[0]:
            continue
        time.append(float(t.split(":")[0]))
        data.append(list(map(lambda s: int(s), t.split(":")[1].replace("[", "").replace("]", "").split(",")[:-1])))
        # data.append(list(map(lambda s: int(s), t.split(":")[1].replace("[", "").replace("]", "").split(","))))
    return time, data

time_ilp_e, data_ilp_e = collect_ilp("data/sample_blocks_data.py")
data_collection(time_ilp_e, data_ilp_e)
final_sum = data_mod(time_ilp_e, data_ilp_e)

# time_ilp_e, data_ilp_e = collect("data/sample_data.txt")
# data_collection(time_ilp_e, data_ilp_e)
# data_mod(time_ilp_e, data_ilp_e)

# print(final_sum)

import matplotlib.pyplot as plt

# x = list(range(0, 24))
# y = list(range(0, 18))

plt.boxplot(final_sum)
plt.show()

# fig, axs = plt.subplots(2,2)
# axs[0, 0].bar(x, data_unigen[0])
# axs[0, 1].bar(y, data_excluded_unigen[0])
# axs[1, 0].bar(x, data_ilp[0])
# axs[1, 1].bar(y, data_ilp_e[0])

# plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
# plt.savefig("all_four")

# for t, j in enumerate([data_unigen, data_excluded_unigen, data_ilp, data_excluded_ilp, data_ilp_s]):
#     x = list(range(0, len(j[0])))
#     fig, axs = plt.subplots(10,10)

#     for i in range(0,100):
#         axs[int(i/10), i%10].bar(x, j[i])
#     plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
#     plt.savefig(str(t))