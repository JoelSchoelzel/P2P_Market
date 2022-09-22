

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle


def compute_out(options, options_DG, par_rh, central_opti_results, weights_typeweeks, params):

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

    cost_co2_year.update({"cost_diff_BES_district": sum(cost_co2_year["cost_BES"][n] for n in range(options["nb_bes"])) - cost_co2_year["cost_district"]})

    # cost_diff_BES_district = sum(cost_co2_year["cost_BES"][n] for n in range(options["nb_bes"])) - cost_co2_year["cost_district"]

    criteria = [energy_power_year, cost_co2_year]
    with open(options["path_results"] + "/criteria_" + options_DG["scenario_name"]+ "_T" + str(options["T_heating_limit_BZ"]) + ".p", 'wb') as fp:
        pickle.dump(criteria, fp)

    # create dataframe
    #df = {'P_peak_trafo_from_grid': energy_power_year["peak_power_transformer_from_grid"], 'P_peak_trafo_to_grid': energy_power_year["peak_power_transformer_to_grid"],}
    #criteria = pd.DataFrame(data=df, index = [0])

    # save dataframe to csv file
    #criteria.to_csv(options["path_results"] + "/criteria_" + options_DG["scenario_name"]+ "_T" + str(options["T_heating_limit_BZ"]) + ".csv", index=False)



    return results_ch, criteria_typeweeks, cost_co2_year, energy_power_year



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