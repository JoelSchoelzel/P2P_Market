"""
Created on 10.06.2021

@author: jsc
"""
from pathlib import Path

import python.opti_methods as opti_methods
import python.parse_inputs as parse_inputs
import python.load_scenarios as scenarios
import python.load_net as net
import python.plots as plots
import python.calc_output as output
import pickle
import numpy as np
import pandas as pd
import datetime
# import run as DistrictGenerator
import json

# import data.time_data as time_data
from classes import Datahandler
from data import *


# from settings import *

def get_inputs(par_rh, options, districtData):  # gets inputs for optimization
    ### Load Params
    # load rolling horizon parameters
    par_rh = parse_inputs.compute_pars_rh(par_rh, options, districtData)

    # Read economic parameters and parameters for opti/gurobi
    params = parse_inputs.read_economics()

    # Load weather parameters
    # weather = pd.read_csv(options["path_file"] + "/raw_inputs/weather_potsdam.csv")  # DWD weather data for potsdam
    # nodes, solar_irr, weather = parse_inputs.get_solar_irr(options, weather, par_rh)

    # Read demands (elec, heat, dhw, ev) and pv generation
    nodes, building_params, options = parse_inputs.read_demands(options, districtData, par_rh)
    # Read devices, economic date and other parameters
    nodes, devs, building_params = parse_inputs.map_devices(options, nodes, building_params, par_rh, districtData)
    # nodes, building_params = parse_inputs.get_pv_power(nodes, options, building_params, devs, solar_irr, par_rh)
    # nodes, building_params = parse_inputs.get_pv_power_from_DG(nodes, options, building_params, districtData)

    # Read technical data of the network
    net_data = net.create_net(options)

    return nodes, building_params, params, devs, net_data, par_rh


