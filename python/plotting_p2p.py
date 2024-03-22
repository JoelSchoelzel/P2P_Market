import matplotlib.pyplot as plt
import pandas as pd
import pickle


# open the pickle files containing the data
#with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results"+"/mar_dict_P2P_" +"scenario3"+ ".p", 'rb') as file_mar:
    #mar_dict = pickle.load(file_mar)

#with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/par_rh_P2P_" + "scenario3" + ".p",'rb') as file_par:
    #par_rh = pickle.load(file_par)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_time_P2P_" + "Quartier_3" + ".p",'rb') as file_res_time:
    results_time = pickle.load(file_res_time)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_val_P2P_" + "Quartier_3" + ".p",'rb') as file_res_val:
    results_val = pickle.load(file_res_val)

# create the DataFrame to plot
df = pd.DataFrame(results_time)
print(df)

# choose criteria to plot
plot_kpi = "total_demand"

# customizing the plot
plt.figure(figsize=(10, 5))
plt.xlabel("Timesteps [h]")  # X-axis label
plt.grid()
time_steps = len(df["total_demand"])

if plot_kpi == "total_demand":
    df_week = df.head(168)
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df_week["total_demand"], color="red", label="Total demand")
    plt.plot(df_week["total_supply"], color="green", label="Total supply")
    plt.plot(df_week["traded_power"], color="blue", label="Traded power")
    #plt.plot(df_week["power_to_grid"], color="orange", label="Power to grid")
    #plt.plot(df_week["power_from_grid"], color="purple", label="Power from grid")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "traded_power":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df["total_demand"], color="red", label="Total demand")
    plt.plot(df["total_supply"], color="green", label="Total supply")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "saved_costs":
    df_week = df.head(168) # only plot the first week
    plt.ylabel("Costs [€]")  # Y-axis label
    plt.plot(df_week["saved_costs"], color="blue", label="Saved costs")
    plt.title("Saved costs within district")  # Title of the plot
    plt.legend()


plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/plots/Quartier_3_"+plot_kpi+".svg")
plt.show()




