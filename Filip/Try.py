import pickle
import datetime

file_path = "D:/jdu-zwu/P2P_Market/results/P2P_mar_dict/scenario_test_price.p"
with open(file_path, 'rb') as file:
    loaded_data = pickle.load(file)

# get the bid of the buildings
bids = loaded_data['bid'][0]

# get the bid of the buildings
print(bids)

time = datetime.datetime.now()
time_index = time.strftime("%d/%m/%Y, %H:%M:%S")