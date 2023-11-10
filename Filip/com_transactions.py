import pickle
import matplotlib.pyplot as plt
import pandas as pd
import ast

#data from P2P_Market
file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
with open(file_path1, 'rb') as file:
    data1 = pickle.load(file)
price1 = []
ave_price1 = []
for s in range(2, 709):
    for t in range(3):
        if t in data1['transactions'][s]:
            price1.append(data1['transactions'][s][t]['price'])
    ave_price1.append(sum(price1)/len(price1))
print(price1)
print(len(price1))
average1 = sum(price1) / len(price1)
print(average1)
print(ave_price1)
print(len(ave_price1))

price2 = []
ave_price2 = []
#data from Filip
chunk_size = 1
data2 = pd.read_csv('output_transactions.csv', chunksize=chunk_size)

# Iterate over the chunks (each chunk is a DataFrame with one row)
for data2_chunk in data2:
    # Process the current row (chunk)
    for n in range(3):
        if not pd.isna(data2_chunk[str(n)].iloc[0]):
            data2_list = ast.literal_eval(data2_chunk[str(n)].iloc[0])
            price2.append(data2_list['price'])
    if len(price2) > 0:
        ave_price2.append(sum(price2)/len(price2))
    # Add your custom processing logic here
print(f"Price2: {price2}")
print(f"Length of Price2: {len(price2)}")
average2 = sum(price2) / len(price2)
print(f"average2: {average2}")
print(f"ave_price2: {ave_price2}")
print(f"Length of Ave_Price: {len(ave_price2)}")

fig, ax = plt.subplots()
ax.plot(ave_price1, label='P2P_Market', color='blue', linestyle='-', marker='o')
ax.plot(ave_price2, label='Filip', color='red', linestyle='--', marker='s')
ax.legend()
ax.set_ylabel('average price for every hour')
ax.set_title('The average price in 707h')
plt.show()