def run_optimization(scenario_name, calcUserProfiles, crit_prio, block_length, enhanced_horizon, month):
    print("""
 _   _           _     ____  _                 _ 
| \ | | _____  _| |_  / ___|(_)_ __ ___  _   _| |
|  \| |/ _ \ \/ / __| \___ \| | '_ ` _ \| | | | |
| |\  |  __/>  <| |_   ___) | | | | | | | |_| | |
|_| \_|\___/_/\_\\__| |____/|_|_| |_| |_|\__,_|_|
""")
    print("Start optimization for scenario " + scenario_name + " with calcUserProfiles " + str(calcUserProfiles)
          + " with crit_prio " + crit_prio + ", block_length " + str(block_length)
          + ", enhanced_horizon " + str(enhanced_horizon) + " and month " + str(month) + ".")
    # Start time (time measurement)
    time = {}
    time["begin"] = datetime.datetime.now()
    print("This program begins at " + str(datetime.datetime.now()) + ".")

    # Set options for DistrictGenerator
    options_DG = {
        "scenario_name": scenario_name,  # name of csv input file, scenario3, Quartier_2
    }

    '''
    # Set options for DistrictGenerator
    options_DG = {
        "scenario_name" : "District_CP03_SFH60_MFH20_TH20_BZ3-4-3", # name of csv input file
        "randomProfile" : False,
        # clustering - True: perform time series clustering, False: use rolling horizon approach
        "clustering" : True,
        # calcUserProfiles - False: load user profiles from file (Tip: do if you need annual data!), True: new calculation
        "calcUserProfiles" : False,
        # saveUserProfiles - Only taken into account if calcUserProfile is True
        "saveUserProfiles" : False,
        # use5R1C - Use 5R1C model
        # False: Heating demand is a parameter
        # True: Indoor temperature and heating demand are variables to be calculated dynamically
        "use5R1C" : True,
        # bat2grid - True: battery can sell power, False: self-consumption only
        "bat2grid": False,
        # central - True: district balance, False: building balance
        "central" : True,
        # loadDistrict - True: take scenario pickle file as input instead of reading csv files
        "loadDistrict" : False,
        # saveDistrict - True: save scenario pickle file
        "saveDistrict" : False,
        "srcPath" : "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\districtgenerator_python",
        "filePath" : "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\districtgenerator_python\\data\\demands",
    }

    with open('C:/Users/Arbeit/Documents/WiHi_EBC/districtgenerator_python/settings/user_settings.json','w') as f:
        json.dump(options_DG,f)
    '''
    # create district with load (elec, heat, ..) and generation (pv, bz ..)  profiles as input for MAScity
    # districtData = DistrictGenerator.run_districtgenerator(options_DG)
    # print("Finished district generation (" + str(datetime.datetime.now()) + ").")

    # DistrictGenerator
    data = Datahandler()
    # Bei erstem Durchlauf calcUserProfiles=True setzen, danach calcUserProfiles=False
    data.generateDistrictComplete(options_DG["scenario_name"], calcUserProfiles=calcUserProfiles, saveUserProfiles=True)
    data.designDevicesComplete(saveGenerationProfiles=True)
    data.clusterProfiles()
    districtData = data

    # Set options for MAScity
    options = {"optimization": "P2P",  # P2P, P2P_typeWeeks
               "bid_strategy": "devices",  # zero for zero-intelligence, learning, devices
               "crit_prio": crit_prio,  # "flex_energy",
               # criteria to assign priority for trading: (mean_price, mean_quantity, flex_energy) for block, (price, alpha_el_flex, quantity...) for single
               "block_length": block_length,  # length of block bid in hours
               "negotiation": True,  # True: negotiation, False: auction
               "enhanced_horizon": enhanced_horizon,  # False: only block bid length, True: all 36hours
               "flex_price_delta": True,  # True: flex price delta, False: identical delta
               "descending": True,  # True: highest value of chosen has highest priority, False: lowest
               "multi_round": True,  # True: multiple trading rounds, False: single trading round
               "trading_rounds": 0,  # Number of trading rounds for multi round trading, 0 for unlimited
               "flexible_demands": False,  # True: flexible demands aren't necessarily fulfilled every step
               "number_typeWeeks": 0,  # set 0 in case no type weeks are investigated
               "full_path_scenario": (
                       "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/districtgenerator/data/scenarios/" +
                       options_DG["scenario_name"] + ".csv"),  # scenario csv, name set for DG is used
               # "times": 2688, #8760 * 4,  # whole year 15min resolution
               # "tweeks": 4,  # number of typical weeks
               "Dorfnetz": False,
               # grid type # todo: aktuell klappt nur Vorstadtnetz, da bei Dorfnetz noch 1 Gebäude fehlt
               "neighborhood": "district01",  # name of neighborhood
               # "pv_share": 0.5,  # 0.25, 0.5, 0.75, 1.0
               "ev_share": 0.0,  # 0.25, 0.5, 0.75, 1.0
               "ev_public": True,  # Skript für Opti von öffentlichen Ladestationen
               "grid": False,  # True -> consider grid constraints, False -> dont
               # "dt": 0.25,  # dt in h for rolling horizon
               "discretization_input_data": districtData.time['timeResolution'] / 3600,
               # in h - for: elec, dhw and heat
               "path_file": "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market",  # path to the project
               "path_results": "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results",
               # path to where the result should be stored
               "time_zone": districtData.site['timeZone'],  # ---,      time zone
               "location": districtData.site['location'],  # degree,   latitude, longitude of location
               "altitude": districtData.site['altitude'],  # m,        height of location above sea level
               }

    # Set rolling horizon options
    par_rh = {
        # Parameters for operational optimization
        "n_hours": 36,  # ----,      number of hours of prediction horizon for rolling horizon
        "n_hours_ov": 36 - options["block_length"],  # ----,      number of hours of overlap horizon for rolling horizon
        "n_opt_max": 8760,  # 8760  # -----,       maximum number of optimizations (one year)
        "month": month,  # -----,     optimize this month 1-12 (1: Jan, 2: Feb, ...), set to 0 to optimize entire year
        # set month to 0 for clustered input data
        # Parameters for rolling horizon with aggregated foresight
        "n_blocks": 2,  # ----, number of blocks with different resolution: minimum 2 (control and overlap horizon)
        # "resolution": [0.25, 1],  # h,    time resolution of each resolution block, insert list
        "resolution": [1, 1],  # h,    time resolution of each resolution block, insert list
        # [0.25, 1] resembles: control horizon with 15min, overlap horizon with 1h discretization
        "overlap_block_duration": [0, 0],
        # h, duration of overlap time blocks, insert 0 for default: half of overlap horizon
        "block_bid_length": options["block_length"]
    }
    # Get following inputs:
    nodes, building_params, params, devs_pre_opti, net_data, par_rh = get_inputs(par_rh, options, districtData)
    # pickledump
    with open(options["path_results"] + "/nodes_input_" + options_DG["scenario_name"] + ".p", 'wb') as file_nodes:
        pickle.dump(nodes, file_nodes)

    # Run (rolling horizon) optimization for whole year or month
    if options["optimization"] == "P2P":
        # run optimization incl. trading
        mar_dict, characteristics, init_val, res_time, res_val, opti_res = (
            opti_methods.rolling_horizon_opti(options=options, nodes=nodes, par_rh=par_rh,
                                              building_params=building_params,
                                              params=params, block_length=options["block_length"]))

        scenario_folder = scenario_name.replace("_", " ")
        month_folder = ""
        month_suffix = ""
        if month == 1:
            month_folder = "1_Jan"
            month_suffix = "_jan"
        elif month == 4:
            month_folder = "2_Apr"
            month_suffix = "_apr"
        elif month == 7:
            month_folder = "3_Jul"
            month_suffix = "_jul"
        block_length_folder = "nB=" + str(block_length)
        enhanced_folder = "nCH=36" if enhanced_horizon else "nCH=nB"
        crit_prio_folder = crit_prio

        # save results
        complete_path = (options["path_results"] + "/" + scenario_folder + "/" + month_folder + "/"
                         + block_length_folder + "/" + enhanced_folder + "/" + crit_prio_folder)

        Path(complete_path).mkdir(parents=True, exist_ok=True)

        with open(complete_path + "/mar_dict_P2P_" + options_DG["scenario_name"] + ".p", 'wb') as file_mar:
            pickle.dump(mar_dict, file_mar)

        with open(complete_path + "/par_rh_P2P_" + options_DG["scenario_name"] + ".p", 'wb') as file_par:
            pickle.dump(par_rh, file_par)

        with open(complete_path + "/init_val_P2P_" + options_DG["scenario_name"] + ".p", 'wb') as file_init:
            pickle.dump(par_rh, file_init)

        with open(complete_path + "/res_time_P2P_" + options_DG["scenario_name"] + month_suffix + ".p",
                  'wb') as file_res_list:
            pickle.dump(res_time, file_res_list)
        with open(complete_path + "/res_val_P2P_" + options_DG["scenario_name"] + month_suffix + ".p",
                  'wb') as file_res_val:
            pickle.dump(res_val, file_res_val)



    # Run (rolling horizon) optimization for type weeks
    elif options["optimization"] == "P2P_typeWeeks":
        opti_results, typeweeks_indices, mar_dict, trade_res = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                                 building_params,
                                                                                                 params)
        # Compute plots
        # criteria_typeweeks, criteria_year = output.compute_out_P2P_typeWeeks(options, options_DG, par_rh, opti_results,
        #                      districtData.weights, params, building_params, trade_res, mar_dict)

        # Save results
        with open(options["path_results"] + "/P2P_typeWeeks_opti_output/" + options_DG["scenario_name"] + ".p",
                  'wb') as fp:
            pickle.dump(opti_results, fp)

    # End time (Time measurement)
    time["end"] = datetime.datetime.now()
    print("Finished rolling horizon. " + str(datetime.datetime.now()))


if __name__ == '__main__':
    for scenario in ["Quartier_1"]:  # , "Quartier_2", "Quartier_3"]:
        first_run = False
        for month in [1]:  # , 7]:
            for block_length in [5]:  # , 3, 5]:
                for enhanced_horizon in [False]:  # , True]:
                    for crit_prio in ["mean_price"]:  #    # , "mean_quantity", "flex_energy"]:
                        run_optimization(scenario, calcUserProfiles=first_run, crit_prio=crit_prio,
                                         block_length=block_length,
                                         enhanced_horizon=enhanced_horizon, month=month)
                        first_run = False
