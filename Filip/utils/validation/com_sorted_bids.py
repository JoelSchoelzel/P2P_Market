"""
TODO add documentation
"""

import pickle
import pandas as pd
import ast
#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)
price1 = []
for s in range(2, 581):
    price1.append(len(data1['sorted_bids'][s]['buy']))
    price1.append(len(data1['sorted_bids'][s]['sell']))
#print(price1)
print(len(price1))
print(f"sum: {sum(price1)}")
#print(average1)

price2 = []
#data from Filip
data2 = pd.read_csv('output_sortedbids.csv')
for m in range(2, 581):
    data2_list = ast.literal_eval(data2['buy'][m])
    data3_list = ast.literal_eval(data2['sell'][m])
    price2.append(len(data2_list))
    price2.append(len(data3_list))
#print(price2)
print(len(price2))
print(f"sum: {sum(price2)}")
#average2 = sum(price2) / len(price2)
#print(average2)