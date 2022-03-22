"""
Created on 10.06.2021

@author: jsc
"""
import python.opti_methods as opti_methods
import python.parse_inputs as parse_inputs
import python.load_scenarios as scenarios
import python.load_net as net

import numpy as np
import pandas as pd
import datetime

def get_inputs(par_rh, options, scenarios, scn):
    ### Load Params
    # load rolling horizon parameters
    par_rh = parse_inputs.compute_pars_rh(par_rh)

    # Read economic parameters and parameters for opti/gurobi
    params = parse_inputs.read_economics()

    # Load weather parameters
    weather = pd.read_csv(options["path_file"] + "/raw_inputs/weather_potsdam.csv")  # DWD weather data for potsdam
    nodes, solar_irr, weather = parse_inputs.get_solar_irr(options, weather)

    # Read demands (elec, heat, dhw, ev) and pv generation
    nodes, building_params, options = parse_inputs.read_demands(options, nodes)
    # Read devices, economic date and other parameters
    nodes, devs, building_params = parse_inputs.map_devices(options, nodes, building_params, weather, params, scenarios, scn)

    nodes, building_params = parse_inputs.get_pv_power(nodes, options, building_params, devs, solar_irr)

    # Read technichal datas of the network
    net_data = net.create_net(options)

    return nodes, building_params, params, devs, net_data, weather, par_rh



if __name__ == '__main__':
    # Start time (Time measurement)
    time = {}
    time["begin"] = datetime.datetime.now()
    print("This program begin at " + str(datetime.datetime.now()) + ".")

    # Set options
    options = {"optimization": "central",   # central or decentral
               "times": 8760, #* 4,  # whole year 15min resolution
               "tweeks": 4,  # number of typical weeks
               "Dorfnetz": False,  # todo: aktuell klappt nur Vorstadtnetz, da bei Dorfnetz noch 1 Gebäude fehlt
               "pv_share": 0.0,  # 0.25, 0.5, 0.75, 1.0
               "ev_share": 0.0,  # 0.25, 0.5, 0.75, 1.0
               "ev_public": True,  # Skript für Opti von öffentlichen Ladestationen
               "grid": False,  # True -> consider grid constraints, False -> dont
               "path_file": "C:/Users/jsc/Python/MAScity",
               "path_results": "C:/Users/jsc/Python/ref_models/dgoc_central/optimization/results"}

    # load heating devs per building
    scenarios = scenarios.get_scenarios(options)  # Stadtnetz: 195 scenarios
    scn = 194                                     # selected scenario

    # Set rolling horizon options
    par_rh = {
        # Parameters for operational optimization
        "n_hours": 36,  # ----,      number of hours of prediction horizon for rolling horizon
        "n_hours_ov": 35,  # ----,      number of hours of overlap horizon for rolling horizon
        "n_opt_max": 8760,  # -----,       maximum number of optimizations
        "month": 3,  # -----,     optimize this month 1-12 (1: Jan, 2: Feb, ...), set to 0 to optimize entire year

        # Parameters for rolling horizon with aggregated foresight
        "n_blocks": 2,    # ----, number of blocks with different resolution: minimum 2 (control horizon and overlap horizon)
        "resolution": [1, 1],  # h,    time resolution of each resolution block, insert list
        "overlap_block_duration": [0, 0],} # h, duration of overlap time blocks, insert 0 for default: half of overlap horizon

    # Get following inputs:
    nodes, building_params, params, devs, net_data, weather, par_rh = get_inputs(par_rh, options, scenarios, scn)

    # Run (rolling horizon) optimization
    if options["optimization"] == "central":
        central_opti = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)
    elif options["optimization"] == "decentral":
        decentral_opti = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

    # Compute plots

    # Safe results

    # End time (Time measurement)
    time["end"] = datetime.datetime.now()
    print("Finished rolling horizon.")
