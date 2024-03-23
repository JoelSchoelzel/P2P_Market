import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle


def calc_results_p2p(par_rh, block_bids, options, block_length, nego_results, transactions_grid):

    last_n_opt = par_rh["n_opt"]
    time_steps = []
    for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + block_length):
        time_steps.append(i)

    # --------------------- SCF, DCF ---------------------
    total_demand = {t: {} for t in time_steps}
    total_supply = {t: {} for t in time_steps}

    for opt in range(par_rh["n_opt"]):
        for t in time_steps:
            total_demand[t] = {"bes_" + str(n): 0 for n in range(options["nb_bes"])}
            total_supply[t] = {"bes_" + str(n): 0 for n in range(options["nb_bes"])}

    for opt in range(par_rh["n_opt"]):
        for n in range(options["nb_bes"]):
            valid_time_steps = {k: v for k, v in block_bids[opt]["bes_" + str(n)].items() if isinstance(k, int)}
            for t in valid_time_steps:
                if isinstance(block_bids[opt]["bes_"+str(n)][t], list) and block_bids[opt]["bes_"+str(n)][t][2] == "True":
                    total_demand[t]["bes_"+str(n)] = block_bids[opt]["bes_"+str(n)][t][1]/1000 # convert from Wh to kWh
                elif isinstance(block_bids[opt]["bes_"+str(n)][t], list) and block_bids[opt]["bes_"+str(n)][t][2] == "False":
                    total_supply[t]["bes_"+str(n)] = block_bids[opt]["bes_"+str(n)][t][1]/1000 # convert from Wh to kWh

    # Initialize the variable to store the sum of all supplies
    total_supply_month = 0
    total_demand_month = 0
    total_demand_all_bes = {}
    total_supply_all_bes = {}
    scf = {}
    dcf = {}
    for i in time_steps:
        total_supply_all_bes[i] = 0
        total_demand_all_bes[i] = 0

    for t in total_supply:
        for building in total_supply[t]:
            total_supply_all_bes[t] += total_supply[t][building]
            total_supply_month += total_supply[t][building]

    for t in total_demand:
        for building in total_demand[t]:
            total_demand_all_bes[t] += total_demand[t][building]
            total_demand_month += total_demand[t][building]

    # calculate scf dcf for each time step
    for t in time_steps:
        if total_supply_all_bes[t] > 0:
            scf[t] = min(total_supply_all_bes[t], total_demand_all_bes[t]) / total_supply_all_bes[t]
        if total_demand_all_bes[t] > 0:
            dcf[t] = min(total_supply_all_bes[t], total_demand_all_bes[t]) / total_demand_all_bes[t]

    # Calculate the Supply Coverage Factor (SCF) and Demand Coverage Factor (DCF) for the month
    if total_supply_month > 0:
        total_scf_month = min(total_supply_month, total_demand_month) / total_supply_month
    else:
        total_scf_month = 0

    if total_demand_month > 0:
        total_dcf_month = min(total_supply_month, total_demand_month) / total_demand_month
    else:
        total_dcf_month = 0

    # --------------------- MDCF, MSCF ---------------------
    traded_power = {}
    price = {}
    additional_revenue = {}
    saved_costs = {}
    average_trade_price = {}
    gain = {}

    for i in time_steps:
        traded_power[i] = 0
        additional_revenue[i] = 0
        saved_costs[i] = 0
        gain[i] = 0
        average_trade_price[i] = 0
        price[i] = {}

    for opt in range(par_rh["n_opt"]):
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                valid_time_steps = {k: v for k, v in nego_results[opt][round_nb][match]["quantity"].items() if isinstance(k, int)}
                for t in valid_time_steps:
                    traded_power[t] += nego_results[opt][round_nb][match]["quantity"][t]/1000 # convert from Wh to kWh
                    price[t][match] = nego_results[opt][round_nb][match]["price"][t] #€/kWh
                    additional_revenue[t] += nego_results[opt][round_nb][match]["additional_revenue"][t]/1000 #€/kWh
                    saved_costs[t] += nego_results[opt][round_nb][match]["saved_costs"][t]/1000 #€/kWh
                    gain[t] = saved_costs[t] + additional_revenue[t]

    # calculate average trade price at time step t for all buildings
    for t in time_steps:
        for match in price[t]:
            average_trade_price[t] += price[t][match]
        if len(price[t]) > 0:
            average_trade_price[t] /= len(price[t])

    total_traded_power = 0
    total_additional_revenue = 0
    total_saved_costs = 0
    total_gain = 0

    for t in time_steps:
        total_traded_power += traded_power[t]
        total_additional_revenue += additional_revenue[t]
        total_saved_costs += saved_costs[t]
        total_gain = gain[t]

    total_mdcf = total_traded_power / total_demand_month
    total_mscf = total_traded_power / total_supply_month

    # --------------------- Total Power from/to Grid ---------------------

    power_from_grid = {}
    power_to_grid = {}

    for i in time_steps:
        power_from_grid[i] = 0
        power_to_grid[i] = 0

    for opt in range(par_rh["n_opt"]):
        for n in range(options["nb_bes"]):
            valid_time_steps = {k: v for k, v in transactions_grid[opt]["power_from_grid"][n].items() if
                                isinstance(k, int)}
            for t in valid_time_steps:
                power_from_grid[t] += transactions_grid[opt]["power_from_grid"][n][t]/1000 # convert from Wh to kWh

    for opt in range(par_rh["n_opt"]):
        for n in range(options["nb_bes"]):
            valid_time_steps = {k: v for k, v in transactions_grid[opt]["power_to_grid"][n].items() if
                                isinstance(k, int)}
            for t in valid_time_steps:
                power_to_grid[t] += transactions_grid[opt]["power_to_grid"][n][t]/1000 # convert from Wh to kWh

    total_power_from_grid = 0
    total_power_to_grid = 0

    for t in time_steps:
        total_power_from_grid += power_from_grid[t]
        total_power_to_grid += power_to_grid[t]

    # --------------------- STORE THE RESULTS ---------------------
    results_over_time = {
        "total_demand": total_demand_all_bes,
        "total_supply": total_supply_all_bes,
        "traded_power": traded_power,
        "scf": scf,
        "dcf": dcf,
        "average_trade_price": average_trade_price,
        "power_from_grid": power_from_grid,
        "power_to_grid": power_to_grid,
        "additional_revenue": additional_revenue,
        "saved_costs": saved_costs,
        "gain": gain
    }

    results_values = {
        "scf_month": total_scf_month,
        "dcf_month": total_dcf_month,
        "mscf_month": total_mscf,
        "mdcf_month": total_mdcf,
        "total_demand_month": total_demand_month,
        "total_supply_month": total_supply_month,
        "total_traded_power": total_traded_power,
        "average_trade_price": average_trade_price,
        "total_power_from_grid": total_power_from_grid,
        "total_power_to_grid": total_power_to_grid,
        "total_additional_revenue": total_additional_revenue,
        "total_saved_costs": total_saved_costs,
        "gain": total_gain

    }

    return results_over_time, results_values




