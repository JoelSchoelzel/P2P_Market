

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle


def compute_out(options, options_DG, par_rh, central_opti_results, weights_typeweeks, params, building_params):

    results_ch = {} # transfer the results of all control horizons into time series
    # calculate criteria for typeweeks (criteria_typeweeks) and the whole year (criteria_year)
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
                results_ch[k]["power_feed"].append(central_opti_results[k][i][22][t] + central_opti_results[k][i][25][t])
                results_ch[k]["power_demand"].append(central_opti_results[k][i][23][t])
                results_ch[k]["power_pv_gen"].append(sum(central_opti_results[k][i][8][n]["pv"][t] for n in range(options["nb_bes"])))

                for n in range(options["nb_bes"]):
                    results_ch[k]["power_feed_pv_bes"][n].append(central_opti_results[k][i][8][n]["pv"][t])
                    results_ch[k]["power_feed_chp_bes"][n].append(central_opti_results[k][i][8][n]["chp"][t] + central_opti_results[k][i][8][n]["bz"][t])
                    results_ch[k]["power_demand_bes"][n].append(central_opti_results[k][i][4][n][t])
                    results_ch[k]["gas_from_grid_bes"][n].append(
                        central_opti_results[k][i][24][n]["boiler"][t] + central_opti_results[k][i][24][n]["chp"][t] +
                        central_opti_results[k][i][24][n]["bz"][t])

        # distr: district, bes: building energy system
        criteria_typeweeks[k] = {"E_el_from_grid_distr": sum(results_ch[k]["power_from_grid"])/1000 * par_rh["resolution"][0], # kWh
                         "E_el_to_grid_distr": sum(results_ch[k]["power_to_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_gas_from_grid_distr": sum(results_ch[k]["gas_from_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_el_feed_distr": sum(results_ch[k]["power_feed"]) / 1000 * par_rh["resolution"][0],
                         "E_el_demand_distr": sum(results_ch[k]["power_demand"]) / 1000 * par_rh["resolution"][0],
                         "E_el_pv_gen_distr": sum(results_ch[k]["power_pv_gen"]) / 1000 * par_rh["resolution"][0],
                         "peak_power_transformer_to_grid": max(results_ch[k]["power_to_grid"])/1000, # kW
                         "peak_power_transformer_from_grid": max(results_ch[k]["power_from_grid"])/1000,
                         "E_el_feed_pv_bes": {(n): sum(results_ch[k]["power_feed_pv_bes"][n])/1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_el_feed_chp_bes": {(n): sum(results_ch[k]["power_feed_chp_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_el_demand_bes": {(n): sum(results_ch[k]["power_demand_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_gas_from_grid_bes": {(n): sum(results_ch[k]["gas_from_grid_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "T_e_mean": building_params["T_e_mean"][k]
                                 }

        criteria_typeweeks[k].update({"CO2_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["co2_el"]})
        criteria_typeweeks[k].update({"CO2_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["co2_gas"]})
        criteria_typeweeks[k].update({"CO2_pv_gen_distr": criteria_typeweeks[k]["E_el_pv_gen_distr"] * params["eco"]["co2_pv"]})
        criteria_typeweeks[k].update({"cost_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["gas"]})
        criteria_typeweeks[k].update({"cost_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["pr",   "el"]})
        criteria_typeweeks[k].update({"cost_gas_from_grid_bes": {(n): criteria_typeweeks[k]["E_gas_from_grid_bes"][n] * params["eco"]["gas"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"cost_el_demand_bes": {(n): criteria_typeweeks[k]["E_el_demand_bes"][n] * params["eco"]["pr",   "el"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"revenue_el_feed_pv_bes": {(n): criteria_typeweeks[k]["E_el_feed_pv_bes"][n] * params["eco"]["sell_pv"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"revenue_el_feed_chp_bes": {(n): criteria_typeweeks[k]["E_el_feed_chp_bes"][n] * params["eco"]["sell_chp"] for n in range(options["nb_bes"])}})


    criteria_year = {"E_el_from_grid_distr": sum(criteria_typeweeks[k]["E_el_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_to_grid_distr": sum(criteria_typeweeks[k]["E_el_to_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_gas_from_grid_distr": sum(criteria_typeweeks[k]["E_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_feed_distr": sum(criteria_typeweeks[k]["E_el_feed_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_demand_distr": sum(criteria_typeweeks[k]["E_el_demand_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_pv_gen_distr": sum(criteria_typeweeks[k]["E_el_pv_gen_distr"] * weights_typeweeks[k] for k in
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
                     "CO2_el_from_grid_distr": sum(criteria_typeweeks[k]["CO2_el_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "CO2_gas_from_grid_distr": sum(criteria_typeweeks[k]["CO2_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "CO2_pv_gen_distr": sum(criteria_typeweeks[k]["CO2_pv_gen_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_gas_from_grid_distr": sum(criteria_typeweeks[k]["cost_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_el_from_grid_distr": sum(criteria_typeweeks[k]["cost_el_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_gas_from_grid_bes": {(n): sum(criteria_typeweeks[k]["cost_gas_from_grid_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "cost_el_demand_bes": {(n): sum(criteria_typeweeks[k]["cost_el_demand_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "revenue_el_feed_pv_bes": {(n): sum(criteria_typeweeks[k]["revenue_el_feed_pv_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "revenue_el_feed_chp_bes": {(n): sum(criteria_typeweeks[k]["revenue_el_feed_chp_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                          }

    criteria_year.update({"cost_diff_el_bes_distr": sum(criteria_year["cost_el_demand_bes"][n] for n in range(options["nb_bes"])) - criteria_year["cost_el_from_grid_distr"]})


    criteria = [criteria_typeweeks, criteria_year]
    with open(options["path_results"] + "/criteria_central_" + options_DG["scenario_name"] + ".p", 'wb') as fp:
        pickle.dump(criteria, fp)

    # create dataframe
    #df = {'P_peak_trafo_from_grid': energy_power_year["peak_power_transformer_from_grid"], 'P_peak_trafo_to_grid': energy_power_year["peak_power_transformer_to_grid"],}
    #criteria = pd.DataFrame(data=df, index = [0])

    # save dataframe to csv file
    #criteria.to_csv(options["path_results"] + "/criteria_" + options_DG["scenario_name"]+ "_T" + str(options["T_heating_limit_BZ"]) + ".csv", index=False)


    return criteria_typeweeks, criteria_year

def compute_out_decentral(options, options_DG, par_rh, decentral_opti_results, weights_typeweeks, params, building_params):

    results_ch = {} # transfer the results of all control horizons into time series
    # calculate criteria for typeweeks (criteria_typeweeks) and the whole year (criteria_year)
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
                results_ch[k]["power_from_grid"].append(sum(decentral_opti_results[k][i][4][n][t] for n in range(options["nb_bes"]))) #sum of p_imp over all buildings
                results_ch[k]["power_to_grid"].append(sum(sum(decentral_opti_results[k][i][8][n][dev][t] for dev in ("chp","pv")) for n in range(options["nb_bes"]))) #sum of p_sell over all builings and devs
                results_ch[k]["gas_from_grid"].append(sum(decentral_opti_results[k][i][17][n][t] for n in range(options["nb_bes"]))) #sum of gas_sum over all buildings
                results_ch[k]["power_feed"].append(sum(sum(decentral_opti_results[k][i][8][n][dev][t] for dev in ("chp","pv")) for n in range(options["nb_bes"]))) #sum of p_sell over all buildings and devs
                results_ch[k]["power_demand"].append(sum(decentral_opti_results[k][i][4][n][t] for n in range(options["nb_bes"]))) #sum of p_imp over all buildings
                results_ch[k]["power_pv_gen"].append(sum(decentral_opti_results[k][i][8][n]["pv"][t] for n in range(options["nb_bes"])))

                for n in range(options["nb_bes"]):
                    results_ch[k]["power_feed_pv_bes"][n].append(decentral_opti_results[k][i][8][n]["pv"][t])
                    results_ch[k]["power_feed_chp_bes"][n].append(decentral_opti_results[k][i][8][n]["chp"][t]) #+ decentral_opti_results[k][i][8][n]["bz"][t])
                    results_ch[k]["power_demand_bes"][n].append(decentral_opti_results[k][i][4][n][t])
                    results_ch[k]["gas_from_grid_bes"][n].append(decentral_opti_results[k][i][17][n][t])

        # distr: district, bes: building energy system
        criteria_typeweeks[k] = {"E_el_from_grid_distr": sum(results_ch[k]["power_from_grid"])/1000 * par_rh["resolution"][0], # kWh
                         "E_el_to_grid_distr": sum(results_ch[k]["power_to_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_gas_from_grid_distr": sum(results_ch[k]["gas_from_grid"]) / 1000 * par_rh["resolution"][0],
                         "E_el_feed_distr": sum(results_ch[k]["power_feed"]) / 1000 * par_rh["resolution"][0],
                         "E_el_demand_distr": sum(results_ch[k]["power_demand"]) / 1000 * par_rh["resolution"][0],
                         "E_el_pv_gen_distr": sum(results_ch[k]["power_pv_gen"]) / 1000 * par_rh["resolution"][0],
                         "peak_power_transformer_to_grid": max(results_ch[k]["power_to_grid"])/1000, # kW
                         "peak_power_transformer_from_grid": max(results_ch[k]["power_from_grid"])/1000,
                         "E_el_feed_pv_bes": {(n): sum(results_ch[k]["power_feed_pv_bes"][n])/1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_el_feed_chp_bes": {(n): sum(results_ch[k]["power_feed_chp_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_el_demand_bes": {(n): sum(results_ch[k]["power_demand_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "E_gas_from_grid_bes": {(n): sum(results_ch[k]["gas_from_grid_bes"][n]) / 1000 * par_rh["resolution"][0] for n
                            in range(options["nb_bes"])},
                         "T_e_mean": building_params["T_e_mean"][k]
                                 }

        criteria_typeweeks[k].update({"CO2_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["co2_el"]})
        criteria_typeweeks[k].update({"CO2_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["co2_gas"]})
        criteria_typeweeks[k].update({"CO2_pv_gen_distr": criteria_typeweeks[k]["E_el_pv_gen_distr"] * params["eco"]["co2_pv"]})
        criteria_typeweeks[k].update({"cost_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["gas"]})
        criteria_typeweeks[k].update({"cost_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["pr",   "el"]})
        criteria_typeweeks[k].update({"cost_gas_from_grid_bes": {(n): criteria_typeweeks[k]["E_gas_from_grid_bes"][n] * params["eco"]["gas"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"cost_el_demand_bes": {(n): criteria_typeweeks[k]["E_el_demand_bes"][n] * params["eco"]["pr",   "el"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"revenue_el_feed_pv_bes": {(n): criteria_typeweeks[k]["E_el_feed_pv_bes"][n] * params["eco"]["sell_pv"] for n in range(options["nb_bes"])}})
        criteria_typeweeks[k].update({"revenue_el_feed_chp_bes": {(n): criteria_typeweeks[k]["E_el_feed_chp_bes"][n] * params["eco"]["sell_chp"] for n in range(options["nb_bes"])}})


    criteria_year = {"E_el_from_grid_distr": sum(criteria_typeweeks[k]["E_el_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_to_grid_distr": sum(criteria_typeweeks[k]["E_el_to_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_gas_from_grid_distr": sum(criteria_typeweeks[k]["E_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_feed_distr": sum(criteria_typeweeks[k]["E_el_feed_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_demand_distr": sum(criteria_typeweeks[k]["E_el_demand_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "E_el_pv_gen_distr": sum(criteria_typeweeks[k]["E_el_pv_gen_distr"] * weights_typeweeks[k] for k in
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
                     "CO2_el_from_grid_distr": sum(criteria_typeweeks[k]["CO2_el_from_grid_distr"] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])),
                     "CO2_gas_from_grid_distr": sum(criteria_typeweeks[k]["CO2_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "CO2_pv_gen_distr": sum(criteria_typeweeks[k]["CO2_pv_gen_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_gas_from_grid_distr": sum(criteria_typeweeks[k]["cost_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_el_from_grid_distr": sum(criteria_typeweeks[k]["cost_el_from_grid_distr"] * weights_typeweeks[k] for k in
                         range(options["number_typeWeeks"])),
                     "cost_gas_from_grid_bes": {(n): sum(criteria_typeweeks[k]["cost_gas_from_grid_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "cost_el_demand_bes": {(n): sum(criteria_typeweeks[k]["cost_el_demand_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "revenue_el_feed_pv_bes": {(n): sum(criteria_typeweeks[k]["revenue_el_feed_pv_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                     "revenue_el_feed_chp_bes": {(n): sum(criteria_typeweeks[k]["revenue_el_feed_chp_bes"][n] * weights_typeweeks[k] for k in
                        range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
                          }

    criteria_year.update({"cost_diff_el_bes_distr": sum(criteria_year["cost_el_demand_bes"][n] for n in range(options["nb_bes"])) - criteria_year["cost_el_from_grid_distr"]})


    criteria = [criteria_typeweeks, criteria_year]
    with open(options["path_results"] + "/criteria_decentral_" + options_DG["scenario_name"] + ".p", 'wb') as fp:
        pickle.dump(criteria, fp)

def compute_out_P2P(options, options_DG, par_rh, decentral_opti_results, weights_typeweeks, params,
                          building_params, trade_res, mar_dict):

    results_ch = {}  # transfer the results of all control horizons into time series
    # calculate criteria for typeweeks (criteria_typeweeks) and the whole year (criteria_year)
    criteria_typeweeks = {}

    for k in range(options["number_typeWeeks"]):
        results_ch[k] = {"power_from_grid": [],
                         "power_to_grid": [],
                         "power_traded": [],
                         "cost_el" : [],
                         "revenue_el": [],
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
                results_ch[k]["power_from_grid"].append(sum(trade_res[k][i]["el_from_grid"][n] for n in range(
                    options["nb_bes"])))  # sum of el bought from grid
                results_ch[k]["power_to_grid"].append(sum(trade_res[k][i]["el_to_grid"][n] for n in range(
                    options["nb_bes"])))  # sum of el sold to grid
                results_ch[k]["gas_from_grid"].append(sum(decentral_opti_results[k][i][17][n][t] for n in range(
                    options["nb_bes"])))  # sum of gas_sum over all buildings
                results_ch[k]["power_feed"].append(sum(
                    sum(decentral_opti_results[k][i][8][n][dev][t] for dev in ("chp", "pv")) for n in
                    range(options["nb_bes"])))  # sum of p_sell over all buildings and devs
                results_ch[k]["power_demand"].append(sum(decentral_opti_results[k][i][4][n][t] for n in range(
                    options["nb_bes"])))  # sum of p_imp over all buildings
                results_ch[k]["power_pv_gen"].append(
                    sum(decentral_opti_results[k][i][8][n]["pv"][t] for n in range(options["nb_bes"])))
                results_ch[k]["power_traded"].append(sum(trade_res[k][i]["el_to_distr"][n] for n in range(
                    options["nb_bes"])))
                results_ch[k]["cost_el"].append(sum(trade_res[k][i]["cost"][n] for n in range(
                    options["nb_bes"])))
                results_ch[k]["revenue_el"].append(sum(trade_res[k][i]["revenue"][n] for n in range(
                    options["nb_bes"])))

                for n in range(options["nb_bes"]):
                    results_ch[k]["power_feed_pv_bes"][n].append(decentral_opti_results[k][i][8][n]["pv"][t])
                    results_ch[k]["power_feed_chp_bes"][n].append(decentral_opti_results[k][i][8][n]["chp"][
                                                                      t])  # + decentral_opti_results[k][i][8][n]["bz"][t])
                    results_ch[k]["power_demand_bes"][n].append(decentral_opti_results[k][i][4][n][t])
                    results_ch[k]["gas_from_grid_bes"][n].append(decentral_opti_results[k][i][17][n][t])

        # distr: district, bes: building energy system
        criteria_typeweeks[k] = {
            "E_el_from_grid_distr": sum(results_ch[k]["power_from_grid"]) / 1000 * par_rh["resolution"][0],  # kWh
            "E_el_to_grid_distr": sum(results_ch[k]["power_to_grid"]) / 1000 * par_rh["resolution"][0],
            "E_el_traded": sum(results_ch[k]["power_traded"]) / 1000 * par_rh["resolution"][0],
            "cost_el": sum(results_ch[k]["cost_el"]) / 1000 * par_rh["resolution"][0],
            "revenue_el": sum(results_ch[k]["revenue_el"]) / 1000 * par_rh["resolution"][0],
            "E_gas_from_grid_distr": sum(results_ch[k]["gas_from_grid"]) / 1000 * par_rh["resolution"][0],
            "E_el_feed_distr": sum(results_ch[k]["power_feed"]) / 1000 * par_rh["resolution"][0],
            "E_el_demand_distr": sum(results_ch[k]["power_demand"]) / 1000 * par_rh["resolution"][0],
            "E_el_pv_gen_distr": sum(results_ch[k]["power_pv_gen"]) / 1000 * par_rh["resolution"][0],
            "peak_power_transformer_to_grid": max(results_ch[k]["power_to_grid"]) / 1000,  # kW
            "peak_power_transformer_from_grid": max(results_ch[k]["power_from_grid"]) / 1000,
            "E_el_feed_pv_bes": {(n): sum(results_ch[k]["power_feed_pv_bes"][n]) / 1000 * par_rh["resolution"][0]
                                 for n
                                 in range(options["nb_bes"])},
            "E_el_feed_chp_bes": {(n): sum(results_ch[k]["power_feed_chp_bes"][n]) / 1000 * par_rh["resolution"][0]
                                  for n
                                  in range(options["nb_bes"])},
            "E_el_demand_bes": {(n): sum(results_ch[k]["power_demand_bes"][n]) / 1000 * par_rh["resolution"][0] for
                                n
                                in range(options["nb_bes"])},
            "E_gas_from_grid_bes": {(n): sum(results_ch[k]["gas_from_grid_bes"][n]) / 1000 * par_rh["resolution"][0]
                                    for n
                                    in range(options["nb_bes"])},
            "T_e_mean": building_params["T_e_mean"][k],
            }

        criteria_typeweeks[k].update(
            {"CO2_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["co2_el"]})
        criteria_typeweeks[k].update(
            {"CO2_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["co2_gas"]})
        criteria_typeweeks[k].update(
            {"CO2_pv_gen_distr": criteria_typeweeks[k]["E_el_pv_gen_distr"] * params["eco"]["co2_pv"]})
        criteria_typeweeks[k].update(
            {"cost_gas_from_grid_distr": criteria_typeweeks[k]["E_gas_from_grid_distr"] * params["eco"]["gas"]})
        #criteria_typeweeks[k].update(
        #    {"cost_el_from_grid_distr": criteria_typeweeks[k]["E_el_from_grid_distr"] * params["eco"]["pr", "el"]})
        criteria_typeweeks[k].update({"cost_gas_from_grid_bes": {
            (n): criteria_typeweeks[k]["E_gas_from_grid_bes"][n] * params["eco"]["gas"] for n in
            range(options["nb_bes"])}})
        #criteria_typeweeks[k].update({"cost_el_demand_bes": {
        #    (n): criteria_typeweeks[k]["E_el_demand_bes"][n] * params["eco"]["pr", "el"] for n in
        #    range(options["nb_bes"])}})
        #criteria_typeweeks[k].update({"revenue_el_feed_pv_bes": {
        #    (n): criteria_typeweeks[k]["E_el_feed_pv_bes"][n] * params["eco"]["sell_pv"] for n in
        #    range(options["nb_bes"])}})
        #criteria_typeweeks[k].update({"revenue_el_feed_chp_bes": {
        #    (n): criteria_typeweeks[k]["E_el_feed_chp_bes"][n] * params["eco"]["sell_chp"] for n in
        #    range(options["nb_bes"])}})

    criteria_year = {
        "E_el_from_grid_distr": sum(criteria_typeweeks[k]["E_el_from_grid_distr"] * weights_typeweeks[k] for k in
                                    range(options["number_typeWeeks"])),
        "E_el_to_grid_distr": sum(criteria_typeweeks[k]["E_el_to_grid_distr"] * weights_typeweeks[k] for k in
                                  range(options["number_typeWeeks"])),
        "E_el_traded": sum(criteria_typeweeks[k]["E_el_traded"] * weights_typeweeks[k] for k in
                                    range(options["number_typeWeeks"])),
        "cost_el": sum(criteria_typeweeks[k]["cost_el"] * weights_typeweeks[k] for k in
                           range(options["number_typeWeeks"])),
        "revenue_el": sum(criteria_typeweeks[k]["revenue_el"] * weights_typeweeks[k] for k in
                       range(options["number_typeWeeks"])),
        "E_gas_from_grid_distr": sum(criteria_typeweeks[k]["E_gas_from_grid_distr"] * weights_typeweeks[k] for k in
                                     range(options["number_typeWeeks"])),
        "E_el_feed_distr": sum(criteria_typeweeks[k]["E_el_feed_distr"] * weights_typeweeks[k] for k in
                               range(options["number_typeWeeks"])),
        "E_el_demand_distr": sum(criteria_typeweeks[k]["E_el_demand_distr"] * weights_typeweeks[k] for k in
                                 range(options["number_typeWeeks"])),
        "E_el_pv_gen_distr": sum(criteria_typeweeks[k]["E_el_pv_gen_distr"] * weights_typeweeks[k] for k in
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
        "E_gas_from_grid_bes": {
            (n): sum(criteria_typeweeks[k]["E_gas_from_grid_bes"][n] * weights_typeweeks[k] for k in
                     range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
        "CO2_el_from_grid_distr": sum(
            criteria_typeweeks[k]["CO2_el_from_grid_distr"] * weights_typeweeks[k] for k in
            range(options["number_typeWeeks"])),
        "CO2_gas_from_grid_distr": sum(
            criteria_typeweeks[k]["CO2_gas_from_grid_distr"] * weights_typeweeks[k] for k in
            range(options["number_typeWeeks"])),
        "CO2_pv_gen_distr": sum(criteria_typeweeks[k]["CO2_pv_gen_distr"] * weights_typeweeks[k] for k in
                                range(options["number_typeWeeks"])),
        "cost_gas_from_grid_distr": sum(
            criteria_typeweeks[k]["cost_gas_from_grid_distr"] * weights_typeweeks[k] for k in
            range(options["number_typeWeeks"])),
        #"cost_el_from_grid_distr": sum(
        #    criteria_typeweeks[k]["cost_el_from_grid_distr"] * weights_typeweeks[k] for k in
        #    range(options["number_typeWeeks"])),
        "cost_gas_from_grid_bes": {
            (n): sum(criteria_typeweeks[k]["cost_gas_from_grid_bes"][n] * weights_typeweeks[k] for k in
                     range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
        #"cost_el_demand_bes": {
        #    (n): sum(criteria_typeweeks[k]["cost_el_demand_bes"][n] * weights_typeweeks[k] for k in
        #             range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
        #"revenue_el_feed_pv_bes": {
        #    (n): sum(criteria_typeweeks[k]["revenue_el_feed_pv_bes"][n] * weights_typeweeks[k] for k in
        #             range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
        #"revenue_el_feed_chp_bes": {
        #    (n): sum(criteria_typeweeks[k]["revenue_el_feed_chp_bes"][n] * weights_typeweeks[k] for k in
        #             range(options["number_typeWeeks"])) for n in range(options["nb_bes"])},
        }

    #criteria_year.update({"cost_diff_el_bes_distr": sum(
    #    criteria_year["cost_el_demand_bes"][n] for n in range(options["nb_bes"])) - criteria_year[
    #                                                        "cost_el_from_grid_distr"]})

    criteria = [criteria_typeweeks, criteria_year]
    with open(options["path_results"] + "/criteria_P2P_" + options_DG["scenario_name"] + ".p", 'wb') as fp:
        pickle.dump(criteria, fp)

    # create dataframe
    #df = {'P_peak_trafo_from_grid': energy_power_year["peak_power_transformer_from_grid"], 'P_peak_trafo_to_grid': energy_power_year["peak_power_transformer_to_grid"],}
    #criteria = pd.DataFrame(data=df, index = [0])

    # save dataframe to csv file
    #criteria.to_csv(options["path_results"] + "/criteria_" + options_DG["scenario_name"]+ "_T" + str(options["T_heating_limit_BZ"]) + ".csv", index=False)


    return criteria_typeweeks, criteria_year

''''''
#gas_district = np.zeros(len(par_rh["time_steps"]))
#residual_district = np.zeros(len(par_rh["time_steps"]))

    #for n_opt in range(par_rh["n_opt"]):
    #    for t in par_rh["time_steps"][n_opt][0:par_rh["n_hours"] - par_rh["n_hours_ov"]]:
    #        for n in range(options["nb_bes"]):
    #            residual_district[n_opt] = residual_district[n_opt] + opti_bes[n_opt][n][4][t] \
    #                                   - opti_bes[n_opt][n][8]["pv"][t] \
    #                                   - opti_bes[n_opt][n][8]["chp"][t]

    #fig, ax1 = plt.subplots(1, figsize=(11, 6))
    #ax1.plot(residual_district[:5*24], color='darkblue', linewidth=1.0, label="Residuallast")
    #ax1.set(ylabel='Power in kW')
    #ax1.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.3)
    #plt.savefig("residual_power_total_scn_comp", dpi=300, bbox_inches="tight")
    #plt.show()