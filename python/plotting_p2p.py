import matplotlib.pyplot as plt
import pandas as pd
import pickle



## Transform the data saved in mar_dict into a DataFrame, in order to plot them with matplotlib

# open the pickle files containing the data
with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results"+"/mar_dict_P2P_" +"scenario3"+ ".p", 'rb') as file_mar:
    mar_dict = pickle.load(file_mar)

with open("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results" + "/par_rh_P2P_" + "scenario3" + ".p",'rb') as file_par:
    par_rh = pickle.load(file_par)

# Choose which data to plot
plotting_criteria = "power_from_grid"  # "power_within_district" or "power_from_grid"

def plotting(mar_dict, par_rh):

    time_steps = []
    traded_power = []
    traded_power_to_grid = []
    cumulative_volume = 0
    cumulative_grid = 0
    for n_opt in range(len(par_rh["org_time_steps"])):
        time_steps.append(par_rh["hour_start"][n_opt])
        cumulative_volume += mar_dict["total_market_info"][n_opt]["total_traded_volume"]/1000
        traded_power.append(cumulative_volume)
        cumulative_grid += mar_dict["total_market_info"][n_opt]["total_power_to_grid"]/1000
        traded_power_to_grid.append(cumulative_grid)
        # traded_power.append(mar_dict["total_market_info"][n_opt]["total_traded_volume"])

    data = {
        "time_steps": time_steps,
        "traded_power_within_district": traded_power,
        "traded_power_to_grid": traded_power_to_grid
    }

    df = pd.DataFrame(data)

    return df

df = plotting(mar_dict=mar_dict, par_rh=par_rh)


plt.figure(figsize=(10, 5))
plt.xlabel("Timesteps [h]")  # X-axis label
plt.ylabel("Power [kW]")  # Y-axis label
plt.grid()

if plotting_criteria == "power_within_district":
    plt.plot(df["time_steps"], df["traded_power_within_district"])
    plt.title("Cumulative traded power within district")  # Title of the plot

if plotting_criteria == "power_from_grid":
    plt.plot(df["time_steps"], df["traded_power_to_grid"])
    plt.title("Cumulated power injected into grid")  # Title of the plot

plt.show()


#TODO: add Latex font to the plot
"""plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "Palatino"
})"""







