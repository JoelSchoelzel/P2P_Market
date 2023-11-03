import pickle
import matplotlib.pyplot as plt
import pandas as pd
import ast
#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)

y1 = []
for n in range(3):
    #x.append(n)
    y1.append(data1['bid'][n]['bes_0'][1])

#data from Filip
data2 = pd.read_csv('output0.csv')

y2 = []
for n in range(3):
    data2_list = ast.literal_eval(data2['bes_0'][n])
    y2.append(data2_list[1])

fig, ax = plt.subplots()
ax.plot(y1, ":b", label='Linie 1', marker=".")
ax.plot(y2, "--r", label='Line 2')
plt.legend()
plt.xlabel('n_opt')
plt.ylabel('quantity')
plt.show()
