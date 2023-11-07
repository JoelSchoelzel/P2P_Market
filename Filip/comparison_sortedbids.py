import pickle
import matplotlib.pyplot as plt
import pandas as pd
import ast
#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)




#data from Filip
data2 = pd.read_csv('output1.csv')