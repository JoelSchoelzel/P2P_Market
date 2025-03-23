import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from matplotlib import rc

from python.block_bids import mean_all


def calc_results_p2p(par_rh, block_length, nego_results, opti_res, opti_res_check, grid_transaction, params, options,
                     opti_res_css: dict = None, mar_agent_bes: dict = None, mar_agent_css: object = None):

    last_n_opt = par_rh["n_opt"]
    time_steps = []
    for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + block_length):
        time_steps.append(i)
    nb_agents = len(opti_res[0])
    if options["central_supply_system"]:
        nb_agents = len(opti_res[0]) + 1

    # --------------------- DGOC --------------------- #

    total_p_purchase = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    total_feed_in = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_p_purchase[t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000 # kW
                total_feed_in[t - par_rh["hour_start"][0]] += (opti_res[n_opt][n][8]["chp"][t] +
                                                               opti_res[n_opt][n][8]["pv"][t]) / 1000  # kW
        if options["central_supply_system"]:
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_p_purchase[t - par_rh["hour_start"][0]] += opti_res_css[n_opt]["res_p_imp"][t] / 1000  # kW
                total_feed_in[t - par_rh["hour_start"][0]] += (opti_res_css[n_opt]["res_p_sell"]["s_pv"][t] +
                                                               opti_res_css[n_opt]["res_p_sell"]["s_wind"][t] +
                                                               opti_res_css[n_opt]["res_p_dch"]["s_bat"][t]) / 1000  # kW

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
                bat_losses.append(0.03 * (opti_res[n_opt][n][3]["bat"][t]  # res_soc
                                          + opti_res[n_opt][n][5]["bat"][t]  # res_p_ch
                                          + opti_res[n_opt][n][6]["bat"][t]))  # res_p_dch
                tes_losses.append(0.03 * opti_res[n_opt][n][3]["tes"][t])
        if options["central_supply_system"]:
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                bat_losses.append(0.03 * (opti_res_css[n_opt]["res_soc"]["s_bat"][t]
                                          + opti_res_css[n_opt]["res_p_ch"]["s_bat"][t]
                                          + opti_res_css[n_opt]["res_p_dch"]["s_bat"][t]))
    bat_losses = sum(bat_losses) / 1000  # kWh
    tes_losses = sum(tes_losses) / 1000  # kWh

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
    traded_power = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    additional_revenue = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    saved_costs = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_revenue = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_costs = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    gain = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    av_MCP = np.zeros(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0])
    counter = 0

    for opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                # valid_time_steps = {k: v for k, v in nego_results[opt][round_nb][match]["quantity"].items() if isinstance(k, int)}
                for t in range(par_rh["hour_start"][opt], par_rh["hour_start"][opt] + block_length):
                    try:
                        if isinstance(nego_results[opt][round_nb][match]["trading_quantity"][t], float):  # valid_time_steps
                            traded_power[nego_results[opt][round_nb][match]["buyer_id"], t - par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["trading_quantity"][t]/1000  # kWh
                            traded_power[nego_results[opt][round_nb][match]["seller_id"], t - par_rh["hour_start"][0]] +=  \
                                nego_results[opt][round_nb][match]["trading_quantity"][t] / 1000  # kWh
                            additional_revenue[nego_results[opt][round_nb][match]["seller_id"], t - par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["additional_revenue"][t]  # €/kWh
                            saved_costs[nego_results[opt][round_nb][match]["buyer_id"], t - par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["saved_costs"][t]  # €/kWh
                            trading_revenue[nego_results[opt][round_nb][match]["seller_id"], t - par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["trading_revenue"][t]  # €/kWh
                            trading_costs[nego_results[opt][round_nb][match]["buyer_id"], t - par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["trading_cost"][t]  # €/kWh
                            gain[nego_results[opt][round_nb][match]["buyer_id"], t - par_rh["hour_start"][0]] = \
                                saved_costs[nego_results[opt][round_nb][match]["buyer_id"], t - par_rh["hour_start"][0]]
                            gain[nego_results[opt][round_nb][match]["seller_id"], t - par_rh["hour_start"][0]] = \
                                additional_revenue[nego_results[opt][round_nb][match]["seller_id"], t - par_rh["hour_start"][0]]
                    except KeyError:
                        counter =+ 1
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                for t in range(par_rh["hour_start"][opt], par_rh["hour_start"][opt] + block_length):
                    try:
                        if isinstance(nego_results[opt][round_nb][match]["trading_quantity"][t], float):
                            # av_MCP[t - par_rh["hour_start"][0]] = (
                            #             sum(nego_results[opt][round_nb][match]["trading_price"][t]
                            #                 for round_nb in nego_results[opt]
                            #                 for match in nego_results[opt][round_nb])
                            #             / sum(1 for round_nb in nego_results[opt]
                            #                   for match in nego_results[opt][
                            #                       round_nb]))  # len(nego_results[opt][round_nb][match]["trading_price"]))
                            av_MCP[t - par_rh["hour_start"][0]] = (
                                    sum(nego_results[opt][round_nb][match]["trading_price"][t]
                                        for round_nb in nego_results[opt]
                                        for match in nego_results[opt][round_nb]
                                        if nego_results[opt][round_nb][match]["trading_price"][t] != 0)
                                    / sum(1 for round_nb in nego_results[opt]
                                          for match in nego_results[opt][round_nb]
                                          if nego_results[opt][round_nb][match]["trading_price"][t] != 0)
                            )

                    except ZeroDivisionError:
                        pass

    print("counter_"+str(counter))

    traded_power_per_building = np.zeros(nb_agents)
    trading_costs_per_building = np.zeros(nb_agents)
    saved_costs_per_building = np.zeros(nb_agents)
    trading_revenue_per_building = np.zeros(nb_agents)
    additional_revenue_per_building = np.zeros(nb_agents)
    gain_per_building = np.zeros(nb_agents)
    for n in range(nb_agents):
        traded_power_per_building[n] = np.sum(traded_power[n, :])
        trading_costs_per_building[n] = np.sum(trading_costs[n, :])
        saved_costs_per_building[n] = np.sum(saved_costs[n, :])
        trading_revenue_per_building[n] = np.sum(trading_revenue[n, :])
        additional_revenue_per_building[n] = np.sum(additional_revenue[n, :])
        gain_per_building[n] = np.sum(gain[n, :])

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

    total_cost = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    total_cost = total_cost + trading_costs - trading_revenue
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["costs_power_from_grid"][n][t] \
                                                           - grid_transaction[n_opt]["revenue_power_to_grid"][n][t] \
                                                           + opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"]
        if options["central_supply_system"]:
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost[nb_agents - 1, t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["costs_power_from_grid"][nb_agents - 1][t] \
                                                                    - grid_transaction[n_opt]["revenue_power_to_grid"][nb_agents - 1][t]

    total_cost_per_buildung = np.zeros(nb_agents)
    for n in range(nb_agents):
        total_cost_per_buildung[n] = np.sum(total_cost[n,:])

    total_cost_without_LEM = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost_without_LEM[n,t - par_rh["hour_start"][0]] += opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"] \
                                                                         + opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000* params["eco"]["pr", "el"] \
                                                                         - (opti_res[n_opt][n][8]["chp"][t] + opti_res[n_opt][n][8]["pv"][t]) / 1000*params["eco"]["sell_pv"] # kW
        if options["central_supply_system"]:
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost_without_LEM[nb_agents - 1, t - par_rh["hour_start"][0]] += opti_res_css[n_opt]["res_p_imp"][t] / 1000 * params["eco"]["pr", "el"] \
                                                                                     - (opti_res_css[n_opt]["res_p_sell"]["s_pv"][t] + opti_res_css[n_opt]["res_p_sell"]["s_wind"][t]) / 1000 * params["eco"]["sell_pv"]

    total_cost_without_LEM_per_buildung = np.zeros(nb_agents)
    for n in range(nb_agents):
        total_cost_without_LEM_per_buildung[n] = np.sum(total_cost_without_LEM[n,:])

    # ----------- traded supply and demand quantities   ---------------------

    denominator_total_demand = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    denominator_total_supply = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_demand = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_supply = np.zeros((nb_agents, par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

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
        if options["central_supply_system"]:
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                denominator_total_demand[nb_agents - 1, t - par_rh["hour_start"][0]] += opti_res_css[n_opt]["res_p_imp"][t] / 1000
                denominator_total_supply[nb_agents - 1, t - par_rh["hour_start"][0]] += opti_res_css[n_opt]["res_p_sell"]["s_pv"][t] / 1000 \
                                                                                          + opti_res_css[n_opt]["res_p_sell"]["s_wind"][t] / 1000
                if denominator_total_demand[nb_agents - 1, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_demand[nb_agents - 1, t - par_rh["hour_start"][0]] = traded_power[nb_agents - 1, t - par_rh["hour_start"][0]]
                if denominator_total_supply[nb_agents - 1, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_supply[nb_agents - 1, t - par_rh["hour_start"][0]] = traded_power[nb_agents - 1, t - par_rh["hour_start"][0]]

    mSCF_bd = {}
    mDCF_bd = {}
    for n in range(nb_agents):
        if sum(denominator_total_supply[n, :]) != 0:
            mSCF_bd[n] = sum(nominator_total_supply[n, :]) / sum(denominator_total_supply[n, :])
        if sum(denominator_total_demand[n, :]) != 0:
            mDCF_bd[n] = sum(nominator_total_demand[n, :]) / sum(denominator_total_demand[n, :])

    mSCF = sum(sum(nominator_total_supply)) / sum(sum(denominator_total_supply))
    mDCF = sum(sum(nominator_total_demand)) / sum(sum(denominator_total_demand))

    cumulative_q_rewards = {}
    CSS_q_value_change = {}
    if options["central_supply_system"] and options["bid_strategy"] == "q_learning":
        cumulative_q_rewards = {}
        for n in range(nb_agents-1):
            cumulative_q_rewards[n] = mar_agent_bes[n].cum_q_reward
        cumulative_q_rewards[nb_agents-1] = mar_agent_css.cum_q_reward
        cumulative_q_rewards = np.array(list(cumulative_q_rewards.values()))

        CSS_q_value_change = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
        for n_opt in range(par_rh["n_opt"] - int(36 / block_length) - 1):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                CSS_q_value_change[t - par_rh["hour_start"][0]] = mar_agent_css.q_value_change[t]
        # CSS_q_value_change = mar_agent_css.q_value_change
        # CSS_q_value_change = np.array(CSS_q_value_change)


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

        "traded_power_total": traded_power_total,
        "additional_revenue_total": additional_revenue_total,
        "saved_costs_total": saved_costs_total,
        "gain_total": gain_total,
        "trading_costs_total": trading_costs_total,
        "trading_revenue_total": trading_revenue_total,
        "av_prices_buy": av_prices_buy,
        "av_prices_sell": av_prices_sell,
        "av_MCP": av_MCP,

        "total_cost": total_cost,
        "total_cost_per_buildung": total_cost_per_buildung,
        "total_cost_without_LEM_per_buildung": total_cost_without_LEM_per_buildung,

        "traded_supply_bids_per_building": mSCF_bd,
        "traded_demand_bids_per_building": mDCF_bd,
        "traded_supply_bids": mSCF,
        "traded_demand_bids": mDCF,

        "bat_losses": bat_losses,
        "tes_losses": tes_losses,

        "residual_load": residual_load,
        "total_p_purchase": total_p_purchase,
        "total_feed_in": total_feed_in,

        "cumulative_Q_Rewards": cumulative_q_rewards,
        "CSS_q_value_change": CSS_q_value_change
    }
    return results

# def plots():
#
#
#     import pickle
#     import matplotlib.pyplot as plt
#     import seaborn as sns
#     import numpy as np
#
#     xlabel_fontsize = 16
#     ylabel_fontsize = 16
#     xtick_fontsize = 16
#     ytick_fontsize = 16
#     legend_fontsize = 16
#
#
#     results = {}
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_random.p", "rb") as file_res_list:
#         results[str(1)+"_"+str(1)+"_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_quantity.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(1) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_flex.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(1) + "_flex"] = pickle.load(file_res_list)
#
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_random.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(3) + "_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_quantity.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(3) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_flex.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(3) + "_flex"] = pickle.load(file_res_list)
#
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_random.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(5) + "_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_quantity.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(5) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_flex.p", "rb") as file_res_list:
#         results[str(1) + "_" + str(5) + "_flex"] = pickle.load(file_res_list)
#
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len1_random.p", "rb") as file_res_list:
#         results[str(5)+"_"+str(1)+"_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len1_quantity.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(1) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len1_flex.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(1) + "_flex"] = pickle.load(file_res_list)
#
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len3_random.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(3) + "_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len3_quantity.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(3) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len3_flex.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(3) + "_flex"] = pickle.load(file_res_list)
#
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len5_random.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(5) + "_random"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len5_quantity.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(5) + "_quantity"] = pickle.load(file_res_list)
#     with open("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r5_len5_flex.p", "rb") as file_res_list:
#         results[str(5) + "_" + str(5) + "_flex"] = pickle.load(file_res_list)
#
#
#     """
#         dgoc_heat_map[0, x] = np.round(results["DGOC"]*100, 2)
#         peak_purchase_heat_map[0, x] = int(np.round(results["peak_purchase"], 0))
#         peak_feedin_heat_map[0, x] = int(np.round(results["peak_feed_in"], 0))
#         traded_supply_bids_heat_map[0, x] = np.round(results["traded_supply_bids"]*100, 2)
#         traded_demand_bids_heat_map[0, x] = np.round(results["traded_demand_bids"]*100, 2)
#         energy_losses_heat_map [0, x] = np.round((results["bat_losses"]+results["bat_losses"])/1000, 2) # MWh
#         traded_power_heat_map[0, x] = np.round(results["traded_power_total"]/1000, 2)  # MWh
#         x += 1
#     """
#
#
#     #### ------------------- dgoc_heat_map ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/dgoc_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Benutzerdefinierte Achsenwerte
#     x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
#     y_labels = ["1", "10"]  # Beispielwerte für y-Achse
#     # Erstellen der Heatmap
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(dgoc_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
#     plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
#     plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
#     plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#     #### ------------------- traded_supply_bids ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_supply_bids_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Creating the DataFrame
#     data = {
#         ('random', 1): [results["1_1_random"]["traded_supply_bids"]*100, results["1_3_random"]["traded_supply_bids"]*100, results["1_5_random"]["traded_supply_bids"]*100],
#         ('random', 10): [results["5_1_random"]["traded_supply_bids"]*100, results["5_3_random"]["traded_supply_bids"]*100, results["5_5_random"]["traded_supply_bids"]*100],
#         ('quantity', 1): [results["1_1_quantity"]["traded_supply_bids"]*100, results["1_3_quantity"]["traded_supply_bids"]*100, results["1_5_quantity"]["traded_supply_bids"]*100],
#         ('quantity', 10): [results["5_1_quantity"]["traded_supply_bids"]*100, results["5_3_quantity"]["traded_supply_bids"]*100, results["5_5_quantity"]["traded_supply_bids"]*100],
#         ('flexibility', 1): [results["1_1_flex"]["traded_supply_bids"]*100, results["1_3_flex"]["traded_supply_bids"]*100, results["1_5_flex"]["traded_supply_bids"]*100],
#         ('flexibility', 10): [results["5_1_flex"]["traded_supply_bids"]*100, results["5_3_flex"]["traded_supply_bids"]*100, results["5_5_flex"]["traded_supply_bids"]*100],
#     }
#     df = pd.DataFrame(data, index=[1, 3, 5])
#     # Plotting the heatmap
#     plt.figure(figsize=(14, 8))
#     sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
#     plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
#     plt.xticks(fontsize=xtick_fontsize)
#     plt.yticks(fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#
#     #### ------------------- traded_demand_bids ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_demand_bids_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Creating the DataFrame
#     data = {
#         ('random', 1): [results["1_1_random"]["traded_demand_bids"]*100, results["1_3_random"]["traded_demand_bids"]*100, results["1_5_random"]["traded_demand_bids"]*100],
#         ('random', 10): [results["5_1_random"]["traded_demand_bids"]*100, results["5_3_random"]["traded_demand_bids"]*100, results["5_5_random"]["traded_demand_bids"]*100],
#         ('quantity', 1): [results["1_1_quantity"]["traded_demand_bids"]*100, results["1_3_quantity"]["traded_demand_bids"]*100, results["1_5_quantity"]["traded_demand_bids"]*100],
#         ('quantity', 10): [results["5_1_quantity"]["traded_demand_bids"]*100, results["5_3_quantity"]["traded_demand_bids"]*100, results["5_5_quantity"]["traded_demand_bids"]*100],
#         ('flexibility', 1): [results["1_1_flex"]["traded_demand_bids"]*100, results["1_3_flex"]["traded_demand_bids"]*100, results["1_5_flex"]["traded_demand_bids"]*100],
#         ('flexibility', 10): [results["5_1_flex"]["traded_demand_bids"]*100, results["5_3_flex"]["traded_demand_bids"]*100, results["5_5_flex"]["traded_demand_bids"]*100],
#     }
#     df = pd.DataFrame(data, index=[1, 3, 5])
#     # Plotting the heatmap
#     plt.figure(figsize=(14, 8))
#     sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
#     plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
#     plt.xticks(fontsize=xtick_fontsize)
#     plt.yticks(fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#
#     #### ------------------- traded_power ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/traded_power_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Creating the DataFrame
#     data = {
#         ('random', 1): [results["1_1_random"]["traded_power_total"] / 1000,
#                         results["1_3_random"]["traded_power_total"] / 1000,
#                         results["1_5_random"]["traded_power_total"] / 1000],
#         ('random', 10): [results["5_1_random"]["traded_power_total"] / 1000,
#                          results["5_3_random"]["traded_power_total"] / 1000,
#                          results["5_5_random"]["traded_power_total"] / 1000],
#         ('quantity', 1): [results["1_1_quantity"]["traded_power_total"] / 1000,
#                           results["1_3_quantity"]["traded_power_total"] / 1000,
#                           results["1_5_quantity"]["traded_power_total"] / 1000],
#         ('quantity', 10): [results["5_1_quantity"]["traded_power_total"] / 1000,
#                            results["5_3_quantity"]["traded_power_total"] / 1000,
#                            results["5_5_quantity"]["traded_power_total"] / 1000],
#         ('flexibility', 1): [results["1_1_flex"]["traded_power_total"] / 1000,
#                              results["1_3_flex"]["traded_power_total"] / 1000,
#                              results["1_5_flex"]["traded_power_total"] / 1000],
#         ('flexibility', 10): [results["5_1_flex"]["traded_power_total"] / 1000,
#                               results["5_3_flex"]["traded_power_total"] / 1000,
#                               results["5_5_flex"]["traded_power_total"] / 1000],
#     }
#     df = pd.DataFrame(data, index=[1, 3, 5])
#     # Plotting the heatmap
#     plt.figure(figsize=(14, 8))
#     sns.heatmap(df, annot=True, fmt=".1f", cmap=cmap, cbar=False, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Matching criteria and maximal negotiation rounds", fontsize=xlabel_fontsize)
#     plt.ylabel("Length of block bids", fontsize=ylabel_fontsize)
#     plt.xticks(fontsize=xtick_fontsize)
#     plt.yticks(fontsize=ytick_fontsize)
#     # Titel
#     # plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#     #### ------------------- peak_feedin ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/peak_feedin_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Benutzerdefinierte Achsenwerte
#     x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
#     y_labels = ["1", "10"]  # Beispielwerte für y-Achse
#     # Erstellen der Heatmap
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(                        peak_feedin_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
#     plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
#     plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
#     plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#     #### ------------------- peak_purchase ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/peak_purchase_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Benutzerdefinierte Achsenwerte
#     x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
#     y_labels = ["1", "10"]  # Beispielwerte für y-Achse
#     # Erstellen der Heatmap
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(                 peak_purchase_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Length of block bids", fontsize=xlabel_fontsize)
#     plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
#     plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
#     plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#     #### ------------------- losses ------------------- ####
#     # Hauptfarbe
#     main_color = "#00549F"
#     # Erstellen einer benutzerdefinierten Farbpalette mit Schattierungen der Hauptfarbe
#     cmap = sns.light_palette(main_color, as_cmap=True)
#     # Pfad zum Speichern der Datei
#     save_path = "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/energy_losses_heat_map.png"
#     # Auflösung (DPI)
#     dpi = 300
#     # Benutzerdefinierte Achsenwerte
#     x_labels = ["1", "3", "5"]  # Beispielwerte für x-Achse
#     y_labels = ["1", "10"]  # Beispielwerte für y-Achse
#     # Erstellen der Heatmap
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(                  energy_losses_heat_map, annot=True, fmt=".2f", cmap=cmap, cbar=True, linewidths=.5)
#     # Achsenbeschriftungen
#     plt.xlabel("Matching creLength of block bids", fontsize=xlabel_fontsize)
#     plt.ylabel("Max. negotiation rounds", fontsize=ylabel_fontsize)
#     plt.xticks(ticks=np.arange(len(x_labels)) + 0.5, labels=x_labels, fontsize=xtick_fontsize)
#     plt.yticks(ticks=np.arange(len(y_labels)) + 0.5, labels=y_labels, fontsize=ytick_fontsize)
#     # Titel
#     #plt.title("Generic 3x3 Heatmap")
#     # Speichern der Heatmap als PNG
#     plt.savefig(save_path, dpi=dpi)
#     # Anzeige der Heatmap
#     plt.show()
#
#
#     # --------------------- Balkendiagramm für Nutzergruppen --------------------- #
#
#     import pickle
#     import matplotlib.pyplot as plt
#     import numpy as np
#     av_gain_per_group = np.zeros((9, 6))
#     min_gain_per_group = np.zeros((9, 6))
#     max_gain_per_group = np.zeros((9, 6))
#
#     results_block_bid_length_r1 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len1_flex.p",
#                                    "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len1_flex.p",
#                                    "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len3_flex.p",
#                                    "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len3_flex.p",
#                                    "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r1_len5_flex.p",
#                                    "C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_flex.p",]
#     x = 0
#     for i in results_block_bid_length_r1:
#         with open(i, "rb") as file_res_list:
#             results = pickle.load(file_res_list)
#         for group in range(0, 9*5, 5):
#             av_gain_per_group[int(group/5), x] = int(np.mean(results["gain_per_building"][group:group+5]))
#             min_gain_per_group[int(group/5), x] = int(np.min(results["gain_per_building"][group:group+5]))
#             max_gain_per_group[int(group/5), x] = int(np.max(results["gain_per_building"][group:group+5]))
#         x += 1
#
#     num_user_groups = 9
#     num_bars_per_group = 6
#     # Farben und Schraffierungen nach RWTH Aachen
#     colors = ['#00549F', '#00549F', '#8EBAE5', '#8EBAE5', '#AAAAAA', '#AAAAAA']
#     hatch_patterns = ['', '//', '', '//', '', '//']
#     # Erstellen des Balkendiagramms
#     fig, ax = plt.subplots(figsize=(15, 8))
#     bar_width = 0.1
#     bar_positions = np.arange(num_user_groups)
#     for i in range(num_bars_per_group):
#         bars = ax.bar(bar_positions + i * bar_width, av_gain_per_group[:, i], bar_width,
#                       label=f'Bar {i + 1}', color=colors[i], hatch=hatch_patterns[i])
#         # Hinzufügen von Minimal- und Maximalwerten als Kreise
#         for j in range(num_user_groups):
#             ax.plot(bar_positions[j] + i * bar_width, min_gain_per_group[j, i], 'o', color='black')
#             ax.plot(bar_positions[j] + i * bar_width, max_gain_per_group[j, i], 'o', color='red')
#     # Achsenbeschriftungen
#     ax.set_xlabel('User groups', fontsize=xlabel_fontsize)
#     ax.set_ylabel('Gain', fontsize=ylabel_fontsize)
#     ax.set_xticks(bar_positions + (num_bars_per_group - 1) * bar_width / 2)
#     ax.set_xticklabels([f'Group {i + 1}' for i in range(num_user_groups)])
#     ax.set_ylim(0, 5500)
#     # Legende
#     ax.legend()
#     # Titel
#     plt.title('User Groups Gain')
#     # Anzeige des Diagramms
#     plt.show()
#
#     ### -------------------- gain as times series -------------------- ###
#
#     import pickle
#     import matplotlib.pyplot as plt
#     import numpy as np
#     import                    tikzplotlib
#
#     gain_per_group_over_time = np.zeros((9, 8760))
#     gain_per_building = np.zeros(45)
#     total_cost_per_buildung = np.zeros(45)
#     total_cost_without_LEM_per_buildung = np.zeros(45)
#
#     results_block_bid_length_r1 = ["C:/Users/jsc/Python/Results/AppliedEnergy/all_results/r10_len5_flex.p"]
#
#     for i in results_block_bid_length_r1:
#         with open(i, "rb") as file_res_list:
#             results = pickle.load(file_res_list)
#         for group in range(0, 9*5, 5):
#             for t in range(8759):
#                 gain_per_group_over_time[int(group/5), t] = np.sum(results["gain"][group:group+5, t])
#         total_gain_over_time = results["gain_total_over_time"]
#         for nb in range(45):
#             gain_per_building[nb] = results["gain_per_building"][nb]
#             total_cost_per_buildung = results["total_cost_per_buildung"]
#             total_cost_without_LEM_per_buildung = results["total_cost_without_LEM_per_buildung"]
#     gain_per_group_over_time = np.cumsum(gain_per_group_over_time, axis=1)
#
#     num_series = 9
#     hours_per_year = 8760
#     data = gain_per_group_over_time
#     # Konvertiere Stunden in Tage (für die x-Achsen-Beschriftung)
#     x_values = np.linspace(0, 365, hours_per_year)
#     title_fontsize = 20
#     xlabel_fontsize = 16
#     ylabel_fontsize = 16
#     xtick_fontsize = 16
#     ytick_fontsize = 16
#     legend_fontsize = 16
#     # Legendenlabels
#     legend_labels = ["User group 1", "User group 2", "User group 3", "User group 4", "User group 5",
#                      "User group 6", "User group 7", "User group 8", "User group 9"]
#
#     plt.figure(figsize=(15, 8))
#     for i in range(data.shape[0]):
#         plt.plot(x_values, data[i], label=legend_labels[i], linewidth=1.8)
#     # Achsenbeschriftungen
#     plt.xlabel('Day', fontsize=xlabel_fontsize)
#     plt.ylabel('Gain in €', fontsize=ylabel_fontsize)
#     plt.ylim(0, 8000)
#     plt.xlim(0, 365)
#     # Setzt die xticks auf ganze Zahlen für Tage
#     plt.xticks(np.arange(0, 366, step=30), fontsize=xtick_fontsize)
#     plt.yticks(fontsize=ytick_fontsize)
#     # Legende
#     plt.legend(fontsize=legend_fontsize)
#     # Titel
#     #plt.title("title", fontsize=title_fontsize)
#     # Anzeige der Grafik
#     tikzplotlib.save("C:/Users/jsc/Python/Results/AppliedEnergy/all_results/pictures/gain_per_group_over_time_test.tex")  # , axis_height ='5 cm',axis_width='15 cm')
#     plt.show()
#     return




#     ### -------------------- gain as times series -------------------- ###
#
#     import pickle
#     import matplotlib.pyplot as plt
#     import numpy as np
#
#     # Ensure compatibility with tikzplotlib
#     import matplotlib.backends.backend_pgf as backend_pgf
#
#     # Patch backend_pgf if common_texification is missing
#     if not hasattr(backend_pgf, "common_texification"):
#         def common_texification(input_str):
#             # Define a placeholder function that returns the input unchanged
#             return input_str
#
#         backend_pgf.common_texification = common_texification
#
#     import tikzplotlib
#
#     # gain_per_group_over_time = np.zeros((9, 8760))
#     # gain_per_building = np.zeros(45)
#     # total_cost_per_buildung = np.zeros(45)
#     # total_cost_without_LEM_per_buildung = np.zeros(45)
#     #
#     # results_block_bid_length_r1 = ["C:/Users/muham/Documents/GitHub/results/AppliedEnergy/all_results/r10_len5_flex.p"]
#     #
#     # for i in results_block_bid_length_r1:
#     #     with open(i, "rb") as file_res_list:
#     #         results = pickle.load(file_res_list)
#     #     for group in range(0, 9*5, 5):
#     #         for t in range(8759):
#     #             gain_per_group_over_time[int(group/5), t] = np.sum(results["gain"][group:group+5, t])
#     #     total_gain_over_time = results["gain_total_over_time"]
#     #     for nb in range(45):
#     #         gain_per_building[nb] = results["gain_per_building"][nb]
#     #         total_cost_per_buildung = results["total_cost_per_buildung"]
#     #         total_cost_without_LEM_per_buildung = results["total_cost_without_LEM_per_buildung"]
#     # gain_per_group_over_time = np.cumsum(gain_per_group_over_time, axis=1)
#     #
#     # num_series = 9
#     # hours_per_year = 8760
#     # data = gain_per_group_over_time
#     # # Konvertiere Stunden in Tage (für die x-Achsen-Beschriftung)
#     # x_values = np.linspace(0, 365, hours_per_year)
#     # title_fontsize = 20
#     # xlabel_fontsize = 16
#     # ylabel_fontsize = 16
#     # xtick_fontsize = 16
#     # ytick_fontsize = 16
#     # legend_fontsize = 16
#     # # Legendenlabels
#     # legend_labels = ["User group 1", "User group 2", "User group 3", "User group 4", "User group 5",
#     #                  "User group 6", "User group 7", "User group 8", "User group 9"]
#     #
#     # plt.figure(figsize=(15, 8))
#     # for i in range(data.shape[0]):
#     #     plt.plot(x_values, data[i], label=legend_labels[i], linewidth=1.8)
#     # # Achsenbeschriftungen
#     # plt.xlabel('Day', fontsize=xlabel_fontsize)
#     # plt.ylabel('Gain in €', fontsize=ylabel_fontsize)
#     # plt.ylim(0, 8000)
#     # plt.xlim(0, 365)
#     # # Setzt die xticks auf ganze Zahlen für Tage
#     # plt.xticks(np.arange(0, 366, step=30), fontsize=xtick_fontsize)
#     # plt.yticks(fontsize=ytick_fontsize)
#     # # Legende
#     # plt.legend(fontsize=legend_fontsize)
#     # # Titel
#     # #plt.title("title", fontsize=title_fontsize)
#     # # Anzeige der Grafik
#     # tikzplotlib.save("C:/Users/muham/Documents/GitHub/results/AppliedEnergy/all_results/pictures/gain_per_group_over_time_test.tex")  # , axis_height ='5 cm',axis_width='15 cm')
#     # plt.show()


def plots():
    import numpy as np
    import matplotlib.pyplot as plt
    import pickle
    from matplotlib import rc
    import pandas as pd

    """
    Function to generate a bar chart showing traded energy per configuration and strategy.
    """
    # --- File paths (parameterized for better structure) ---
    base_path = "C:/Users/muham/Documents/GitHub/P2P_Market/results/District1/all_results"
    config_strategy_files = {
        "WTPVBAT_ZI": f"{base_path}/WTPVBAT_ZI/results_P2P_Scenario1_year_r_10.p",
        "WTPVBAT_QL": f"{base_path}/WTPVBAT_QL/results_P2P_Scenario1_year_r_10.p",
        "WT_ZI": f"{base_path}/WT_ZI/results_P2P_Scenario1_year_r_10.p",
        "WT_QL": f"{base_path}/WT_QL/results_P2P_Scenario1_year_r_10.p",
        "WTBAT_ZI": f"{base_path}/WTBAT_ZI/results_P2P_Scenario1_year_r_10.p",
        "WTBAT_QL": f"{base_path}/WTBAT_QL/results_P2P_Scenario1_year_r_10.p",
        "PV_ZI": f"{base_path}/PV_ZI/results_P2P_Scenario1_year_r_10.p",
        "PV_QL": f"{base_path}/PV_QL/results_P2P_Scenario1_year_r_10.p",
        "PVBAT_ZI": f"{base_path}/PVBAT_ZI/results_P2P_Scenario1_year_r_10.p",
        "PVBAT_QL": f"{base_path}/PVBAT_QL/results_P2P_Scenario1_year_r_10.p",
    }

    supply_demand_data = {
        "WT_and_PV": f"{base_path}/WTPVBAT_ZI/mar_dict_P2P_Scenario1.p",
        "Base_District": f"{base_path}/District_without_CSS/results_P2P_Scenario1_year_r_10.p",
    }

    # Enable LaTeX rendering
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')  # Use a serif font (matches LaTeX default)

    # --- Chart settings ---
    font_settings = {
        'xlabel_fontsize': 16,
        'ylabel_fontsize': 16,
        'xtick_fontsize': 14,
        'ytick_fontsize': 14,
        'legend_fontsize': 14,
        'title_fontsize': 16,
    }
    colors_blue = ['#00549F', '#8EBAE5', '#56A3DC', '#0E4E8A', '#1C75BC', '#76C7E6']  # Shades of blue
    colors_red = ["darkred", "firebrick", '#B22222', '#8B0000', '#A52A2A', '#800000', '#990033', '#660000']  # Shades of dark red
    colors_green = ['#006400', '#228B22', '#2E8B57', '#013220', '#004225']  # Shades of dark green
    colors_yellow = ['#B8860B', '#A68A00', '#8B8000', '#FFD700', '#7E6B00']  # Shades of dark yellow

    hatch_patterns = ['', '//', '', '//', '', '//']  # Hatching for redundancy

    configs = ["WT", "WTBAT", "PV", "PVBAT"]  # Main categories
    strategies = ["ZI", "QL"]  # Subcategories
    num_configs = len(configs)
    num_strategies = len(strategies)

    # --- Load results from files ---
    results = {}
    for key, file_path in config_strategy_files.items():
        with open(file_path, "rb") as file:
            results[key] = pickle.load(file)

    # --- Load supply and demand data ---
    supply_demand = {}
    for key, file_path in supply_demand_data.items():
        with open(file_path, "rb") as file:
            supply_demand[key] = pickle.load(file)

    # ______ Traded Energy by Configurations and Strategy ______
    # --- Data preparation ---
    traded_power_total = np.zeros((num_configs, num_strategies))  # 2D array for configs and strategies
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            traded_power_total[c, s] = 0.5 * results[key]["traded_power_total"]/1000  # Add your computation logic here

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12*0.8, 6.75*0.8))
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for bars

    for i, strategy in enumerate(strategies):
        ax.bar(
            bar_positions + i * bar_width,  # Shift based on strategy
            traded_power_total[:, i],  # Values for this strategy
            bar_width,  # Width of the bars
            label=strategy,  # Strategy label
            color=colors_blue[i],  # Bar color
            hatch=hatch_patterns[i],  # Optional hatching
            edgecolor="black"  # Black border for better visibility
        )

    # --- Customizations ---
    ax.set_xlabel('CSS Configurations', fontsize=font_settings['xlabel_fontsize'])
    ax.set_ylabel(r'Traded Energy in in MWh $\rightarrow$', fontsize=font_settings['ylabel_fontsize'], loc="top")
    ax.set_xticks(bar_positions + (bar_width * (num_strategies - 1) / 2))  # Center X-ticks
    ax.set_xticklabels(configs, fontsize=font_settings['xtick_fontsize'])
    ax.tick_params(axis='y', labelsize=font_settings['ytick_fontsize'])
    ax.set_ylim(0, 60)  # Adjust as needed
    ax.legend(title='Strategy', fontsize=font_settings['legend_fontsize'], title_fontsize=14)
    #ax.set_title('Traded Power by Configuration and Strategy', fontsize=font_settings['title_fontsize'])

    # Grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # --- Save and show plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_traded_power_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save at high resolution
    plt.show()
    # ______ Done for Traded Energy by Configurations and Strategy ______

    # ______ Market Supply Cover Factor______
    # --- Data preparation ---
    MSCF = np.zeros((num_configs, num_strategies))  # 2D array for configs and strategies
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            MSCF[c, s] = results[key]["traded_supply_bids"] * 100 # Add your computation logic here

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12*0.8, 6.75*0.8))
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for bars

    for i, strategy in enumerate(strategies):
        ax.bar(
            bar_positions + i * bar_width,  # Shift based on strategy
            MSCF[:, i],  # Values for this strategy
            bar_width,  # Width of the bars
            label=strategy,  # Strategy label
            color=colors_blue[i],  # Bar color
            hatch=hatch_patterns[i],  # Optional hatching
            edgecolor="black"  # Black border for better visibility
        )

    # --- Customizations ---
    ax.set_xlabel('CSS Configurations', fontsize=font_settings['xlabel_fontsize'])
    ax.set_ylabel(r'MSCF in \% $\rightarrow$', fontsize=font_settings['ylabel_fontsize'], loc="top")
    ax.set_xticks(bar_positions + (bar_width * (num_strategies - 1) / 2))  # Center X-ticks
    ax.set_xticklabels(configs, fontsize=font_settings['xtick_fontsize'])
    ax.tick_params(axis='y', labelsize=font_settings['ytick_fontsize'])
    ax.set_ylim(0, 100)  # Adjust as needed
    ax.legend(title='Strategy', fontsize=font_settings['legend_fontsize'], title_fontsize=font_settings['legend_fontsize'])
    # ax.set_title('Market Supply Cover Factor', fontsize=font_settings['title_fontsize'])

    # Grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # --- Save and show plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_MSCF_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save at high resolution
    plt.show()
    # ______ Done for Market Supply Cover Factor______

    # ______ Market Demand Cover Factor______
    # --- Data preparation ---
    MDCF = np.zeros((num_configs, num_strategies))  # 2D array for configs and strategies
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            MDCF[c, s] = results[key]["traded_demand_bids"] * 100 # Add your computation logic here

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12*0.8, 6.75*0.8))
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for bars

    for i, strategy in enumerate(strategies):
        ax.bar(
            bar_positions + i * bar_width,  # Shift based on strategy
            MDCF[:, i],  # Values for this strategy
            bar_width,  # Width of the bars
            label=strategy,  # Strategy label
            color=colors_blue[i],  # Bar color
            hatch=hatch_patterns[i],  # Optional hatching
            edgecolor="black"  # Black border for better visibility
        )

    # --- Customizations ---
    ax.set_xlabel('CSS Configurations', fontsize=font_settings['xlabel_fontsize'])
    ax.set_ylabel(r'MDCF in \% $\rightarrow$', fontsize=font_settings['ylabel_fontsize'], loc="top")
    ax.set_xticks(bar_positions + (bar_width * (num_strategies - 1) / 2))  # Center X-ticks
    ax.set_xticklabels(configs, fontsize=font_settings['xtick_fontsize'])
    ax.tick_params(axis='y', labelsize=font_settings['ytick_fontsize'])
    ax.set_ylim(0, 100)  # Adjust as needed
    ax.legend(title='Strategy', fontsize=font_settings['legend_fontsize'], title_fontsize=font_settings['legend_fontsize'])
    # ax.set_title('Market Demand Cover Factor', fontsize=font_settings['title_fontsize'])

    # Grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # --- Save and show plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_MDCF_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save at high resolution
    plt.show()
    # ______ Done for Market Demand Cover Factor______

    # ______ Economic Gain by Configurations and Strategy ______
    # --- Data preparation ---
    economic_gain = np.zeros((num_configs, num_strategies))  # 2D array for configs and strategies
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            economic_gain[c, s] = results[key]["gain_total"]  # Add your computation logic here

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12*0.8, 6.75*0.8))
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for bars

    colors_ = [colors_yellow[0], colors_green[0]]

    for i, strategy in enumerate(strategies):
        ax.bar(
            bar_positions + i * bar_width,  # Shift based on strategy
            economic_gain[:, i],  # Values for this strategy
            bar_width,  # Width of the bars
            label=strategy,  # Strategy label
            color=colors_[i],  # Bar color
            hatch=hatch_patterns[i],  # Optional hatching
            edgecolor="black"  # Black border for better visibility
        )

    # --- Customizations ---
    ax.set_xlabel('CSS Configurations', fontsize=font_settings['xlabel_fontsize'])
    ax.set_ylabel(r'Economic Gain in EUR $\rightarrow$', fontsize=font_settings['ylabel_fontsize'], loc="top")
    ax.set_xticks(bar_positions + (bar_width * (num_strategies - 1) / 2))  # Center X-ticks
    ax.set_xticklabels(configs, fontsize=font_settings['xtick_fontsize'])
    ax.tick_params(axis='y', labelsize=font_settings['ytick_fontsize'])
    ax.set_ylim(0, 15000)  # Adjust as needed
    ax.legend(title='Strategy', fontsize=font_settings['legend_fontsize'])
    # ax.set_title('Economic Gain by Configuration and Strategy', fontsize=font_settings['title_fontsize'])

    # Grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # --- Save and show plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_eco_gain_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save at high resolution
    plt.show()
    # ______ Done for Financial Gain by Configurations and Strategy ______

    # ______ Cumulative Trading Revenue for Each Strategy and Scenario ______
    # --- Data preparation ---
    cumulative_revenue = {}
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            # Get additional revenue series (as specified)
            additional_revenue_series = (results[key]["additional_revenue"][len(results[key]["additional_revenue"])-1]
                                         + results[key]["traded_power"][len(results[key]["additional_revenue"])-1] * 0.080)

            # Compute cumulative revenue for the strategy
            if key not in cumulative_revenue:
                cumulative_revenue[key] = np.cumsum(additional_revenue_series)  # Cumulative sum of revenue

    # Create individual plots for each scenario
    for c, config in enumerate(configs):
        plt.figure(figsize=(12, 6))  # Create a new figure for each scenario

        # Plot cumulative revenue for both strategies
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            plt.plot(
                range(len(cumulative_revenue[key])),
                cumulative_revenue[key],  # Use cumulative revenue series
                label=f"{strategy}",
                color=colors_blue[s] if strategy == "ZI" else colors_green[s],  # Use blue for ZI, green for QL
                linestyle='-' if strategy == "ZI" else '--',  # Different line styles per strategy
                linewidth=2
            )

        # Add titles, labels, and legend
        plt.title(f'Cumulative Trading Revenue Over Time (CSS configuration: {config})', fontsize=16)
        plt.xlabel('Time [hours]', fontsize=14)
        plt.ylabel(r'Cumulative Revenue [€]', fontsize=14)
        plt.grid(alpha=0.3)
        plt.legend(loc='upper left', fontsize=12)

        # Save and display each scenario's graph
        save_path = f"C:/Users/muham/Documents/GitHub/results/District1/pictures/cumulative_revenue_{config}.png"
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.show()
    # ______ Done for Cumulative Trading Revenue ______

    # ______ Cumulative Saved Costs for Each Strategy and Scenario ______
    # --- Data preparation ---
    cumulative_saved_costs = {}  # Dictionary to store cumulative saved costs
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            # Aggregate saved costs for all buildings at each time step
            saved_costs_series = [sum(results[key]["saved_costs"][i] for i in range(len(results[key]["saved_costs"])))]

            # Compute cumulative saved costs
            if key not in cumulative_saved_costs:
                cumulative_saved_costs[key] = np.cumsum(saved_costs_series)  # Cumulative sum at each time step

    # Create individual plots for each scenario
    for c, config in enumerate(configs):
        plt.figure(figsize=(12, 6))  # Create a new figure for each scenario

        # Plot cumulative saved costs for both strategies
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            plt.plot(
                range(len(cumulative_saved_costs[key])),
                cumulative_saved_costs[key],  # Use cumulative saved costs series
                label=f"{strategy}",
                color=colors_red[s] if strategy == "ZI" else colors_yellow[s],  # Use red for ZI, yellow for QL
                linestyle='-' if strategy == "ZI" else '--',  # Different line styles per strategy
                linewidth=2
            )

        # Add titles, labels, and legend
        plt.title(f'Cumulative Collective Saved Costs Over Time (CSS Configuration: {config})', fontsize=16)
        plt.xlabel('Time [hours]', fontsize=14)
        plt.ylabel(r'Cumulative Saved Costs [€]', fontsize=14)
        plt.grid(alpha=0.3)
        plt.legend(loc='upper left', fontsize=12)

        # Save and display each scenario's graph
        save_path = f"C:/Users/muham/Documents/GitHub/results/District1/pictures/cumulative_saved_costs_{config}.png"
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.show()
    # ______ Done for Cumulative Saved Costs ______

    # # ______ Combined Plots for Revenue and Saved Costs for Each Configuration ______
    #
    # cumulative_saved_costs = {}  # Dictionary to store cumulative saved costs
    # max_y_value = 0  # Track global max y-axis value across all configurations
    #
    # # Pre-compute cumulative saved costs and find the max y-axis value
    # for c, config in enumerate(configs):
    #     for s, strategy in enumerate(strategies):
    #         key = f"{config}_{strategy}"
    #
    #         # Aggregate saved costs for all buildings at each time step
    #         saved_costs_series = [sum(results[key]["saved_costs"][i] for i in range(len(results[key]["saved_costs"])))]
    #
    #         # Compute cumulative saved costs
    #         if key not in cumulative_saved_costs:
    #             cumulative_saved_costs[key] = np.cumsum(saved_costs_series)  # Cumulative sum at each time step
    #
    #         # Safely calculate maximum value for y-axis scaling
    #         # if key in cumulative_saved_costs:
    #         #     max_y_value = max(max_y_value, np.max(cumulative_saved_costs[key]))
    #         if "additional_revenue" in results[key]:
    #             max_y_value = max(max_y_value, np.max(results[key]["additional_revenue"]))
    #
    # # Add 10% buffer to the max y-value for aesthetics
    # max_y_value *= 1.1
    #
    # # Generate plots for each configuration
    # for c, config in enumerate(configs):
    #     # Create a figure for the current configuration
    #     plt.figure(figsize=(6, 4))
    #
    #     # Loop through strategies and merge revenue and cost savings into a single graph
    #     for s, strategy in enumerate(strategies):
    #         key = f"{config}_{strategy}"
    #
    #         # --- Plot Additional Revenue ---
    #         additional_revenue_series = (
    #         results[key]["additional_revenue"][len(results[key]["additional_revenue"]) - 1])
    #         cumulative_revenue = np.cumsum([additional_revenue_series])  # Single entry cumulative sum
    #
    #         plt.plot(
    #             range(len(cumulative_revenue)),
    #             cumulative_revenue,
    #             label=rf"Revenue ({strategy})",  # LaTeX-compatible label
    #             color=colors_blue[0],  # Dark blue for revenue
    #             linestyle='-' if strategy == "QL" else '--',  # QL: solid, ZI: dashed
    #             linewidth=1
    #         )
    #
    #         # --- Plot Saved Costs ---
    #         if key in cumulative_saved_costs:
    #             plt.plot(
    #                 range(len(cumulative_saved_costs[key])),
    #                 cumulative_saved_costs[key],
    #                 label=rf"Cost Savings ({strategy})",  # LaTeX-compatible label
    #                 color=colors_red[0],  # Dark red for cost savings
    #                 linestyle='-' if strategy == "QL" else '--',  # QL: solid, ZI: dashed
    #                 linewidth=1
    #             )
    #
    #     # --- Add Fixed Scaling and Labels ---
    #     # Set a fixed y-axis scale for comparison across configurations
    #     plt.ylim(0, 10000)
    #     plt.xlim(0, 8760)
    #     # plt.title(rf"Cumulative Revenue and Cost Savings: {config}", fontsize=16)
    #     plt.xlabel(r"Time [hours]", fontsize=14)
    #     plt.ylabel(r"Cumulative Values [€]", fontsize=14)
    #     plt.grid(alpha=0.3)
    #     plt.legend(fontsize=12)
    #
    #     # --- Save and Show the Plot ---
    #     plt.tight_layout()  # Ensure the layout fits the title and legend
    #     save_path = f"C:/Users/muham/Documents/GitHub/results/District1/pictures/cumulative_{config}.png"
    #     plt.savefig(save_path, dpi=300)
    #     plt.show()
    # # ______ Done for Combined Revenue and Cost Savings Plots ______

    # ______ Combined Plots for Revenue and Saved Costs for Each Configuration (Ordered Legends and Colors) ______

    cumulative_saved_costs = {}  # Dictionary to store cumulative saved costs
    max_y_value = 0  # Track global max y-axis value across all configurations

    # Pre-compute cumulative saved costs and find the max y-axis value
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"

            # Aggregate saved costs for all buildings at each time step
            saved_costs_series = [
                sum(results[key]["saved_costs"][i] for i in range(len(results[key]["saved_costs"]) - 1))]

            # Compute cumulative saved costs
            if key not in cumulative_saved_costs:
                cumulative_saved_costs[key] = np.cumsum(saved_costs_series)  # Cumulative sum at each time step

            # Safely update maximum y-axis value for scaling
            if "additional_revenue" in results[key]:
                additional_revenue_series = results[key]["additional_revenue"][
                    len(results[key]["additional_revenue"]) - 1]  # Full times series
                max_y_value = max(max_y_value, np.max(np.cumsum(additional_revenue_series)))  # Cumulative max value

    # Add 10% buffer to the max y-value for aesthetics
    max_y_value *= 1.1

    # Colors and linestyle mappings
    line_properties = {
        "Cost Savings (ZI)": {"color": "darkred", "linestyle": "--"},
        "Cost Savings (QL)": {"color": "firebrick", "linestyle": "-"},
        "Revenue (ZI)": {"color": "navy", "linestyle": "--"},
        "Revenue (QL)": {"color": "royalblue", "linestyle": "-"}
    }

    # Generate plots for each configuration
    for c, config in enumerate(configs):
        # Create a figure for the current configuration
        plt.figure(figsize=(6, 4))

        # --- Plot Cost Savings (ZI) ---
        key_zi = f"{config}_ZI"
        if key_zi in cumulative_saved_costs:
            plt.plot(
                range(len(cumulative_saved_costs[key_zi])),
                cumulative_saved_costs[key_zi],
                label="Cost Savings (ZI)",  # Legend label
                color=line_properties["Cost Savings (ZI)"]["color"],  # Dark red
                linestyle=line_properties["Cost Savings (ZI)"]["linestyle"],  # Dashed line
                linewidth=1
            )

        # --- Plot Cost Savings (QL) ---
        key_ql = f"{config}_QL"
        if key_ql in cumulative_saved_costs:
            plt.plot(
                range(len(cumulative_saved_costs[key_ql])),
                cumulative_saved_costs[key_ql],
                label="Cost Savings (QL)",  # Legend label
                color=line_properties["Cost Savings (QL)"]["color"],  # Firebrick
                linestyle=line_properties["Cost Savings (QL)"]["linestyle"],  # Solid line
                linewidth=1
            )

        # --- Plot Revenue (ZI) ---
        if "additional_revenue" in results[key_zi]:
            additional_revenue_zi_series = results[key_zi]["additional_revenue"][
                len(results[key]["additional_revenue"]) - 1]  # Full time series
            cumulative_revenue_zi = np.cumsum(additional_revenue_zi_series)  # Cumulative sum over time
            plt.plot(
                range(len(cumulative_revenue_zi)),
                cumulative_revenue_zi,
                label="Revenue (ZI)",  # Legend label
                color=line_properties["Revenue (ZI)"]["color"],  # Navy
                linestyle=line_properties["Revenue (ZI)"]["linestyle"],  # Dashed line
                linewidth=1
            )

        # --- Plot Revenue (QL) ---
        if "additional_revenue" in results[key_ql]:
            additional_revenue_ql_series = results[key_ql]["additional_revenue"][
                len(results[key]["additional_revenue"]) - 1]  # Full time series
            cumulative_revenue_ql = np.cumsum(additional_revenue_ql_series)  # Cumulative sum over time
            plt.plot(
                range(len(cumulative_revenue_ql)),
                cumulative_revenue_ql,
                label="Revenue (QL)",  # Legend label
                color=line_properties["Revenue (QL)"]["color"],  # Royal blue
                linestyle=line_properties["Revenue (QL)"]["linestyle"],  # Solid line
                linewidth=1
            )

        # --- Add Fixed Scaling and Labels ---
        # Set a fixed y-axis scale for comparison across configurations
        plt.ylim(0, max_y_value)  # Dynamic y-axis limit
        plt.xlim(0, 8760)  # Time in hours
        plt.xlabel(r"Time in hours $\rightarrow$", fontsize=16, loc="right")
        plt.ylabel(r"Cumulative Values in EUR $\rightarrow$", fontsize=16, loc="top")
        # plt.title(rf"Additional Revenue and Cost Savings: {config}", fontsize=16)
        plt.grid(alpha=0.3)

        # Add legend in required sorted order
        handles, labels = plt.gca().get_legend_handles_labels()
        order = ["Cost Savings (ZI)", "Cost Savings (QL)", "Revenue (ZI)", "Revenue (QL)"]
        sorted_handles_labels = [(h, l) for _, (h, l) in sorted(zip(order, zip(handles, labels)), key=lambda x: x[0])]
        handles, labels = zip(*sorted_handles_labels)
        plt.legend(handles, labels, fontsize=14)
        # Adjust tick label font size
        plt.tick_params(axis='both', which='major', labelsize=14)  # Adjust the scale font size (numbers)

        # --- Save and Show the Plot ---
        plt.tight_layout()  # Ensure the layout fits the title and legend
        save_path = f"C:/Users/muham/Documents/GitHub/results/District1/pictures/cumulative_{config}.png"
        plt.savefig(save_path, dpi=300)
        plt.show()
    # ______ Done for Combined Revenue and Cost Savings Plots (Ordered Legends and Colors) ______

    # ______ Weekly Average Market Clearing Price (MCP) for Each Configuration ______
    # --- Data preparation ---
    weekly_avg_MCP = {}  # Dictionary to store weekly average MCP
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            # Extract the hourly MCP series
            hourly_MCP = results[key]["av_MCP"]  # MCP for each hour of the year (8760 hours)

            # # Compute weekly averages (168 hours per week)
            # num_weeks = len(hourly_MCP) // 168  # Total number of full weeks
            # weekly_avg_MCP[key] = [
            #     np.mean(hourly_MCP[week * 168: (week + 1) * 168])
            #     for week in range(num_weeks)]

            # Compute weekly averages (168 hours per week) while ignoring zeros
            num_weeks = len(hourly_MCP) // 168  # Total number of full weeks
            weekly_avg_MCP[key] = [
                np.mean([value for value in hourly_MCP[week * 168: (week + 1) * 168] if value != 0])
                for week in range(num_weeks)
            ]

    # Create individual plots for each configuration
    for c, config in enumerate(configs):
        plt.figure(figsize=(12 * 0.5, 6.75 * 0.5))  # Create a new figure for each configuration

        # Plot weekly average MCP for both strategies
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            plt.plot(
                range(len(weekly_avg_MCP[key])),  # Weeks on the x-axis
                weekly_avg_MCP[key],  # Weekly average MCP series
                label=f"{strategy}",
                color=colors_red[s] if strategy == "QL" else colors_yellow[s],  # Use red for ZI, yellow for QL
                linestyle='-' if strategy == "QL" else '--',  # Different line styles for ZI and QL
                linewidth=1
            )

        # Add titles, labels, and legend
        plt.ylim(0.18, 0.30)
        # plt.yticks([0.15, 0.20, 0.25, 0.30])  # Set specific y-axis ticks
        plt.xlim(0, 51)
        # plt.title(f'Weekly Average MCP (CSS Configuration: {config})', fontsize=16)
        plt.xlabel(r'Time in weeks $\rightarrow$', fontsize=16, loc="right")
        plt.ylabel(r'MCP in EUR/kWh $\rightarrow$', fontsize=16, loc="top")
        plt.grid(alpha=0.15)
        plt.legend(
            loc='upper center',  # Position the legend above the bottom of the graph
            bbox_to_anchor=(0.5, 1),  # Place the legend below the graph (centered horizontally)
            fontsize=14,  # Legend font size
            ncol=len(strategies),  # Number of columns in the legend (One column per strategy)
            frameon=True
        )
        # Adjust tick label font size
        plt.tick_params(axis='both', which='major', labelsize=14)  # Adjust the scale font size (numbers)

        # Save and display each scenario's graph
        save_path = f"C:/Users/muham/Documents/GitHub/results/District1/pictures/weekly_avg_MCP_{config}.png"
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.show()

    # ______ Done for Weekly Average MCP ______

    # ______ Plot of Demand, Wind, and PV Power Over Time (Monthly Averaged) ______
    # --- Data preparation ---

    monthly_avg_values = {"demand": [], "wind": [], "pv": []}
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Extract data for demand, wind, and PV
    demand_series = supply_demand["Base_District"]["total_p_purchase"]  # Hourly demand for the year
    wind_series = supply_demand["WT_and_PV"]["CSS_profiles"]["wind_power"]  # Hourly wind power
    pv_series = supply_demand["WT_and_PV"]["CSS_profiles"]["pv_power"]  # Hourly PV power

    # Compute monthly averages (group over 720 hours—30 days per month assumption)
    num_months = len(demand_series) // 720  # Total number of full months (8760 hours / 720 hours per month)
    monthly_avg_values["demand"] = [
        np.mean(demand_series[month * 720: (month + 1) * 720]) for month in range(num_months)]
    monthly_avg_values["wind"] = [
        np.mean(wind_series[month * 720: (month + 1) * 720]) / 1000 for month in range(num_months)]
    monthly_avg_values["pv"] = [
        np.mean(pv_series[month * 720: (month + 1) * 720]) / 1000 for month in range(num_months)]

    # --- Plotting ---
    plt.figure(figsize=(12, 6))  # Create a new figure
    months = range(1, len(monthly_avg_values["demand"]) + 1)  # Month indices for the x-axis

    # Plot demand (dark red) with hatched area
    plt.plot(
        months, monthly_avg_values["demand"],
        label="Demand", color="#8B0000",  # Dark red
        linestyle="-", linewidth=2)
    plt.fill_between(
        months, monthly_avg_values["demand"], alpha=0.2, color="#8B0000", hatch="//")

    # Plot wind power (dark blue) with hatched area
    plt.plot(
        months, monthly_avg_values["wind"],
        label="Wind Power", color="#00549F",  # Dark blue
        linestyle="--", linewidth=2)
    plt.fill_between(
        months, monthly_avg_values["wind"], alpha=0.2, color="#00549F", hatch="\\")

    # Plot PV power (dark yellow) with hatched area
    plt.plot(
        months, monthly_avg_values["pv"],
        label="PV Power", color="#B8860B",  # Dark yellow
        linestyle=":", linewidth=2)
    plt.fill_between(
        months, monthly_avg_values["pv"], alpha=0.2, color="#B8860B", hatch="||")

    # --- Customizations and Labels ---
    #plt.title("Monthly Averaged Demand, Wind, and PV Potential", fontsize=16)
    plt.xlim(1, 12)
    plt.ylim(0, 38)
    plt.xlabel("Month", fontsize=16)
    plt.ylabel(r"Averaged Power in kW $\rightarrow$", fontsize=16, loc="top")
    plt.xticks(months, month_names[:len(months)], fontsize=14)  # Use month names from the list
    plt.grid(alpha=0.3)
    plt.legend(loc="upper right", fontsize=14)

    # --- Save and Show the Plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/monthly_demand_wind_pv.png"
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)  # Save the file as PNG
    plt.show()
    # ______ Done for Demand, Wind, and PV Power Plot ______

    # ______ Daily Average of Sum of Q-Value Change ______
    # --- Data preparation ---
    daily_avg_q_value_change = []

    # Extract hourly Q-value change data for WTPVBAT_QL
    q_value_change_series = results["WTPVBAT_QL"]["CSS_q_value_change"]  # Hourly Q-value change data

    # Compute daily averages (group over 24 hours)
    num_days = len(q_value_change_series) // 24  # Total number of full days
    daily_avg_q_value_change = [abs(np.mean(q_value_change_series[day * 24: (day + 1) * 24])) for day in range(num_days)]

    # --- Plotting ---
    plt.figure(figsize=(12, 6))  # Create a new figure
    days = range(1, len(daily_avg_q_value_change) + 1)  # Define day indices for the x-axis

    # Plot the daily average Q-value change (blue)
    plt.plot(
        days, daily_avg_q_value_change,
        label="Daily Avg Q-Value Change", color=colors_blue[0], linestyle="-", linewidth=2)

    # --- Customizations and Labels ---
    # plt.title("Daily Average of Total Absolute Q-Value Change", fontsize=16)
    plt.xlabel(r"Time in days $\rightarrow$", fontsize=16, loc="right")
    plt.ylabel(r"Daily average of $\Delta Q_\mathrm{total}$ $\rightarrow$", fontsize=16, loc="top")
    plt.xlim(0, 365)
    plt.ylim(0, 0.55)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(alpha=0.3)
    # plt.legend(loc="upper left", fontsize=12)

    # --- Save and Show the Plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/daily_avg_abs_q_value_change.png"
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)  # Save the file as PNG
    plt.show()
    # ______ Done for Daily Average of Q-Value Change ______

    # ______ Weekly Average of Sum of Q-Value Change ______
    # --- Data preparation ---
    weekly_avg_q_value_change = []

    # Extract hourly Q-value change data for WTPVBAT_QL
    q_value_change_series = results["WTPVBAT_QL"]["CSS_q_value_change"]  # Hourly Q-value change data

    # Compute weekly averages (group over 168 hours)
    num_weeks = len(q_value_change_series) // 168  # Total number of full weeks
    weekly_avg_q_value_change = [
        np.mean(q_value_change_series[week * 168: (week + 1) * 168]) for week in range(num_weeks)]

    # --- Plotting ---
    plt.figure(figsize=(12, 6))  # Create a new figure
    weeks = range(1, len(weekly_avg_q_value_change) + 1)  # Define week indices for the x-axis

    # Plot the weekly average Q-value change (green)
    plt.plot(
        weeks, weekly_avg_q_value_change,
        label="Weekly Avg Q-Value Change", color="green", linestyle="-", linewidth=2)

    # --- Customizations and Labels ---
    plt.xlim(0, 52)
    plt.title("Weekly Average of Q-Value Change (WTPVBAT_QL)", fontsize=16)
    plt.xlabel("Time [weeks]", fontsize=14)
    plt.ylabel("Average Q-Value Change", fontsize=14)
    plt.grid(alpha=0.3)
    plt.legend(loc="upper left", fontsize=12)

    # --- Save and Show the Plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/weekly_avg_q_value_change.png"
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)  # Save the file as PNG
    plt.show()
    # ______ Done for Weekly Average of Q-Value Change ______

    # ______ Participants Cost Savings and CSS Revenue by Configurations and Strategy ______
    # --- Data Preparation ---
    participants_gain = np.zeros((num_configs, num_strategies))  # 2D array for participants' gain
    css_revenue = np.zeros((num_configs, num_strategies))  # 2D array for CSS revenue
    # Prepare gain values for participants and CSS revenue
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            # Calculate total participants' gain (excluding CSS)
            participants_gain[c, s] = sum(
                results[key]["gain_per_building"][:len(results[key]["gain_per_building"]) - 1]  # Exclude CSS
            )
            # Extract the CSS revenue (last entry in gain_per_building)
            css_revenue[c, s] = results[key]["gain_per_building"][-1]
    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.15  # Thinner width for the bars
    bar_positions = np.arange(len(configs))  # Base positions for the categories
    # Colors of the bars for visual consistency
    colors = ["darkred", "firebrick", "navy", "royalblue"]
    # Define offsets for the individual bars within a category
    # Bars are grouped as: [Participant Cost Savings (ZI, QL), CSS Revenue (ZI, QL)].
    offsets = [-1.5 * bar_width, -0.5 * bar_width, 0.5 * bar_width, 1.5 * bar_width]
    # Plot bars: grouped with Participant Savings followed by CSS Revenue
    # Order: Cost Savings (ZI), Cost Savings (QL), Revenue (ZI), Revenue (QL)
    # Use hatching for QL bars
    for idx, (data, strategy_label, color, hatch) in enumerate([
        (participants_gain[:, 0], "Cost Savings (ZI)", colors[0], ""),  # Cost Savings (ZI)
        (participants_gain[:, 1], "Cost Savings (QL)", colors[1], "//"),  # Cost Savings (QL, with hatching)
        (css_revenue[:, 0], "Add. Revenue (ZI)", colors[2], ""),  # CSS Revenue (ZI)
        (css_revenue[:, 1], "Add. Revenue (QL)", colors[3], "//")  # CSS Revenue (QL, with hatching)
    ]):
        ax.bar(
            bar_positions + offsets[idx],  # Offset for the given bar in the group
            data,  # Data for the bar
            bar_width,  # Bar width
            label=strategy_label,  # Label for the legend
            color=color,  # Bar color
            hatch=hatch,  # Hatching for QL bars
            edgecolor="black"  # Black border for better visibility
        )
    # --- Customizations ---
    ax.set_xlabel('CSS Configurations', fontsize=16)
    ax.set_ylabel(r'Savings and Revenue in EUR $\rightarrow$', fontsize=16, loc="top")
    ax.set_xticks(bar_positions)  # Align X-ticks to categories
    ax.set_xticklabels(configs, fontsize=14)
    ax.tick_params(axis='y', labelsize=14)
    # ax.set_title('Participants Savings and CSS Revenue by Configuration and Strategy', fontsize=16)
    ax.legend(
        # title='Component and Strategy',
        fontsize=14,
        title_fontsize=14,
        loc='upper center',  # Position the legend at the top center relative to bbox
        bbox_to_anchor=(0.5, 1.1),  # Move the legend below the x-axis (centered horizontally)
        ncol=4  # Set legend items in 2 columns for compactness
    )
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)  # Add gridlines for readability
    # --- Save and Show Plot ---
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_participants_savings_css_revenue_by_config_side_by_side.png"
    plt.tight_layout()  # Ensure proper layout
    plt.savefig(save_path, dpi=300)  # Save plot as a high-resolution image
    plt.show()
    # ______ Done for Participants Cost Savings and CSS Revenue by Configurations and Strategy ______

    # ______ Peak Feed-in by Configurations and Strategy ______
    # --- Data Preparation ---
    peak_feed_in = np.zeros((num_configs, num_strategies))  # 2D array for configs and strategies
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            peak_feed_in[c, s] = results[key]["peak_feed_in"]  # Extract peak feed-in for each config and strategy

    # Extract the peak feed-in value from the loaded data
    comparison_peak_feed_in = supply_demand["Base_District"]["peak_feed_in"]

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(8, 4.5))  # Set figure size
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for configurations

    # Define shades of red for each strategy
    # colors_red = ["darkred", "lightcoral"]  # Darker red for strategy 1, lighter red for strategy 2

    # Plot bars for each strategy
    for i, strategy in enumerate(strategies):  # Loop over strategies (ZI, QL)
        ax.bar(
            bar_positions + i * bar_width,  # Shift bars for each strategy
            peak_feed_in[:, i],  # Values of peak feed-in for strategy i
            bar_width,  # Set bar width
            label=strategy,  # Add strategy label for legend
            color=colors_red[i],  # Use shades of red
            edgecolor="black"  # Add black border for better visibility
        )

    # --- Add Horizontal Line for Comparison ---
    # Add a horizontal line representing the peak feed-in from "District_without_CSS"
    ax.axhline(
        y=comparison_peak_feed_in,  # Y-value of the horizontal line
        color="gray",  # Color of the line (gray for distinction)
        linestyle="--",  # Dashed line for style
        linewidth=1.5,  # Line width
        label="District without CSS"  # Label for the line
    )

    # --- Customizations ---
    # Add axis labels and title
    ax.set_xlabel('CSS Configurations', fontsize=14)
    ax.set_ylabel('Peak Feed-in [kW]', fontsize=14)  # Unit: [kW]
    ax.set_xticks(bar_positions + (bar_width / 2))  # Center X-ticks between grouped bars
    ax.set_xticklabels(configs, fontsize=12)  # Configuration labels (WT, WTBAT, PV, PVBAT)
    ax.tick_params(axis='y', labelsize=12)  # Adjust Y-axis tick label size
    ax.set_ylim(0, np.max(peak_feed_in) * 1.1)  # Add a 10% buffer to the max value for clarity

    # Add a legend
    ax.legend(title='Bidding Strategy', fontsize=12, title_fontsize=13)  # Legend with title

    # Add grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)  # Dashed gridlines on Y-axis for better readability

    # Add a title to the plot
    ax.set_title('Peak Feed-in by Configuration and Strategy', fontsize=16)

    # --- Save and Show Plot ---
    # Save path for the plot
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_peak_feed_in_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save the plot as a high-resolution image
    plt.show()
    # ______ Done for Peak Feed-in by Configurations and Strategy ______

    import pickle

    # ______ Peak Purchase by Configurations and Strategy ______
    # --- Data Preparation ---
    # Initialize 2D array for peak purchase data for configs and strategies
    peak_purchase = np.zeros((num_configs, num_strategies))
    for c, config in enumerate(configs):
        for s, strategy in enumerate(strategies):
            key = f"{config}_{strategy}"
            peak_purchase[c, s] = results[key]["peak_purchase"]  # Extract peak purchase for each config and strategy

    # Extract the peak purchase value from the loaded data
    comparison_peak_purchase = supply_demand["Base_District"]["peak_purchase"]

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(12*0.8, 6.75*0.8))  # Set figure size
    bar_width = 0.2  # Width of each bar
    bar_positions = np.arange(num_configs)  # Base positions for configurations

    # Define color for each strategy
    colors = ["darkred", "lightcoral", "navy", "royalblue"]
    # colors_red = ["darkred", "lightcoral"]  # Darker red for strategy 1, lighter red for strategy 2

    # Plot bars for each strategy
    for i, strategy in enumerate(strategies):  # Loop over strategies (ZI, QL)
        ax.bar(
            bar_positions + i * bar_width,  # Shift bars for each strategy
            peak_purchase[:, i],  # Values of peak purchase for strategy i
            bar_width,  # Set bar width
            label=strategy,  # Add strategy label for legend
            color=colors[i],  # Use shades of red
            hatch=hatch_patterns[i],  # Optional hatching
            edgecolor="black"  # Add black border for better visibility
        )

    # --- Add Horizontal Line for Comparison ---
    # Add a horizontal line representing the peak purchase from "District_without_CSS"
    ax.axhline(
        y=comparison_peak_purchase,  # Y-value of the horizontal line
        color="gray",  # Color of the line (gray for distinction)
        linestyle="--",  # Dashed line for style
        linewidth=1.5,  # Line width
        label="District without CSS"  # Label for the line
    )

    # --- Customizations ---
    # Add axis labels and title
    ax.set_xlabel('CSS Configurations', fontsize=16)
    ax.set_ylabel(r'Peak Purchase in kW $\rightarrow$', fontsize=16, loc="top")  # Unit: [kW]
    ax.set_xticks(bar_positions + (bar_width / 2))  # Center X-ticks between grouped bars
    ax.set_xticklabels(configs, fontsize=14)  # Configuration labels (WT, WTBAT, PV, PVBAT)
    ax.tick_params(axis='y', labelsize=14)  # Adjust Y-axis tick label size
    ax.set_ylim(0, max(comparison_peak_purchase, np.max(peak_purchase)) * 1.1)  # Dynamic scaling with 10% buffer

    # Add a legend
    ax.legend(title='Bidding Strategy and Baseline', fontsize=14, title_fontsize=14)  # Legend with title

    # Add grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)  # Dashed gridlines on Y-axis for better readability

    # Add a title to the plot
    # ax.set_title('Peak Purchase by Configuration and Strategy', fontsize=16)

    # --- Save and Show Plot ---
    # Save path for the plot
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/bar_diagram_peak_purchase_by_config_and_strategy.png"
    plt.tight_layout()  # Ensure no overlap in layout
    plt.savefig(save_path, dpi=300)  # Save the plot as a high-resolution image
    plt.show()
    # ______ Done for Peak Purchase by Configurations and Strategy ______

    # ______ Peak Purchase by Configurations and Strategy ______
    # ______ Peak Purchase by Configurations and Strategy ______

    # ______ Wind profile _____
    from scipy.interpolate import make_interp_spline

    # Define the data (creating a DataFrame for simplicity)
    data = {
        "wind_speed": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                       16, 17, 18, 19, 20, 20.0001, 21, 22, 23, 24, 25],
        "power": [0, 0, 5, 10, 17, 25, 34, 50, 63, 81, 100, 100, 100, 100,
                  100, 100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0]
    }
    df = pd.DataFrame(data)

    # Perform cubic interpolation
    x_new = np.linspace(df["wind_speed"].min(), df["wind_speed"].max(),
                        50)  # Generate 300 points between the min and max wind speed
    spl = make_interp_spline(df["wind_speed"], df["power"], k=1)  # Cubic spline interpolation
    y_smooth = spl(x_new)

    # Create the graph
    plt.figure(figsize=(10, 6))  # Set figure size
    plt.plot(x_new, y_smooth, label="Power Curve (Smoothed)", color=colors_blue[0], linewidth=2)
    # plt.plot(df["wind_speed"], df["power"], label="Power Curve", color=colors_blue[0], linewidth=2)

    # Customize X-axis label
    plt.xlabel(r"Wind speed in m/s $\rightarrow$", fontsize=16, loc="right")
    plt.xlim(0, 22)  # Limit the x-axis to the wind speed range
    # Customize Y-axis label
    plt.ylabel(r"$P_\mathrm{WT, el}$ in W $\rightarrow$", fontsize=16, loc="top")
    plt.ylim(-5, 105)  # Limit the y-axis to the power range
    # Add title
    plt.title("Wind Turbine Power Curve", fontsize=16)

    # Add grid for better readability
    plt.grid(alpha=0.3)

    # Save path for the plot
    save_path = "C:/Users/muham/Documents/GitHub/results/District1/pictures/wind_turbine_power_curve.png"

    # Show the plot
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)  # Save the plot as a high-resolution image
    plt.show()
    # ______ Done for Wind profile ______


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

    volume = 0
    for n_opt in range(par_rh["n_opt"] - int(36/5)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + 5):
                volume += opti_res[n_opt][n][4][19][t]/1000

    from_grid = np.zeros(900)
    for n_opt in range(par_rh["n_opt"] - int(36/5)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + 5):
                from_grid[t - par_rh["hour_start"][0]] += mar_dict["transactions_with_grid"][n_opt]["power_from_grid"][n][t]
    to_grid = np.zeros(900)
    for n_opt in range(par_rh["n_opt"] - int(36/5)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + 5):
                to_grid[t - par_rh["hour_start"][0]] += mar_dict["transactions_with_grid"][n_opt]["power_to_grid"][n][t]

    A = np.zeros((2,900))
    b = 0
    B = np.zeros(900)
    for t in range(900):
        if from_grid[t] > 0 and to_grid[t] > 0:
            b +=1
            A[0, t] = from_grid[t]
            A[1, t] = to_grid[t]
            B[t] = min(from_grid[t], to_grid[t])
    return