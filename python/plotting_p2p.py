import matplotlib.pyplot as plt
import pandas as pd
import pickle


# ------------ JANUARY ------------
with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_time_P2P_" + "Quartier_3_jan" + ".p",'rb') as file_res_time_jan:
    results_time_jan = pickle.load(file_res_time_jan)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_val_P2P_" + "Quartier_3_jan" + ".p",'rb') as file_res_val_jan:
    results_val_jan = pickle.load(file_res_val_jan)

# ------------ APRIL ------------
with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_time_P2P_" + "Quartier_3_apr" + ".p",'rb') as file_res_time_apr:
    results_time_apr = pickle.load(file_res_time_apr)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_val_P2P_" + "Quartier_3_apr" + ".p",'rb') as file_res_val_apr:
    results_val_apr = pickle.load(file_res_val_apr)

# ------------ JULY ------------
with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_time_P2P_" + "Quartier_3_jul" + ".p",'rb') as file_res_time_jul:
    results_time_jul = pickle.load(file_res_time_jul)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/res_val_P2P_" + "Quartier_3_jul" + ".p",'rb') as file_res_val_jul:
    results_val_jul = pickle.load(file_res_val_jul)



# create the DataFrame to plot
df_time_jan = pd.DataFrame(results_time_jan)
df_val_jan = pd.DataFrame(results_val_jan)

df_time_apr = pd.DataFrame(results_time_apr)
df_val_apr = pd.DataFrame(results_val_apr)

df_time_jul = pd.DataFrame(results_time_jul)
df_val_jul = pd.DataFrame(results_val_jul)


# ------------ PLOTTING ------------

# choose criteria to plot
plot_kpi = "total_demand"

# customizing the plot
plt.figure(figsize=(10, 5))
plt.xlabel("Timesteps [h]")  # X-axis label
#plt.grid()
#time_steps = len(df_time_apr["total_demand"])

if plot_kpi == "dcf_month":
    plt.ylabel("SCF")  # Y-axis label
    plt.bar(0, df_val_jan["scf_month"], color="green", label="January")
    #plt.bar(1, 3, color="red", label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["dcf_month"], color="blue", label="April")
    plt.bar(2, df_val_jul["dcf_month"], color="red", label="July")
    plt.title("DCF district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_demand":
    df_week = df_time_jul.head(168)
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df_week["total_demand"], color="red", label="Total demand")
    plt.plot(df_week["total_supply"], color="green", label="Total supply")
    plt.plot(df_week["traded_power"], color="blue", label="Traded power")
    # plt.plot(df_week["power_to_grid"], color="orange", label="Power to grid")
    # plt.plot(df_week["power_from_grid"], color="purple", label="Power from grid")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "total_traded_power":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_traded_power"], color="green", label="January")
    #plt.bar(1, 3, color="red", label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_traded_power"], color="blue", label="April")
    plt.bar(2, df_val_jul["total_traded_power"], color="red", label="July")
    plt.title("Total traded power district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_power_to_grid":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_power_to_grid"], color="green", label="January")
    #plt.bar(1, 3, color="red", label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_power_to_grid"], color="blue", label="April")
    plt.bar(2, df_val_jul["total_power_to_grid"], color="red", label="July")
    plt.title("total_power_to_grid district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_power_from_grid":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_power_from_grid"], color="green", label="January")
    #plt.bar(1, 3, color="red", label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_power_from_grid"], color="blue", label="April")
    plt.bar(2, df_val_jul["total_power_from_grid"], color="red", label="July")
    plt.title("Total_power_from_grid district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_demand_month":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_demand_month"], color="green", label="Demand", width=1)
    plt.bar(1, df_val_jan["total_power_from_grid"], color="lightgreen", label="Grid import", width=1)

    #plt.bar(1, 3, color="red", label="SCF = 1", width=0.05)
    plt.bar(3, df_val_apr["total_demand_month"], color="green", width=1)
    plt.bar(4, df_val_apr["total_power_from_grid"], color="lightgreen", width=1)

    plt.bar(6, df_val_jul["total_demand_month"], color="green", width=1)
    plt.bar(7, df_val_jul["total_power_from_grid"], color="lightgreen", width=1)

    plt.xticks([0.5, 3.5, 6.5], ["January", "April", "July"])

    plt.title("total_demand_month district 3")  # Title of the plot
    plt.legend()


if plot_kpi == "traded_power":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df_time_jul["total_demand"], color="red", label="Total demand")
    plt.plot(df_time_jul["total_supply"], color="green", label="Total supply")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "saved_costs":
    df_week = df_time_jul.head(168) # only plot the first week
    plt.ylabel("Costs [€]")  # Y-axis label
    # plt.plot(df_week["saved_costs"], color="red", label="Saved costs")
    # plt.plot(df_week["additional_revenue"], color="green", label="Additional Revenue")

    cumulative_values = df_time_jul["gain"].cumsum()
    plt.plot(cumulative_values.index, cumulative_values.values, color="blue", label="Gain")
    plt.title("Saved costs within district")  # Title of the plot
    plt.legend()

plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/plots/Quartier_3_"+plot_kpi+".svg")
plt.show()




