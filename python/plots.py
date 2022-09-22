

import matplotlib.pyplot as plt
import pickle
import pandas as pd

'''
def compute_district_loads(options, par_rh, central_opti_results, weights_typeweeks, params):

    results_ch = {} # combined results of all control horizons
    criteria_typeweeks = {}

    for k in range(options["number_typeWeeks"]):
        results_ch[k] = {"power_from_grid": [],
                         "power_to_grid": [],
                         "gas_from_grid": [],
                         "power_feed": [],
                         "power_demand": [],
                         "power_pv_gen": [],
                         "power_feed_pv_bes": {},
                         "power_feed_chp_bes": {},
                         "power_demand_bes": {},
                         "gas_from_grid_bes": {},
                         }

        for n in range(options["nb_bes"]):
            results_ch[k]["power_feed_pv_bes"][n] = []
            results_ch[k]["power_feed_chp_bes"][n] = []
            results_ch[k]["power_demand_bes"][n] = []
            results_ch[k]["gas_from_grid_bes"][n] = []

        for i in range(par_rh["n_opt"]):
            for t in range(par_rh["time_steps"][i][0], par_rh["time_steps"][i][par_rh["block_duration"][0]]):
                results_ch[k]["power_from_grid"].append(central_opti_results[k][i][19][t])
                results_ch[k]["power_to_grid"].append(central_opti_results[k][i][20][t])
                results_ch[k]["gas_from_grid"].append(central_opti_results[k][i][21][t])
                results_ch[k]["power_feed"].append(central_opti_results[k][i][22][t])
                results_ch[k]["power_demand"].append(central_opti_results[k][i][23][t])
                results_ch[k]["power_pv_gen"].append(sum(central_opti_results[k][i][8][n]["pv"][t] for n in range(options["nb_bes"])))

                for n in range(options["nb_bes"]):
                    results_ch[k]["power_feed_pv_bes"][n].append(central_opti_results[k][i][8][n]["pv"][t])
                    results_ch[k]["power_feed_chp_bes"][n].append(central_opti_results[k][i][8][n]["chp"][t] + central_opti_results[k][i][8][n]["bz"][t] +
                                                                  central_opti_results[k][i][8][n]["bz_sf"][t])
                    results_ch[k]["power_demand_bes"][n].append(central_opti_results[k][i][4][n][t])
                    results_ch[k]["gas_from_grid_bes"][n].append(central_opti_results[k][i][24][n]["boiler"][t] + central_opti_results[k][i][24][n]["chp"][t] +
                                                                 central_opti_results[k][i][24][n]["bz"][t] + central_opti_results[k][i][24][n]["bz_sf"][t])


        criteria_typeweeks[k] = {"E_el_from_grid": sum(results_ch[k]["power_from_grid"])/1000 * par_rh["resolution"][0], # kWh
                         "E_el_to_grid": sum(results_ch[k]["power_to_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_gas_from_grid": sum(results_ch[k]["gas_from_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_el_feed": sum(results_ch[k]["power_feed"]) / 1000 * par_rh["resolution"][0],
                         "E_el_demand": sum(results_ch[k]["power_demand"]) / 1000 * par_rh["resolution"][0],
                         "E_el_pv_gen": sum(results_ch[k]["power_pv_gen"]) / 1000 * par_rh["resolution"][0],
                         "peak_power_transformer_to_grid": max(results_ch[k]["power_to_grid"])/1000, # kW
                         "peak_power_transformer_from_grid": max(results_ch[k]["power_from_grid"])/1000,
                         "E_el_feed_pv_bes": {(n): sum(results_ch[k]["power_feed_pv_bes"][n])/1000 * par_rh["resolution"][0] for n
                                           in range(options["nb_bes"])},
                         "E_el_feed_chp_bes": {(n): sum(results_ch[k]["power_feed_chp_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                                     in range(options["nb_bes"])},
                         "E_el_demand_bes": {(n): sum(results_ch[k]["power_demand_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                                     in range(options["nb_bes"])},
                         "E_gas_from_grid_bes": {(n): sum(results_ch[k]["gas_from_grid_bes"][n]) / 1000 * par_rh["resolution"][0] for
                                     n in range(options["nb_bes"])},
                                 }

    energy_power_year = {"E_el_from_grid": sum(criteria_typeweeks[k]["E_el_from_grid"] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])),
                     "E_el_to_grid": sum(criteria_typeweeks[k]["E_el_to_grid"] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])),
                     "E_gas_from_grid": sum(criteria_typeweeks[k]["E_gas_from_grid"] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])),
                     "E_el_feed": sum(criteria_typeweeks[k]["E_el_feed"] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])),
                     "E_el_demand": sum(criteria_typeweeks[k]["E_el_demand"] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])),
                     "E_el_pv_gen": sum(criteria_typeweeks[k]["E_el_pv_gen"] * weights_typeweeks[k] for k in
                                      range(options["number_typeWeeks"])),
                     "peak_power_transformer_to_grid": max(criteria_typeweeks[k]["peak_power_transformer_to_grid"] for
                                                           k in range(options["number_typeWeeks"])),
                     "peak_power_transformer_from_grid": max(criteria_typeweeks[k]["peak_power_transformer_from_grid"] for
                                                             k in range(options["number_typeWeeks"])),
                     "E_el_feed_pv_bes": {(n): sum(criteria_typeweeks[k]["E_el_feed_pv_bes"][n] * weights_typeweeks[k] for k in
                                           range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "E_el_feed_chp_bes": {(n): sum(criteria_typeweeks[k]["E_el_feed_chp_bes"][n] * weights_typeweeks[k] for k in
                                      range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "E_el_demand_bes": {(n): sum(criteria_typeweeks[k]["E_el_demand_bes"][n] * weights_typeweeks[k] for k in
                                                range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "E_gas_from_grid_bes": {(n): sum(criteria_typeweeks[k]["E_gas_from_grid_bes"][n] * weights_typeweeks[k] for k in
                                                range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     }

    cost_co2_year = {"CO2_emission_district": energy_power_year["E_gas_from_grid"] * params["eco"]["co2_gas"] +
                                              energy_power_year["E_el_from_grid"] * params["eco"]["co2_el"] +
                                              energy_power_year["E_el_pv_gen"] * params["eco"]["co2_pv"],
                     "cost_district": energy_power_year["E_gas_from_grid"] * params["eco"]["gas"] +
                                      energy_power_year["E_el_from_grid"] * params["eco"]["pr",   "el"],
                     "cost_BES": {(n): energy_power_year["E_gas_from_grid_bes"][n] * params["eco"]["gas"] +
                                      energy_power_year["E_el_demand_bes"][n] * params["eco"]["pr",   "el"] for n in range(options["nb_bes"])},
                     "revenue_BES": {(n): energy_power_year["E_el_feed_pv_bes"][n] * params["eco"]["sell_pv"] +
                                          energy_power_year["E_el_feed_chp_bes"][n] * params["eco"]["sell_chp"] for n in range(options["nb_bes"])}
                     }

    cost_diff_BES_district = sum(cost_co2_year["cost_BES"][n] for n in range(options["nb_bes"])) - cost_co2_year["cost_district"]





    return results_ch, criteria_typeweeks, cost_co2_year, energy_power_year, cost_diff_BES_district
'''


