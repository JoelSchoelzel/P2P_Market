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

    # Calculate the Supply Coverage Factor (SCF) and Demand Coverage Factor (DCF) for the month
    if total_supply_month > 0:
        scf_month = min(total_supply_month, total_demand_month) / total_supply_month
    else:
        scf_month = 0

    if total_demand_month > 0:
        dcf_month = min(total_supply_month, total_demand_month) / total_demand_month
    else:
        dcf_month = 0

    # --------------------- MDCF, MSCF ---------------------
    traded_power = {}
    price = {}
    additional_revenue = {}
    saved_costs = {}
    average_trade_price = {}

    for i in time_steps:
        traded_power[i] = 0
        price[i] = 0
        additional_revenue[i] = 0
        saved_costs[i] = 0
        average_trade_price[i] = 0

    for opt in range(par_rh["n_opt"]):
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                valid_time_steps = {k: v for k, v in nego_results[opt][round_nb][match]["quantity"].items() if isinstance(k, int)}
                for t in valid_time_steps:
                    traded_power[t] += nego_results[opt][round_nb][match]["quantity"][t]/1000 # convert from Wh to kWh
                    price[t] = nego_results[opt][round_nb][match]["price"][t]
                    additional_revenue[t] += nego_results[opt][round_nb][match]["additional_revenue"][t]
                    saved_costs[t] += nego_results[opt][round_nb][match]["saved_costs"][t]

                    # calculate average trade price at time step t for all buildings

    total_traded_power = 0
    total_additional_revenue = 0
    total_saved_costs = 0

    for t in time_steps:
        total_traded_power += traded_power[t]
        total_additional_revenue += additional_revenue[t]
        total_saved_costs += saved_costs[t]

    gain = total_additional_revenue + total_saved_costs

    mdcf = total_traded_power / total_demand_month
    mscf = total_traded_power / total_supply_month

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
        # "time_steps": time_steps,
        "total_demand": total_demand_all_bes,
        "total_supply": total_supply_all_bes,
        "traded_power": traded_power,
        #"average_trade_price": average_trade_price,
        "power_from_grid": power_from_grid,
        "power_to_grid": power_to_grid,
        "additional_revenue": additional_revenue,
        "saved_costs": saved_costs,
    }

    results_values = {
        "scf_month": scf_month,
        "dcf_month": dcf_month,
        "mscf_month": mscf,
        "mdcf_month": mdcf,
        "total_demand_month": total_demand_month,
        "total_supply_month": total_supply_month,
        "total_traded_power": total_traded_power,
        "average_trade_price": average_trade_price,
        "total_power_from_grid": total_power_from_grid,
        "total_power_to_grid": total_power_to_grid,
        "total_additional_revenue": total_additional_revenue,
        "total_saved_costs": total_saved_costs,
        "gain": gain

    }

    return results_over_time, results_values




