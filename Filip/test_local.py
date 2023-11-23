import pickle

file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)
print(data1)

file_path2 = 'D:\jdu-zwu\P2P_Market\p2p_transaction.p'
with open(file_path2, 'rb') as file:
    data2 = pickle.load(file)
print(data2)