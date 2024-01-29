import matplotlib.pyplot as plt
import pickle

file_name = "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/P2P_opti_output/scenario2.p"

with open(file_name, "rb") as f:
    data = pickle.load(f)

for building in data[0][0]:
    p_buy = list()
    p_sell = list()
    for time_step in data:
        p_buy.append(data[time_step][4][building][time_step])
        p_sell.append(data[time_step][8][building]["chp"][time_step])
    plt.plot(p_buy)
    plt.plot(p_sell)
    plt.title(f"Building {building}")
    plt.show()