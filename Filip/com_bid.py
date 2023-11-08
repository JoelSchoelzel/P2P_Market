import pickle
import matplotlib.pyplot as plt
import pandas as pd
import ast
#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)

b0_p1 = []
b0_q1 = []
b1_p1 = []
b1_q1 = []
b2_p1 = []
b2_q1 = []
b3_p1 = []
b3_q1 = []
for n in range(36):
    #x.append(n)
    b0_p1.append(data1['bid'][n]['bes_0'][0])
    b0_q1.append(data1['bid'][n]['bes_0'][1])
    b1_p1.append(data1['bid'][n]['bes_1'][0])
    b1_q1.append(data1['bid'][n]['bes_1'][1])
    b2_p1.append(data1['bid'][n]['bes_2'][0])
    b2_q1.append(data1['bid'][n]['bes_2'][1])
    b3_p1.append(data1['bid'][n]['bes_3'][0])
    b3_q1.append(data1['bid'][n]['bes_3'][1])

#data from Filip
data2 = pd.read_csv('output0.csv')

b0_p2 = []
b0_q2 = []
b1_p2 = []
b1_q2 = []
b2_p2 = []
b2_q2 = []
b3_p2 = []
b3_q2 = []
for n in range(36):
    data2_list0 = ast.literal_eval(data2['bes_0'][n*4])
    b0_p2.append(data2_list0[0])
    b0_q2.append(data2_list0[1])
    data2_list1 = ast.literal_eval(data2['bes_1'][n*4+1])
    b1_p2.append(data2_list1[0])
    b1_q2.append(data2_list1[1])
    data2_list2 = ast.literal_eval(data2['bes_2'][n*4+2])
    b2_p2.append(data2_list2[0])
    b2_q2.append(data2_list2[1])
    data2_list3 = ast.literal_eval(data2['bes_3'][n*4+3])
    b3_p2.append(data2_list3[0])
    b3_q2.append(data2_list3[1])

fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8)) = plt.subplots(4, 2, figsize=(12, 8))
ax1.plot(b0_p1, ":b", label='P2P_Market', marker=".")
ax1.plot(b0_p2, "--r", label='Zehao')
ax1.legend()
ax1.set_ylabel('price')
ax1.set_title('The electricity price and quantity of Building_0 in 36h')

ax2.plot(b0_q1, ":b", label='P2P_Market', marker=".")
ax2.plot(b0_q2, "--r", label='Zehao')
plt.legend()
ax2.set_xlabel('n_opt')
ax2.set_ylabel('quantity')

ax3.plot(b1_p1, ":b", label='P2P_Market', marker=".")
ax3.plot(b1_p2, "--r", label='Zehao')
ax3.legend()
ax3.set_ylabel('price')
ax3.set_title('The electricity price and quantity of Building_1 in 36h')

ax4.plot(b1_q1, ":b", label='P2P_Market', marker=".")
ax4.plot(b1_q2, "--r", label='Zehao')
plt.legend()
ax4.set_xlabel('n_opt')
ax4.set_ylabel('quantity')

ax5.plot(b2_p1, ":b", label='P2P_Market', marker=".")
ax5.plot(b2_p2, "--r", label='Zehao')
ax5.legend()
ax5.set_ylabel('price')
ax5.set_title('The electricity price and quantity of Building_2 in 36h')

ax6.plot(b2_q1, ":b", label='P2P_Market', marker=".")
ax6.plot(b2_q2, "--r", label='Zehao')
plt.legend()
ax6.set_xlabel('n_opt')
ax6.set_ylabel('quantity')

ax7.plot(b3_p1, ":b", label='P2P_Market', marker=".")
ax7.plot(b3_p2, "--r", label='Zehao')
ax7.legend()
ax7.set_ylabel('price')
ax7.set_title('The electricity price and quantity of Building_3 in 36h')

ax8.plot(b3_q1, ":b", label='P2P_Market', marker=".")
ax8.plot(b3_q2, "--r", label='Zehao')
plt.legend()
ax8.set_xlabel('n_opt')
ax8.set_ylabel('quantity')
plt.show()