import pickle
import matplotlib.pyplot as plt
import pandas as pd
import ast
#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)
price1 = []
for s in range(2, 583):
    for t in range(3):
        if t in data1['transactions'][s]:
            price1.append(data1['transactions'][s][t]['price'])
print(price1)
print(len(price1))
average1 = sum(price1) / len(price1)
print(average1)

price2 = []
#data from Filip
data2 = pd.read_csv('output_transactions.csv')
for n in range(3):
    for m in range(2, 581):
        data2_list = ast.literal_eval(data2[str(n)][m])
        price2.append(data2_list['price'])
print(price2)
print(len(price2))
average2 = sum(price2) / len(price2)
print(average2)