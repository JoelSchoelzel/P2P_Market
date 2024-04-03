import matplotlib.pyplot as plt
from matplotlib import rc
rc("font", **{"family": "sans-serif", "sans-serif": "Times New Roman"})  # "serif": [""]})  # Computer Modern Roman"
import pandas as pd
import pickle

# ------------ JANUARY ------------
path_root = "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/Results_for_plots/Quartier 3/"

with open(path_root+"/1_Jan/nB=5/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as res_time_jan_e:
        res_time_jan_e = pickle.load(res_time_jan_e)
with open(path_root+"/1_Jan/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as res_val_jan_e:
        res_val_jan_e = pickle.load(res_val_jan_e)

with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_price/res_time_P2P_Quartier_3_jan.p",'rb') as res_time_jan_p:
    res_time_jan_p = pickle.load(res_time_jan_p)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as res_val_jan_p:
    res_val_jan_p = pickle.load(res_val_jan_p)

with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as res_time_jan_q:
    res_time_jan_q = pickle.load(res_time_jan_q)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as res_val_jan_q:
    res_val_jan_q = pickle.load(res_val_jan_q)
# ------------ APRIL ------------
with open(path_root+"/2_Apr/nB=5/nCH=36/flex_energy/res_time_P2P_Quartier_3_apr.p",'rb') as res_time_apr_e:
    res_time_apr_e = pickle.load(res_time_apr_e)
with open(path_root+"/2_Apr/nB=5/nCH=36/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as res_val_apr_e:
    res_val_apr_e = pickle.load(res_val_apr_e)

with open(path_root+"/2_Apr/nB=5/nCH=36/mean_price/res_time_P2P_Quartier_3_apr.p",'rb') as res_time_apr_p:
    res_time_apr_p = pickle.load(res_time_apr_p)
with open(path_root+"/2_Apr/nB=5/nCH=36/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as res_val_apr_p:
    res_val_apr_p = pickle.load(res_val_apr_p)

with open(path_root+"2_Apr/nB=5/nCH=36/mean_quantity/res_time_P2P_Quartier_3_apr.p",'rb') as res_time_apr_q:
    res_time_apr_q = pickle.load(res_time_apr_q)
with open(path_root+"/2_Apr/nB=5/nCH=36/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as res_val_apr_q:
    res_val_apr_q = pickle.load(res_val_apr_q)

# ------------ JULY ------------
#with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jul.p",'rb') as res_time_jul_e:
 #   res_time_jul_e = pickle.load(res_time_jul_e)
with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul_avg.p",'rb') as res_val_jul_e_avg:
    res_val_jul_e_avg = pickle.load(res_val_jul_e_avg)
#with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul_avg2.p",'rb') as res_val_jul_e_avg2:
 #   res_val_jul_e_avg2 = pickle.load(res_val_jul_e_avg2)
with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul_delta.p",'rb') as res_val_jul_e_delta:
    res_val_jul_e_delta = pickle.load(res_val_jul_e_delta)
with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul_delta2.p",'rb') as res_val_jul_e_delta2:
    res_val_jul_e_delta2 = pickle.load(res_val_jul_e_delta2)

with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_price/res_time_P2P_Quartier_3_jul.p",'rb') as res_time_jul_p:
    res_time_jul_p = pickle.load(res_time_jul_p)
with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as res_val_jul_p:
    res_val_jul_p = pickle.load(res_val_jul_p)

with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jul.p",'rb') as res_time_jul_q:
    res_time_jul_q = pickle.load(res_time_jul_q)
with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as res_val_jul_q:
    res_val_jul_q = pickle.load(res_val_jul_q)


# create the DataFrame to plot over time
# ------------ JANUARY ------------
df_time_jan_e_dem = pd.DataFrame(list(res_time_jan_e["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_dem = pd.DataFrame(list(res_time_jan_p["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_dem = pd.DataFrame(list(res_time_jan_q["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jan_e_sup = pd.DataFrame(list(res_time_jan_e["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_sup = pd.DataFrame(list(res_time_jan_p["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_sup = pd.DataFrame(list(res_time_jan_q["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jan_e_trade = pd.DataFrame(list(res_time_jan_e["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_trade = pd.DataFrame(list(res_time_jan_p["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_trade = pd.DataFrame(list(res_time_jan_q["traded_power"].items()), columns=["Timestep", "Total traded power"])

# ------------ APRIL ------------
df_time_apr_e_dem = pd.DataFrame(list(res_time_apr_e["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_dem = pd.DataFrame(list(res_time_apr_p["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_dem = pd.DataFrame(list(res_time_apr_q["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_apr_e_sup = pd.DataFrame(list(res_time_apr_e["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_sup = pd.DataFrame(list(res_time_apr_p["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_sup = pd.DataFrame(list(res_time_apr_q["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_apr_e_trade = pd.DataFrame(list(res_time_apr_e["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_trade = pd.DataFrame(list(res_time_apr_p["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_trade = pd.DataFrame(list(res_time_apr_q["traded_power"].items()), columns=["Timestep", "Total traded power"])

# ------------ JULY ------------
df_time_jul_e_dem = pd.DataFrame(list(res_time_apr_e["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_dem = pd.DataFrame(list(res_time_apr_p["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_dem = pd.DataFrame(list(res_time_apr_q["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jul_e_sup = pd.DataFrame(list(res_time_apr_e["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_sup = pd.DataFrame(list(res_time_apr_p["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_sup = pd.DataFrame(list(res_time_apr_q["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jul_e_trade = pd.DataFrame(list(res_time_apr_e["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_trade = pd.DataFrame(list(res_time_apr_p["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_trade = pd.DataFrame(list(res_time_apr_q["traded_power"].items()), columns=["Timestep", "Total traded power"])


# ------------ COLORS ------------
red = ['#CC071E', '#D85C41', '#E69679', '#F3CDBB', '#FAEBE3']
blue = ['#00549F', '#407FB7', '#8EBAE5', '#C7DDF2', '#E8F1FA']
violet = ['#7A6FAC', '#9B91C1', '#BCB5D7', '#DEDAEB', '#F2F0F7']
green = ['#57ab27', '#8dc060', '#b8d698', '#ddebce', '#f2f7ec']
bordeaux = ['#a11035', '#b65256', '#cd8b87', '#e5c5c0', '#f5e8e5']
black = ['#000000', '#696969', '', '#808080', '#A9A9A9', '#DCDCDC']


# ------------ PLOTTING ------------
plot_kpi = "scf dcf month"  # dem, sup, trade
match_crit = "flex energy"  # flex energy, price, quantity
plt.figure(figsize=(10, 5))


if match_crit == "flex energy":
    if plot_kpi == "dem, sup, trade":
        df_head_e_dem = df_time_apr_e_dem.head(168)
        df_head_e_sup = df_time_apr_e_sup.head(168)
        df_head_e_trade = df_time_apr_e_trade.head(168)
        plt.plot(df_head_e_dem["Timestep"], df_head_e_dem["Total demand"], color=red[1], label="Demand")
        plt.plot(df_head_e_sup["Timestep"], df_head_e_sup["Total supply"], color=blue[1], label="Supply")
        plt.plot(df_head_e_trade["Timestep"], df_head_e_trade["Total traded power"], color=green[1], label="Traded Power")
        plt.xlabel("Timesteps [h]")  # X-axis label
        plt.ylabel("Power [kW]")  # Y-axis label
        plt.title("Trading within district 3 (April, match crit flex energy, nCH=36, nB=5)", fontweight="bold")  # Title of the plot
    elif plot_kpi == "mscf, mdcf":
        # plt.bar(0, res_val_jan_e["mscf_month"], color=red[1], label="MSCF", width=1)
        # plt.bar(1, res_val_jan_e["mdcf_month"], color=blue[1], label="MDCF", width=1)
        # plt.bar(3, res_val_apr_e["mscf_month"], color=red[1], width=1)
        # plt.bar(4, res_val_apr_e["mdcf_month"], color=blue[1], width=1)
        # plt.ylabel("Percentage [%]")  # Y-axis label
        # plt.title("MSCF and MDCF district 3 (match crit flex energy, nCH=36, nB=5)")  # Title of the plot
        # plt.xticks([0.5, 3.5], ["January", "April"])

        bars = []
        bars.append(plt.bar(0, res_val_jul_e_avg["mscf_month"]*100, color=green[0], width=1))
        bars.append(plt.bar(1, res_val_jul_e_delta["mscf_month"]*100, color=blue[0], width=1))
        bars.append(plt.bar(2, res_val_jul_e_delta2["mscf_month"]*100, color=blue[2], width=1))
        bars.append(plt.bar(4, res_val_jul_e_avg["mdcf_month"]*100, color=green[0], label="avg method", width=1))
        bars.append(plt.bar(5, res_val_jul_e_delta["mdcf_month"]*100, color=blue[0], label="delta method", width=1))
        bars.append(plt.bar(6, res_val_jul_e_delta2["mdcf_month"]*100, color=blue[2], label="delta2 method", width=1))

        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                text = f'{height:.2f}'
                plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')
        plt.ylabel("Percentage [%]")
        plt.ylim(0, 100)
        plt.title("MSCF, MDCF district 3 (match crit flex energy, nCH=nB=5)")  # Title of the plot
        plt.xticks([1, 5], ["MSCF", "MDCF"])

    elif plot_kpi == "scf dcf month":
        bars = []
        bars.append(plt.bar(0, res_val_jul_e_avg["scf_month"]*100, color=green[0], width=1))
        bars.append(plt.bar(1, res_val_jul_e_delta["scf_month"]*100, color=blue[0], width=1))
        bars.append(plt.bar(2, res_val_jul_e_delta2["scf_month"]*100, color=blue[2], width=1))
        bars.append(plt.bar(4, res_val_jul_e_avg["dcf_month"]*100, color=green[0], label="avg method", width=1))
        bars.append(plt.bar(5, res_val_jul_e_delta["dcf_month"]*100, color=blue[0], label="delta method", width=1))
        bars.append(plt.bar(6, res_val_jul_e_delta2["dcf_month"]*100, color=blue[2], label="delta2 method", width=1))

        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                text = f'{height:.2f}'
                plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')
        plt.ylabel("Percentage [%]")
        plt.ylim(0, 100)
        plt.title("SCF, DCF district 3 (match crit flex energy, nCH=nB=5)")  # Title of the plot
        plt.xticks([1, 5], ["SCF", "DCF"])

    elif plot_kpi == "saved cots, added rev":
        # plt.bar(0, res_val_jul_e_avg["total_saved_costs"], color=green[0], width=1)
        # plt.bar(1, res_val_jul_e_delta["total_saved_costs"], color=blue[0],  width=1)
        # plt.bar(2, res_val_jul_e_delta2["total_saved_costs"], color=blue[2], width=1)
        # plt.bar(4, res_val_jul_e_avg["total_additional_revenue"], color=green[0], label="avg method", width=1)
        # plt.bar(5, res_val_jul_e_delta["total_additional_revenue"], color=blue[0], label="delta method", width=1)
        # plt.bar(6, res_val_jul_e_delta2["total_additional_revenue"], color=blue[2], label="delta2 method", width=1)
        # plt.bar(8, res_val_jul_e_avg["gain"], color=green[0], width=1)
        # plt.bar(9, res_val_jul_e_delta["gain"], color=blue[0], width=1)
        # plt.bar(10, res_val_jul_e_delta2["gain"], color=blue[2], width=1)
        bars = []
        bars.append(plt.bar(0, res_val_jul_e_avg["total_saved_costs"], color=green[0], width=1))
        bars.append(plt.bar(1, res_val_jul_e_delta["total_saved_costs"], color=blue[0], width=1))
        bars.append(plt.bar(2, res_val_jul_e_delta2["total_saved_costs"], color=blue[2], width=1))
        bars.append(
            plt.bar(4, res_val_jul_e_avg["total_additional_revenue"], color=green[0], label="avg method", width=1))
        bars.append(
            plt.bar(5, res_val_jul_e_delta["total_additional_revenue"], color=blue[0], label="delta method", width=1))
        bars.append(
            plt.bar(6, res_val_jul_e_delta2["total_additional_revenue"], color=blue[2], label="delta2 method", width=1))
        bars.append(plt.bar(8, res_val_jul_e_avg["gain"], color=green[0], width=1))
        bars.append(plt.bar(9, res_val_jul_e_delta["gain"], color=blue[0], width=1))
        bars.append(plt.bar(10, res_val_jul_e_delta2["gain"], color=blue[2], width=1))
        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                text = f'{height:.2f}'
                plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')
        plt.ylabel("Profit [€]")
        plt.title("saved cots, added rev district 3 (match crit flex energy, nCH=nB=5)")  # Title of the plot
        plt.xticks([1, 5, 9], ["Saved costs", "Additional revenue", "Economic Gain"])

        # Adjust the bottom margin to make space for the legend
        # plt.subplots_adjust(bottom=0.2)
        # Place the legend below the plot
        # plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    elif plot_kpi == "traded power":
        bars = []
        bars.append(plt.bar(0, res_val_jul_e_avg["total_traded_power"], color=green[0], width=1))
        bars.append(plt.bar(1, res_val_jul_e_delta["total_traded_power"], color=blue[0], width=1))
        bars.append(plt.bar(2, res_val_jul_e_delta2["total_traded_power"], color=blue[2], width=1))
        bars.append(
            plt.bar(4, res_val_jul_e_avg["total_power_from_grid"], color=green[0], label="avg method", width=1))
        bars.append(
            plt.bar(5, res_val_jul_e_delta["total_power_from_grid"], color=blue[0], label="delta method", width=1))
        bars.append(
            plt.bar(6, res_val_jul_e_delta2["total_power_from_grid"], color=blue[2], label="delta2 method", width=1))

        bars.append(plt.bar(8, res_val_jul_e_avg["total_power_to_grid"], color=green[0], width=1))
        bars.append(plt.bar(9, res_val_jul_e_delta["total_power_to_grid"], color=blue[0], width=1))
        bars.append(plt.bar(10, res_val_jul_e_delta2["total_power_to_grid"], color=blue[2], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                text = f'{height:.2f}'
                plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')
        plt.ylabel("Power [kWh]")
        plt.title("Power quantities district 3 (match crit flex energy, nCH=nB=5)")  # Title of the plot
        plt.xticks([1, 5, 9], ["Traded power", "Power from grid", "Power to grid"])


if match_crit == "price":
    if plot_kpi == "dem, sup, trade":
        df_head_p_dem = df_time_apr_p_dem.head(168)
        df_head_p_sup = df_time_apr_p_sup.head(168)
        df_head_p_trade = df_time_apr_p_trade.head(168)
        plt.plot(df_head_p_dem["Timestep"], df_head_p_dem["Total demand"], color=red[1], label="Demand")
        plt.plot(df_head_p_sup["Timestep"], df_head_p_sup["Total supply"], color=blue[1], label="Supply")
        plt.plot(df_head_p_trade["Timestep"], df_head_p_trade["Total traded power"], color=green[1], label="Traded Power")
        plt.title("Trading within district 3 (April, match crit price, nCH=36, nB=5)")  # Title of the plot
    elif plot_kpi == "mscf, mdcf":
        plt.bar(0, res_val_jan_e["mscf_month"], color=red[1], label="MSCF", width=1)
        plt.bar(1, res_val_jan_e["mdcf_month"], color=blue[1], label="MDCF", width=1)
        plt.bar(3, res_val_apr_e["mscf_month"], color=red[2], width=1)
        plt.bar(4, res_val_apr_e["mdcf_month"], color=blue[2], width=1)
        plt.ylabel("Percentage [%]")  # Y-axis label
        plt.title("MSCF and MDCF district 3 (match crit price, nCH=36, nB=5)")  # Title of the plot
        plt.xticks([0.5, 3.5], ["January", "April"])

if match_crit == "quantity":
    if plot_kpi == "dem, sup, trade":
        df_head_q_dem = df_time_apr_q_dem.head(168)
        df_head_q_sup = df_time_apr_q_sup.head(168)
        df_head_q_trade = df_time_apr_q_trade.head(168)
        plt.plot(df_head_q_dem["Timestep"], df_head_q_dem["Total demand"], color=red[1], label="Demand")
        plt.plot(df_head_q_sup["Timestep"], df_head_q_sup["Total supply"], color=blue[1], label="Supply")
        plt.plot(df_head_q_trade["Timestep"], df_head_q_trade["Total traded power"], color=green[1], label="Traded Power")
        plt.title("Trading within district 3 (April, match crit quantity, nCH=36, nB=5)")  # Title of the plot
    elif plot_kpi == "mscf, mdcf":
        plt.rcParams["font.family"] = "Times New Roman"
        plt.bar(0, res_val_jan_e["mscf_month"], color=red[1], label="MSCF", width=1)
        plt.bar(1, res_val_jan_e["mdcf_month"], color=blue[1], label="MDCF", width=1)
        plt.bar(3, res_val_apr_e["mscf_month"], color=red[1], width=1)
        plt.bar(4, res_val_apr_e["mdcf_month"], color=blue[1], width=1)
        plt.ylabel("Percentage [%]")  # Y-axis label
        plt.title("MSCF and MDCF district 3 (match crit quantity, nCH=36, nB=5)")  # Title of the plot
        plt.xticks([0.5, 3.5], ["January", "April"])
        # change font to times new roman

plt.legend()
# only horizontal grid lines
# plt.grid(axis='y')
plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/Plots/Quartier_3_"+plot_kpi+" "+match_crit+".svg")
plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/Plots/Quartier_3_"+plot_kpi+" "+match_crit+".png")
plt.show()



















"""
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
#df_val_jan = pd.DataFrame(results_val_jan)

# df_time_apr = pd.DataFrame(results_time_apr)
df_val_apr = pd.DataFrame(results_val_apr)

df_time_jul = pd.DataFrame(results_time_jul)
#df_val_jul = pd.DataFrame(results_val_jul)


# Create a DataFrame directly from the nested dictionary
df_time_apr = pd.DataFrame(list(results_time_apr["average_trade_price"].items()), columns=["Timestep", "average_trade_price"])
#df_val_apr = pd.DataFrame(list(results_time_apr["average_trade_price"].items()), columns=["Timestep", "average_trade_price"])

# ------------ PLOTTING ------------

# choose criteria to plot
plot_kpi = "test"

# customizing the plot
plt.figure(figsize=(10, 5))
plt.xlabel("Timesteps [h]")  # X-axis label
#plt.grid()
#time_steps = len(df_time_apr["total_demand"])

if plot_kpi == "test_time":
    plt.ylabel("Price [€/kWh]")  # Y-axis label
    plt.ylabel("Power [kW]")  # Y-axis label

    plt.plot(df_time_apr["Timestep"], df_time_apr["total_demand"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["total_supply"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["traded_power"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["scf"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["dcf"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["average_trade_price"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["power_from_grid"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["power_to_grid"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["additional_revenue"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["saved_costs"], color=green[1], label="April")
    plt.plot(df_time_apr["Timestep"], df_time_apr["gain"], color=green[1], label="April")

    plt.title("Average price district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "test_val":
    plt.ylabel("Price [€/kWh]")  # Y-axis label
    plt.ylabel("Power [kW]")  # Y-axis label

    plt.plot(df_val_apr["Timestep"], df_time_apr["scf_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["dcf_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["mscf_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["mdcf_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_supply_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_demand_month"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_traded_power"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_average_trade_price"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_power_from_grid"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_power_to_grid"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_additional_revenue"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_saved_costs"], color=green[1], label="April")
    plt.plot(df_val_apr["Timestep"], df_time_apr["total_gain"], color=green[1], label="April")

    plt.title("Test")  # Title of the plot
    plt.legend()

if plot_kpi == "dcf_month":
    plt.ylabel("SCF")  # Y-axis label
    plt.bar(0, df_val_jan["scf_month"], color=green[1], label="January")
    #plt.bar(1, 3, color=red[1], label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["dcf_month"], color=blue[1], label="April")
    plt.bar(2, df_val_jul["dcf_month"], color=red[1], label="July")
    plt.title("DCF district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_demand":
    df_week = df_time_apr.head(168)
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df_week["total_demand"], color=red[1], label="Total demand")
    plt.plot(df_week["total_supply"], color=green[1], label="Total supply")
    plt.plot(df_week["traded_power"], color=blue[1], label="Traded power")
    # plt.plot(df_week["power_to_grid"], color="orange", label="Power to grid")
    # plt.plot(df_week["power_from_grid"], color="purple", label="Power from grid")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "total_traded_power":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_traded_power"], color=green[1], label="January")
    #plt.bar(1, 3, color=red[1], label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_traded_power"], color=blue[1], label="April")
    plt.bar(2, df_val_jul["total_traded_power"], color=red[1], label="July")
    plt.title("Total traded power district 3")  # Title of the plot
    plt.legend()



if plot_kpi == "total_power_to_grid":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_power_to_grid"], color=green[1], label="January")
    #plt.bar(1, 3, color=red[1], label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_power_to_grid"], color=blue[1], label="April")
    plt.bar(2, df_val_jul["total_power_to_grid"], color=red[1], label="July")
    plt.title("total_power_to_grid district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_power_from_grid":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_power_from_grid"], color=green[1], label="January")
    #plt.bar(1, 3, color=red[1], label="SCF = 1", width=0.05)
    plt.bar(1, df_val_apr["total_power_from_grid"], color=blue[1], label="April")
    plt.bar(2, df_val_jul["total_power_from_grid"], color=red[1], label="July")
    plt.title("Total_power_from_grid district 3")  # Title of the plot
    plt.legend()

if plot_kpi == "total_demand_month":
    plt.ylabel("Power [kWh]")  # Y-axis label
    plt.bar(0, df_val_jan["total_demand_month"], color=green[1], label="Demand", width=1)
    plt.bar(1, df_val_jan["total_power_from_grid"], color="lightgreen", label="Grid import", width=1)

    #plt.bar(1, 3, color=red[1], label="SCF = 1", width=0.05)
    plt.bar(3, df_val_apr["total_demand_month"], color=green[1], width=1)
    plt.bar(4, df_val_apr["total_power_from_grid"], color="lightgreen", width=1)

    plt.bar(6, df_val_jul["total_demand_month"], color=green[1], width=1)
    plt.bar(7, df_val_jul["total_power_from_grid"], color="lightgreen", width=1)

    plt.xticks([0.5, 3.5, 6.5], ["January", "April", "July"])

    plt.title("total_demand_month district 3")  # Title of the plot
    plt.legend()


if plot_kpi == "traded_power":
    plt.ylabel("Power [kW]")  # Y-axis label
    plt.plot(df_time_jul["total_demand"], color=red[1], label="Total demand")
    plt.plot(df_time_jul["total_supply"], color=green[1], label="Total supply")
    plt.title("Total demand and supply within district")  # Title of the plot
    plt.legend()

if plot_kpi == "saved_costs":
    df_week = df_time_jul.head(168) # only plot the first week
    plt.ylabel("Costs [€]")  # Y-axis label
    # plt.plot(df_week["saved_costs"], color=red[1], label="Saved costs")
    # plt.plot(df_week["additional_revenue"], color=green[1], label="Additional Revenue")

    cumulative_values = df_time_jul["gain"].cumsum()
    plt.plot(cumulative_values.index, cumulative_values.values, color=blue[1], label="Gain")
    plt.title("Saved costs within district")  # Title of the plot
    plt.legend()

plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/plots/Quartier_3_"+plot_kpi+".svg")
plt.show()


"""

