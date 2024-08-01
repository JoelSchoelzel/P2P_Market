import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle


def calc_results_p2p(par_rh, block_length, nego_results, opti_res, grid_transaction, params):

    last_n_opt = par_rh["n_opt"]
    time_steps = []
    for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + block_length):
        time_steps.append(i)

    # --------------------- DGOC --------------------- #

    total_p_purchase = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    total_feed_in = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_p_purchase[t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000 # kW
                total_feed_in[t - par_rh["hour_start"][0]] += (opti_res[n_opt][n][8]["chp"][t] \
                                                              + opti_res[n_opt][n][8]["pv"][t]) / 1000 # kW

    denominator_dgoc = []
    numerator_dgoc = []
    for t in range(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]):
        numerator_dgoc.append(2 * min(total_p_purchase[t], total_feed_in[t]))
        denominator_dgoc.append(total_p_purchase[t] + total_feed_in[t])
    DGOC = sum(numerator_dgoc) / sum(denominator_dgoc)

    # --------------------- peak loads --------------------- #

    residual_load = total_p_purchase - total_feed_in
    peak_feed_in = -1*min(residual_load)  # kW
    if peak_feed_in < 0:
        peak_feed_in=0
    peak_purchase = max(residual_load)  # kW

    # --------------------- storage losses  --------------------- #

    bat_losses = []
    tes_losses = []
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                bat_losses.append(0.03 * (opti_res[n_opt][n][3]["bat"][t]
                                          + opti_res[n_opt][n][5]["bat"][t]
                                          + opti_res[n_opt][n][6]["bat"][t]))
                tes_losses.append(0.03 * opti_res[n_opt][n][3]["tes"][t])
    bat_losses = sum(bat_losses) /1000 # kWh
    tes_losses = sum(tes_losses) /1000 # kWh

    # --------------------- energy exchange with higher grid --------------------- #

    district_import = []
    district_export = []
    for t in range(len(residual_load)):
        if residual_load[t] > 0:
            district_import.append(residual_load[t])
        else:
            district_export.append(residual_load[t])
    district_import = sum(district_import)     # kWh
    district_export = sum(district_export) *-1 # kWh


    # --------------------- trade price, revenue, costs, gain  ---------------------

    traded_power = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    additional_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    saved_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    gain = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    for opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                # valid_time_steps = {k: v for k, v in nego_results[opt][round_nb][match]["quantity"].items() if isinstance(k, int)}
                for t in range(par_rh["hour_start"][opt], par_rh["hour_start"][opt] + block_length):
                    if isinstance(nego_results[opt][round_nb][match]["quantity"][t], float):  # valid_time_steps
                        #price[t][match] = nego_results[opt][round_nb][match]["price"][t]  # €/kWh
                        traded_power[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                            nego_results[opt][round_nb][match]["quantity"][t]/1000  # kWh
                        traded_power[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] +=  \
                            nego_results[opt][round_nb][match]["quantity"][t] / 1000  # kWh
                        additional_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] += \
                            nego_results[opt][round_nb][match]["additional_revenue"][t]  # €/kWh
                        saved_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                            nego_results[opt][round_nb][match]["saved_costs"][t]  # €/kWh
                        trading_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] += \
                            nego_results[opt][round_nb][match]["trading_revenue"][t]  # €/kWh
                        trading_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                            nego_results[opt][round_nb][match]["trading_cost"][t]  # €/kWh
                        gain[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] = \
                            saved_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]]
                        gain[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] = \
                            additional_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]]

    traded_power_per_building = np.zeros(len(opti_res[0]))
    trading_costs_per_building  = np.zeros(len(opti_res[0]))
    saved_costs_per_building = np.zeros(len(opti_res[0]))
    trading_revenue_per_building  = np.zeros(len(opti_res[0]))
    additional_revenue_per_building = np.zeros(len(opti_res[0]))
    gain_per_building = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        traded_power_per_building[n] = np.sum(traded_power[n,:])
        trading_costs_per_building[n] = np.sum(trading_costs[n,:])
        saved_costs_per_building[n] = np.sum(saved_costs[n,:])
        trading_revenue_per_building[n] = np.sum(trading_revenue[n,:])
        additional_revenue_per_building[n] = np.sum(additional_revenue[n,:])
        gain_per_building[n] = np.sum(gain[n,:])

    traded_power_total = np.sum(traded_power_per_building)
    additional_revenue_total = np.sum(additional_revenue_per_building)
    saved_costs_total = np.sum(saved_costs_per_building)
    gain_total = np.sum(gain_per_building)
    trading_costs_total = np.sum(trading_costs_per_building)
    trading_revenue_total = np.sum(trading_revenue_per_building)

    av_prices_buy = trading_costs_total / traded_power_total
    av_prices_sell = trading_revenue_total / traded_power_total

    gain_total_over_time = np.zeros(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0])
    for t in range(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]):
        gain_total_over_time[t] = np.sum(gain[:,t])

    # --------------------- absolute_energy_cost  --------------------- #

    total_cost = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    total_cost = total_cost + trading_costs - trading_revenue
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["costs_power_from_grid"][n][t] \
                                                           - grid_transaction[n_opt]["revenue_power_to_grid"][n][t] \
                                                           + opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"]
    total_cost_per_buildung = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        total_cost_per_buildung[n] = np.sum(total_cost[n,:])

    total_cost_without_LEM = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost_without_LEM[n,t - par_rh["hour_start"][0]] += opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"] \
                                                                         + opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000* params["eco"]["pr", "el"] \
                                                                         - (opti_res[n_opt][n][8]["chp"][t] + opti_res[n_opt][n][8]["pv"][t]) / 1000*params["eco"]["sell_pv"] # kW
    total_cost_without_LEM_per_buildung = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        total_cost_without_LEM_per_buildung[n] = np.sum(total_cost_without_LEM[n,:])

    # ----------- traded supply and demand quantities   ---------------------

    denominator_total_demand = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    denominator_total_supply = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_demand = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_supply = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                denominator_total_demand[n, t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t]/1000
                denominator_total_supply[n, t - par_rh["hour_start"][0]] += opti_res[n_opt][n][8]["chp"][t]/1000 \
                                                              + opti_res[n_opt][n][8]["pv"][t]/1000
                if denominator_total_demand[n, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_demand[n, t - par_rh["hour_start"][0]] = traded_power[n, t - par_rh["hour_start"][0]]
                if denominator_total_supply[n, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_supply[n, t - par_rh["hour_start"][0]] = traded_power[n, t - par_rh["hour_start"][0]]

    mSCF_bd = {}
    mDCF_bd = {}
    for n in range(len(opti_res[0])):
        if sum(denominator_total_supply[n,:]) != 0:
            mSCF_bd[n] = sum(nominator_total_supply[n,:]) / sum(denominator_total_supply[n,:])
        if sum(denominator_total_demand[n, :]) != 0:
            mDCF_bd[n] =  sum(nominator_total_demand[n,:]) / sum(denominator_total_demand[n,:])

    mSCF = sum(sum(nominator_total_supply)) / sum(sum(denominator_total_supply))
    mDCF =  sum(sum(nominator_total_demand)) / sum(sum(denominator_total_demand))

    # --------------------- STORE THE RESULTS ---------------------

    results = {

        "DGOC": DGOC,
        "peak_feed_in": peak_feed_in,
        "peak_purchase": peak_purchase,
        "district_import": district_import,
        "district_export": district_export,

        "traded_power": traded_power,
        "additional_revenue": additional_revenue,
        "saved_costs": saved_costs,
        "gain": gain,
        "gain_total_over_time": gain_total_over_time,

        "traded_power_per_building": traded_power_per_building,
        "trading_costs_per_building": trading_costs_per_building,
        "saved_costs_per_building": saved_costs_per_building,
        "trading_revenue_per_building": trading_revenue_per_building,
        "additional_revenue_per_building": additional_revenue_per_building,
        "gain_per_building": gain_per_building,

        "traded_power_total" : traded_power_total,
        "additional_revenue_total": additional_revenue_total,
        "saved_costs_total": saved_costs_total,
        "gain_total": gain_total,
        "trading_costs_total": trading_costs_total,
        "trading_revenue_total": trading_revenue_total,
        "av_prices_buy": av_prices_buy,
        "av_prices_sell": av_prices_sell,

        "total_cost": total_cost,
        "total_cost_per_buildung": total_cost_per_buildung,
        "total_cost_without_LEM_per_buildung": total_cost_without_LEM_per_buildung,

        "traded_supply_bids_per_building": mSCF_bd,
        "traded_demands_bids_per_building": mDCF_bd,
        "traded_supply_bids": mSCF,
        "traded_demands_bids": mDCF,

        "bat_losses": bat_losses,
        "tes_losses": tes_losses,

        "residual_load":residual_load,
        "total_p_purchase":total_p_purchase,
        "total_feed_in": total_feed_in,
    }
    return results

def plots():


    import pickle
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    xlabel_fontsize = 16
    ylabel_fontsize = 16
    xtick_fontsize = 16
    ytick_fontsize = 16
    legend_fontsize = 16


    results = {}
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_random.p", "rb") as file_res_list:
        results[str(1)+"_"+str(1)+"_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_quantity.p", "rb") as file_res_list:
        results[str(1) + "_" + str(1) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_flex.p", "rb") as file_res_list:
        results[str(1) + "_" + str(1) + "_flex"] = pickle.load(file_res_list)

    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_random.p", "rb") as file_res_list:
        results[str(1) + "_" + str(3) + "_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_quantity.p", "rb") as file_res_list:
        results[str(1) + "_" + str(3) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_flex.p", "rb") as file_res_list:
        results[str(1) + "_" + str(3) + "_flex"] = pickle.load(file_res_list)

    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_random.p", "rb") as file_res_list:
        results[str(1) + "_" + str(5) + "_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_quantity.p", "rb") as file_res_list:
        results[str(1) + "_" + str(5) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_flex.p", "rb") as file_res_list:
        results[str(1) + "_" + str(5) + "_flex"] = pickle.load(file_res_list)

    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len1_random.p", "rb") as file_res_list:
        results[str(10)+"_"+str(1)+"_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len1_quantity.p", "rb") as file_res_list:
        results[str(10) + "_" + str(1) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len1_flex.p", "rb") as file_res_list:
        results[str(10) + "_" + str(1) + "_flex"] = pickle.load(file_res_list)

    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len3_random.p", "rb") as file_res_list:
        results[str(10) + "_" + str(3) + "_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len3_quantity.p", "rb") as file_res_list:
        results[str(10) + "_" + str(3) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len3_flex.p", "rb") as file_res_list:
        results[str(10) + "_" + str(3) + "_flex"] = pickle.load(file_res_list)

    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_random.p", "rb") as file_res_list:
        results[str(10) + "_" + str(5) + "_random"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_quantity.p", "rb") as file_res_list:
        results[str(10) + "_" + str(5) + "_quantity"] = pickle.load(file_res_list)
    with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_flex.p", "rb") as file_res_list:
        results[str(10) + "_" + str(5) + "_flex"] = pickle.load(file_res_list)


    """
        dgoc_heat_map[0, x] = np.round(results["DGOC"]*100, 2)
        peak_purchase_heat_map[0, x] = int(np.round(results["peak_purchase"], 0))
        peak_feedin_heat_map[0, x] = int(np.round(results["peak_feed_in"], 0))
        traded_supply_bids_heat_map[0, x] = np.round(results["traded_supply_bids"]*100, 2)
        traded_demand_bids_heat_map[0, x] = np.round(results["traded_demands_bids"]*100, 2)
        energy_losses_heat_map [0, x] = np.round((results["bat_losses"]+results["bat_losses"])/1000, 2) # MWh
        traded_power_heat_map[0, x] = np.round(results["traded_power_total"]/1000, 2)  # MWh
        x += 1
    """


    #### ------------------- dgoc_heat_map ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/dgoc_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Benutzerdefinierte Achsenwerte
    x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
    y_labels = ["1", "10"]  # Beispielwerte für y-Achse
    # Erstellen der Heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(dgoc_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
    plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
    plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
    plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()

    #### ------------------- traded_supply_bids ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_supply_bids_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Creating the DataFrame
    data = {
        ('random', 1): [results["1_1_random"]["traded_supply_bids"]*100, results["1_3_random"]["traded_supply_bids"]*100, results["1_5_random"]["traded_supply_bids"]*100],
        ('random', 10): [results["10_1_random"]["traded_supply_bids"]*100, results["10_3_random"]["traded_supply_bids"]*100, results["10_5_random"]["traded_supply_bids"]*100],
        ('quantity', 1): [results["1_1_quantity"]["traded_supply_bids"]*100, results["1_3_quantity"]["traded_supply_bids"]*100, results["1_5_quantity"]["traded_supply_bids"]*100],
        ('quantity', 10): [results["10_1_quantity"]["traded_supply_bids"]*100, results["10_3_quantity"]["traded_supply_bids"]*100, results["10_5_quantity"]["traded_supply_bids"]*100],
        ('flexibility', 1): [results["1_1_flex"]["traded_supply_bids"]*100, results["1_3_flex"]["traded_supply_bids"]*100, results["1_5_flex"]["traded_supply_bids"]*100],
        ('flexibility', 10): [results["10_1_flex"]["traded_supply_bids"]*100, results["10_3_flex"]["traded_supply_bids"]*100, results["10_5_flex"]["traded_supply_bids"]*100],
    }
    df = pd.DataFrame(data, index=[1, 3, 5])
    # Plotting the heatmap
    plt.figure(figsize=(14, 8))
    sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
    plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
    plt.xticks(fontsize=xtick_fontsize)
    plt.yticks(fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()


    #### ------------------- traded_demand_bids ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_demand_bids_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Creating the DataFrame
    data = {
        ('random', 1): [results["1_1_random"]["traded_demand_bids"]*100, results["1_3_random"]["traded_demand_bids"]*100, results["1_5_random"]["traded_demand_bids"]*100],
        ('random', 10): [results["10_1_random"]["traded_demand_bids"]*100, results["10_3_random"]["traded_demand_bids"]*100, results["10_5_random"]["traded_demand_bids"]*100],
        ('quantity', 1): [results["1_1_quantity"]["traded_demand_bids"]*100, results["1_3_quantity"]["traded_demand_bids"]*100, results["1_5_quantity"]["traded_demand_bids"]*100],
        ('quantity', 10): [results["10_1_quantity"]["traded_demand_bids"]*100, results["10_3_quantity"]["traded_demand_bids"]*100, results["10_5_quantity"]["traded_demand_bids"]*100],
        ('flexibility', 1): [results["1_1_flex"]["traded_demand_bids"]*100, results["1_3_flex"]["traded_demand_bids"]*100, results["1_5_flex"]["traded_demand_bids"]*100],
        ('flexibility', 10): [results["10_1_flex"]["traded_demand_bids"]*100, results["10_3_flex"]["traded_demand_bids"]*100, results["10_5_flex"]["traded_demand_bids"]*100],
    }
    df = pd.DataFrame(data, index=[1, 3, 5])
    # Plotting the heatmap
    plt.figure(figsize=(14, 8))
    sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
    plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
    plt.xticks(fontsize=xtick_fontsize)
    plt.yticks(fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()


    #### ------------------- traded_power ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_power_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Creating the DataFrame
    data = {
        ('random', 1): [results["1_1_random"]["traded_power_total"] / 1000,
                        results["1_3_random"]["traded_power_total"] / 1000,
                        results["1_5_random"]["traded_power_total"] / 1000],
        ('random', 10): [results["10_1_random"]["traded_power_total"] / 1000,
                         results["10_3_random"]["traded_power_total"] / 1000,
                         results["10_5_random"]["traded_power_total"] / 1000],
        ('quantity', 1): [results["1_1_quantity"]["traded_power_total"] / 1000,
                          results["1_3_quantity"]["traded_power_total"] / 1000,
                          results["1_5_quantity"]["traded_power_total"] / 1000],
        ('quantity', 10): [results["10_1_quantity"]["traded_power_total"] / 1000,
                           results["10_3_quantity"]["traded_power_total"] / 1000,
                           results["10_5_quantity"]["traded_power_total"] / 1000],
        ('flexibility', 1): [results["1_1_flex"]["traded_power_total"] / 1000,
                             results["1_3_flex"]["traded_power_total"] / 1000,
                             results["1_5_flex"]["traded_power_total"] / 1000],
        ('flexibility', 10): [results["10_1_flex"]["traded_power_total"] / 1000,
                              results["10_3_flex"]["traded_power_total"] / 1000,
                              results["10_5_flex"]["traded_power_total"] / 1000],
    }
    df = pd.DataFrame(data, index=[1, 3, 5])
    # Plotting the heatmap
    plt.figure(figsize=(14, 8))
    sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
    plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
    plt.xticks(fontsize=xtick_fontsize)
    plt.yticks(fontsize=ytick_fontsize)
    # Titel
    # plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()

    #### ------------------- peak_feedin ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/peak_feedin_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Benutzerdefinierte Achsenwerte
    x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
    y_labels = ["1", "10"]  # Beispielwerte für y-Achse
    # Erstellen der Heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(peak_feedin_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
    plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
    plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
    plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()

    #### ------------------- peak_purchase ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/peak_purchase_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Benutzerdefinierte Achsenwerte
    x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
    y_labels = ["1", "10"]  # Beispielwerte für y-Achse
    # Erstellen der Heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(peak_purchase_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
    plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
    plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
    plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()

    #### ------------------- losses ------------------- ####
    # Hauptfarbe
    main_color = "#00549F"
    # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
    cmap = sns.light_palette(main_color, as_cmap=True)
    # Pfad zum Speichern der Datei
    save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/energy_losses_heat_map.png"
    # Auflösung (DPI)
    dpi = 300
    # Benutzerdefinierte Achsenwerte
    x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
    y_labels = ["1", "10"]  # Beispielwerte für y-Achse
    # Erstellen der Heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(energy_losses_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
    # Achsenbeschriftungen
    plt.xlabel("Matching creLength of block bids", fontsize=xlabel_fontsize)
    plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
    plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
    plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
    # Titel
    #plt.title("Generic 3x3 Heatmap")
    # Speichern der Heatmap als PNG
    plt.savefig(save_path, dpi=dpi)
    # Anzeige der Heatmap
    plt.show()


    # --------------------- Balkendiagramm für Nutzergruppen --------------------- #

    import pickle
    import matplotlib.pyplot as plt
    import numpy as np
    av_gain_per_group = np.zeros((9, 6))
    min_gain_per_group = np.zeros((9, 6))
    max_gain_per_group = np.zeros((9, 6))

    results_block_bid_length_r1 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_flex.p",
                                   "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len1_flex.p",
                                   "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_flex.p",
                                   "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len3_flex.p",
                                   "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_flex.p",
                                   "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_flex.p",]
    x = 0
    for i in results_block_bid_length_r1:
        with open(i, "rb") as file_res_list:
            results = pickle.load(file_res_list)
        for group in range(0, 9*5, 5):
            av_gain_per_group[int(group/5), x] = int(np.mean(results["gain_per_building"][group:group+5]))
            min_gain_per_group[int(group/5), x] = int(np.min(results["gain_per_building"][group:group+5]))
            max_gain_per_group[int(group/5), x] = int(np.max(results["gain_per_building"][group:group+5]))
        x += 1

    num_user_groups = 9
    num_bars_per_group = 6
    # Farben und Schraffierungen nach RWTH Aachen
    colors = ['#00549F', '#00549F', '#8EBAE5', '#8EBAE5', '#AAAAAA', '#AAAAAA']
    hatch_patterns = ['', '//', '', '//', '', '//']
    # Erstellen des Balkendiagramms
    fig, ax = plt.subplots(figsize=(15, 8))
    bar_width = 0.1
    bar_positions = np.arange(num_user_groups)
    for i in range(num_bars_per_group):
        bars = ax.bar(bar_positions + i * bar_width, av_gain_per_group[:, i], bar_width,
                      label=f'Bar {i + 1}', color=colors[i], hatch=hatch_patterns[i])
        # Hinzufügen von Minimal- und Maximalwerten als Kreise
        for j in range(num_user_groups):
            ax.plot(bar_positions[j] + i * bar_width, min_gain_per_group[j, i], 'o', color='black')
            ax.plot(bar_positions[j] + i * bar_width, max_gain_per_group[j, i], 'o', color='red')
    # Achsenbeschriftungen
    ax.set_xlabel('User groups', fontsize=xlabel_fontsize)
    ax.set_ylabel('Gain', fontsize=ylabel_fontsize)
    ax.set_xticks(bar_positions + (num_bars_per_group - 1) * bar_width / 2)
    ax.set_xticklabels([f'Group {i + 1}' for i in range(num_user_groups)])
    ax.set_ylim(0, 5500)
    # Legende
    ax.legend()
    # Titel
    plt.title('User Groups Gain')
    # Anzeige des Diagramms
    plt.show()

    ### -------------------- gain as times series -------------------- ###

    import pickle
    import matplotlib.pyplot as plt
    import numpy as np
    import tikzplotlib

    gain_per_group_over_time = np.zeros((9, 8760))
    gain_per_building = np.zeros(45)
    total_cost_per_buildung = np.zeros(45)
    total_cost_without_LEM_per_buildung = np.zeros(45)

    results_block_bid_length_r1 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_flex.p"]

    for i in results_block_bid_length_r1:
        with open(i, "rb") as file_res_list:
            results = pickle.load(file_res_list)
        for group in range(0, 9*5, 5):
            for t in range(8759):
                gain_per_group_over_time[int(group/5), t] = np.sum(results["gain"][group:group+5, t])
        total_gain_over_time = results["gain_total_over_time"]
        for nb in range(45):
            gain_per_building[nb] = results["gain_per_building"][nb]
            total_cost_per_buildung = results["total_cost_per_buildung"]
            total_cost_without_LEM_per_buildung = results["total_cost_without_LEM_per_buildung"]
    gain_per_group_over_time = np.cumsum(gain_per_group_over_time, axis=1)

    num_series = 9
    hours_per_year = 8760
    data = gain_per_group_over_time
    # Konvertiere Stunden in Tage (für die x-Achsen-Beschriftung)
    x_values = np.linspace(0, 365, hours_per_year)
    title_fontsize = 20
    xlabel_fontsize = 16
    ylabel_fontsize = 16
    xtick_fontsize = 16
    ytick_fontsize = 16
    legend_fontsize = 16
    # Legendenlabels
    legend_labels = ["User group 1", "User group 2", "User group 3", "User group 4", "User group 5",
                     "User group 6", "User group 7", "User group 8", "User group 9"]

    plt.figure(figsize=(15, 8))
    for i in range(data.shape[0]):
        plt.plot(x_values, data[i], label=legend_labels[i], linewidth=1.8)
    # Achsenbeschriftungen
    plt.xlabel('Day', fontsize=xlabel_fontsize)
    plt.ylabel('Gain in €', fontsize=ylabel_fontsize)
    plt.ylim(0, 8000)
    plt.xlim(0, 365)
    # Setzt die xticks auf ganze Zahlen für Tage
    plt.xticks(np.arange(0, 366, step=30), fontsize=xtick_fontsize)
    plt.yticks(fontsize=ytick_fontsize)
    # Legende
    plt.legend(fontsize=legend_fontsize)
    # Titel
    #plt.title("title", fontsize=title_fontsize)
    # Anzeige der Grafik
    tikzplotlib.save("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/gain_per_group_over_time_test.tex")  # , axis_height ='5 cm',axis_width='15 cm')
    plt.show()

    return


def calc_gain():

    import pickle
    import matplotlib.pyplot as plt
    import numpy as np
    import tikzplotlib

    xlabel_fontsize = 16
    ylabel_fontsize = 16
    xtick_fontsize = 16
    ytick_fontsize = 16
    legend_fontsize = 16

    list_opti_res_dec = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_random.p"]
    for i in list_opti_res_dec:
        with open(i, "rb") as file_res_list:
            results_dec = pickle.load(file_res_list)

    results_block_bid_length_r1 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_quantity.p"]
    for i in results_block_bid_length_r1:
        with open(i, "rb") as file_res_list:
            results_bb = pickle.load(file_res_list)

    list_par_rh = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/par_rh.p"]
    for i in list_par_rh:
        with open(i, "rb") as file_par_rh_list:
            par_rh = pickle.load(file_par_rh_list)

    list_par_rh5 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/par_rh5.p"]
    for i in list_par_rh5:
        with open(i, "rb") as file_par_rh5_list:
            par_rh5 = pickle.load(file_par_rh5_list)

    list_opti_res = ["C:/Users/jsc/Python/Results/AppliedEnergy/opti_res/opti_res.p"]
    for i in list_opti_res:
        with open(i, "rb") as file_opti_res_list:
            opti_res = pickle.load(file_opti_res_list)

    list_mar_dict = ["C:/Users/jsc/Python/Results/AppliedEnergy/opti_res/mar_dict_r10_b5_quan.p"]
    for i in list_mar_dict:
        with open(i, "rb") as file_mar_dict_list:
            mar_dict = pickle.load(file_mar_dict_list)

    total_p_purchase = np.zeros((45, 8760))
    total_feed_in = np.zeros((45, 8760))
    for n_opt in range(par_rh["n_opt"] - int(36/1)-1):
        for n in range(45):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + 1):
                total_p_purchase[n, t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000 # kW
                total_feed_in[n, t - par_rh["hour_start"][0]] += (opti_res[n_opt][n][8]["chp"][t] \
                                                              + opti_res[n_opt][n][8]["pv"][t]) / 1000 # kW

    cost_per_building_without_LEM = np.sum(total_p_purchase, axis=1) * 0.36
    revenue_per_building_without_LEM = np.sum(total_feed_in, axis=1)* 0.081

    costs_power_from_grid = np.zeros((45, 8760))
    revenue_power_to_grid = np.zeros((45, 8760))
    for n_opt in range(par_rh5["n_opt"] - int(36/5)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh5["hour_start"][n_opt], par_rh5["hour_start"][n_opt] + 5):
                costs_power_from_grid[n, t - par_rh5["hour_start"][0]] += mar_dict["transactions_with_grid"][n_opt]["costs_power_from_grid"][n][t]
                revenue_power_to_grid[n, t - par_rh5["hour_start"][0]] += mar_dict["transactions_with_grid"][n_opt]["revenue_power_to_grid"][n][t]


    trading_costs_per_building = results_bb["trading_costs_per_building"]+np.sum(costs_power_from_grid, axis=1)
    trading_revenue_per_building = results_bb["trading_revenue_per_building"]+np.sum(costs_power_from_grid, axis=1)
    gain_per_bulding = cost_per_building_without_LEM - trading_costs_per_building + trading_revenue_per_building - revenue_per_building_without_LEM
    rel_gain_per_bulding = results_bb["total_cost_per_buildung"]/ results_dec["total_cost_without_LEM_per_buildung"]

    av_rel_gain_per_group = np.zeros(9)
    min_rel_gain_per_group = np.zeros(9)
    max_rel_gain_per_group = np.zeros(9)

    for group in range(0, 9 * 5, 5):
        av_rel_gain_per_group[int(group / 5)] = 100-np.round(np.mean(rel_gain_per_bulding[group:group + 5])*100,2)
        min_rel_gain_per_group[int(group / 5)] = 100-np.round(np.max(rel_gain_per_bulding[group:group + 5])*100,2)
        max_rel_gain_per_group[int(group / 5)] = 100-np.round(np.min(rel_gain_per_bulding[group:group + 5])*100,2)


    num_user_groups = 9
    num_bars_per_group = 1
    # Farben und Schraffierungen nach RWTH Aachen
    colors = ['#CC071E',]
    # Legendenlabels
    legend_labels = ["User group 1", "User group 2", "User group 3", "User group 4", "User group 5",
                     "User group 6", "User group 7", "User group 8", "User group 9"]
    # Erstellen des Balkendiagramms
    fig, ax = plt.subplots(figsize=(20, 8))
    bar_width = 0.4
    bar_positions = np.arange(num_user_groups)
    bars = ax.bar(bar_positions, av_rel_gain_per_group, bar_width, color=colors[0])
    # Hinzufügen von Minimal- und Maximalwerten als Kreise
    ax.plot(bar_positions, min_rel_gain_per_group, 'x', color='black')
    ax.plot(bar_positions, max_rel_gain_per_group, 'x', color='red')
    # Achsenbeschriftungen
    ax.set_xlabel('User groups', fontsize=xlabel_fontsize)
    ax.set_ylabel('Relative cost savings in %', fontsize=ylabel_fontsize)
    ax.set_xticks(bar_positions + (num_bars_per_group - 1) * bar_width / 2)
    ax.set_xticklabels([f'{i + 1}' for i in range(num_user_groups)], fontsize=xtick_fontsize)
    plt.yticks(ticks=[0,10,20,30,40,50, 60],fontsize=ytick_fontsize)
    ax.set_ylim(0, 60)
    # Legende
    ax.legend()
    # add horizontal gridlines
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    # Titel
    #plt.title('User Groups Gain')
    # Anzeige des Diagramms
    tikzplotlib.save("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/rel_savings_per_group.tex", axis_height ='5 cm',axis_width='15 cm')
    plt.show()

    av_abs_gain_per_group = np.zeros(9)
    min_abs_gain_per_group = np.zeros(9)
    max_abs_gain_per_group = np.zeros(9)

    for group in range(0, 9 * 5, 5):
        av_abs_gain_per_group[int(group / 5)] = np.round(np.mean(gain_per_bulding[group:group + 5]), 0)
        min_abs_gain_per_group[int(group / 5)] = np.round(np.min(gain_per_bulding[group:group + 5]), 0)
        max_abs_gain_per_group[int(group / 5)] = np.round(np.max(gain_per_bulding[group:group + 5]), 0)

    num_user_groups = 9
    num_bars_per_group = 1
    # Farben und Schraffierungen nach RWTH Aachen
    colors = ['#D85C41', ]
    # Legendenlabels
    legend_labels = ["User group 1", "User group 2", "User group 3", "User group 4", "User group 5",
                     "User group 6", "User group 7", "User group 8", "User group 9"]
    # Erstellen des Balkendiagramms
    fig, ax = plt.subplots(figsize=(20, 8))
    bar_width = 0.4
    bar_positions = np.arange(num_user_groups)
    bars = ax.bar(bar_positions, av_abs_gain_per_group, bar_width, color=colors[0])
    # Hinzufügen von Minimal- und Maximalwerten als Kreise
    ax.plot(bar_positions, min_abs_gain_per_group, 'x', color='black')
    ax.plot(bar_positions, max_abs_gain_per_group, 'x', color='red')
    # Achsenbeschriftungen
    ax.set_xlabel('User groups', fontsize=xlabel_fontsize)
    ax.set_ylabel('Gain in €', fontsize=ylabel_fontsize)
    ax.set_xticks(bar_positions + (num_bars_per_group - 1) * bar_width / 2)
    ax.set_xticklabels([f' {i + 1}' for i in range(num_user_groups)], fontsize=xtick_fontsize)
    plt.yticks(fontsize=ytick_fontsize)
    ax.set_ylim(0, 6000)
    # add horizontal gridlines
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    # Legende
    ax.legend()
    # Titel
    # plt.title('User Groups Gain')
    # Anzeige des Diagramms
    tikzplotlib.save(
        "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/abs_gain_per_group.tex", axis_height ='5 cm',axis_width='15 cm')
    plt.show()



    return