''''''
if __name__ == '__main__':

    mode = "80% SFH / 20% MFH: " # adjust for plot titles, "80% SFH / 20% MFH: " -or- "100% TH: "

    # add paths to pickle files to be loaded here:
    paths_in = ["C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p", #0: 1969-1978, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p", #1: 1969-1978, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p", #2: 1969-1978, 50% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p", #3: 1984-1994, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p", #4 1994-1994, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p", #5 1994-1994, 50% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p", #6 2002-2009, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p", #7 2002-2009, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p"] #8 2002-2009, 50% BZ
    # read data
    data = []
    for k in range(paths_in.__len__()):
        with open(paths_in[k], 'rb') as f:
            data.append(pickle.load(f))

    # peak power transformer to grid
    df = pd.DataFrame([["1969-1978", data[0][0]["peak_power_transformer_to_grid"], data[1][0]["peak_power_transformer_to_grid"], data[2][0]["peak_power_transformer_to_grid"]],
                       ["1984-1994", data[3][0]["peak_power_transformer_to_grid"], data[4][0]["peak_power_transformer_to_grid"], data[5][0]["peak_power_transformer_to_grid"]],
                       ["2002-2009", data[6][0]["peak_power_transformer_to_grid"], data[7][0]["peak_power_transformer_to_grid"], data[8][0]["peak_power_transformer_to_grid"]]],
                      columns=["construction period", "0% FC", "25% FC", "50% FC"])

    print(df)
    df.plot(x="construction period", rot=0, ylabel="P_peak transformer to grid [kW]", kind="bar", grid=True, stacked=False, title=(mode + "peak power of transformer (to grid)"), color=['firebrick','lightgrey','navy'])
    plt.show()

    # peak power transformer from grid
    df = pd.DataFrame([["1969-1978", data[0][0]["peak_power_transformer_from_grid"], data[1][0]["peak_power_transformer_from_grid"], data[2][0]["peak_power_transformer_from_grid"]],
                       ["1984-1994", data[3][0]["peak_power_transformer_from_grid"], data[4][0]["peak_power_transformer_from_grid"], data[5][0]["peak_power_transformer_from_grid"]],
                       ["2002-2009", data[6][0]["peak_power_transformer_from_grid"], data[7][0]["peak_power_transformer_from_grid"], data[8][0]["peak_power_transformer_from_grid"]]],
                      columns=["construction period", "0% FC", "25% FC", "50% FC"])

    print(df)
    df.plot(x="construction period", rot=0, ylabel="P_peak transformer from grid [kW]", kind="bar", grid=True, stacked=False, title=(mode + "peak power of transformer (from grid)"), color=['firebrick','lightgrey','navy'])
    plt.show()

