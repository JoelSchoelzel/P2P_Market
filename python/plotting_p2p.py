import matplotlib.pyplot as plt
import pandas as pd
import pickle



## Transform the data saved in mar_dict into a DataFrame, in order to plot them with matplotlib
def plotting(mar_dict, par_rh):
    # initialize necessary lists
    time_steps = []
    traded_power_within_distr = []
    power_to_grid = []
    cumulative_traded_power_within_distr = []
    cumulative_power_to_grid = []
    supply_demand_ratio = []
    total_avg_trade_price = []
    cumulative_volume = 0
    cumulative_grid = 0

    for n_opt in range(len(par_rh["org_time_steps"])):
        time_steps.append(par_rh["hour_start"][n_opt])
        #time_steps.append(par_rh["hour_start"][n_opt][0:par_rh["block_bid_length"]])
        traded_power_within_distr.append(mar_dict["total_market_info"][n_opt]["total_traded_volume"])
        #power_to_grid.append(mar_dict["total_market_info"][n_opt]["total_power_to_grid"]/1000)

        cumulative_volume += mar_dict["total_market_info"][n_opt]["total_traded_volume"]/1000
        cumulative_traded_power_within_distr.append(cumulative_volume)
        #cumulative_grid += mar_dict["total_market_info"][n_opt]["total_power_to_grid"]/1000
        #cumulative_power_to_grid.append(cumulative_grid)

        supply_demand_ratio.append(mar_dict["total_market_info"][n_opt]["supply_demand_ratio"])
        total_avg_trade_price.append(mar_dict["total_market_info"][n_opt]["total_average_trade_price"])

    data = {
        "time_steps": time_steps,
        "traded_power_within_district": traded_power_within_distr,
        #"power_to_grid": power_to_grid,
        "cumulative_traded_power_within_district": cumulative_traded_power_within_distr,
        #"cumulative_power_to_grid": cumulative_power_to_grid,
        "supply_demand_ratio": supply_demand_ratio,
        "total_avg_trade_price": total_avg_trade_price
    }

    df = pd.DataFrame(data)

    return df


"""def plot_pv_gen(nodes,par_rh):
    # initialize necessary lists
    time_steps = []
    pv_gen = []

    for node in range(len(nodes)):
        for n_opt in range(len(par_rh["org_time_steps"])):
            time_steps.append(par_rh["hour_start"][n_opt][0:par_rh["block_bid_length"]])
        pv_gen.append(nodes[node]["pv_power"])

    data = {
        "time_steps": time_steps,
        "pv_gen": pv_gen
    }

    df_pv_gen = pd.DataFrame(data)

    return df_pv_gen"""



# open the pickle files containing the data
with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results"+"/mar_dict_P2P_" +"scenario3"+ ".p", 'rb') as file_mar:
    mar_dict = pickle.load(file_mar)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/par_rh_P2P_" + "scenario3" + ".p",'rb') as file_par:
    par_rh = pickle.load(file_par)

#with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/nodes_P2P_" + "scenario3" + ".p",'rb') as file_nodes:
   # nodes = pickle.load(file_nodes)

# Choose which data to plot
plotting_criteria = "total_avg_trade_price"  # "power_within_district" or "power_from_grid"

# create the DataFrame to plot
df = plotting(mar_dict=mar_dict, par_rh=par_rh)

# customizing the plot
plt.figure(figsize=(10, 5))
plt.xlabel("Timesteps [h]")  # X-axis label
plt.grid()

# plot the data
if plotting_criteria == "traded_power_within_district":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df["time_steps"], df["traded_power_within_district"])
    plt.title("Traded power within district")  # Title of the plot
elif plotting_criteria == "cumulative_traded_power_within_district":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df["time_steps"], df["cumulative_traded_power_within_distr"])
    plt.title("Cumulated power traded within district")  # Title of the plot


elif plotting_criteria == "power_to_grid":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df["time_steps"], df["power_to_grid"])
    plt.title("Power injected into grid")  # Title of the plot
elif plotting_criteria == "cumulative_power_to_grid":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df["time_steps"], df["cumulative_power_to_grid"])
    plt.title("Cumulated power injected into grid")  # Title of the plot

elif plotting_criteria == "supply_demand_ratio":
    plt.ylabel("SDR [%]")  # Y-axis label
    plt.plot(df["time_steps"], df["supply_demand_ratio"])
    plt.title("Supply demand ratio before trading")  # Title of the plot

elif plotting_criteria == "total_avg_trade_price":
    plt.ylabel("Price [€/kW]")  # Y-axis label
    plt.plot(df["time_steps"], df["total_avg_trade_price"])
    plt.title("Total average trading price")  # Title of the plot

# save the plot as svg file with file name "plot_"+plotting_criteria+".svg"
plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/Plots/scenario3/"+plotting_criteria+".svg")
plt.show()





#TODO: add Latex font to the plot
"""plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "Palatino"
})"""







