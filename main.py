"""
Created on 10.06.2021

@author: jsc
"""
from pathlib import Path

#import python.opti_methods as opti_methods
import python.opti_methods_BlockBids as opti_methods
import python.parse_inputs as parse_inputs
import pickle
import os
import datetime

import sys
# Define the path to the 'classes' directory
#classes_path = os.path.join('C:', 'Users', 'jsc', 'Python', 'districtgenerator', 'classes')
classes_path = 'C:/Users/jsc-tma/Masterarbeit_tma/Optimierung/districtgenerator'
sys.path.append(classes_path)

# Append the absolute path to sys.path
#sys.path.append(os.path.abspath(classes_path))

import classes

# import DistrictGenerator
# from classes import Datahandler
from classes import *

def get_inputs(par_rh, options, districtData, scenario_name):  # gets inputs for optimization
    ### Load Params
    # load rolling horizon parameters
    par_rh = parse_inputs.compute_pars_rh(par_rh, options, districtData)

    # Read economic parameters and parameters for opti/gurobi
    params = parse_inputs.read_economics()

    # Read demands (elec, heat, dhw, ev) and pv generation
    nodes, building_params, options = parse_inputs.read_demands(options, districtData, par_rh)

    # Read devices, economic date and other parameters
    nodes, devs, building_params = parse_inputs.map_devices(options, nodes, building_params, par_rh, districtData)

    # Read technical data of the network
    # TODO: create a pandapower network and extracts node and line information
    #net_data = net.create_net(options)

    if not options["WithElecDem"]:
        for n in nodes:
            for t in range(8760):
                nodes[n]["elec"][t] = 0
    
    if scenario_name == "old/Medium_District_12houses_BOI+HP+CHP":
        for n in nodes:
            if nodes[n]["devs"]["chp"]["cap"] != 0:
                nodes[n]["devs"]["chp"]["cap"] = 25610
                #nodes[n]["devs"]["chp"]["cap"] = 46000
                #nodes[n]["devs"]["chp"]["mod_lvl"] = 0.3






    return nodes, building_params, params, devs, par_rh


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

    # DistrictGenerator -> create district with load and generation profiles
    data = Datahandler()
    # Bei erstem Durchlauf calcUserProfiles=True setzen, danach calcUserProfiles=False
    data.generateDistrictComplete(options_DG["scenario_name"], calcUserProfiles=False, saveUserProfiles=False)
    data.designDecentralDevices(saveGenerationProfiles=False)
    data.clusterProfiles(centralEnergySupply = False)
    districtData = data


    # Set options for energy trading
    options = {"optimization": "P2P",  # P2P, P2P_typeWeeks
               "mpc": True, #True: use of model predictive control with simulation, False: sole optimizatio negotiation
               "WithElecDem": False, #True: electric demands for buildings are considered 
               "bid_strategy": "zero",  # zero for zero-intelligence, learning, devices
               "crit_prio": crit_prio,  # "flex_energy",
               # criteria to assign priority for trading: (mean_price, mean_quantity, flex_energy) for block, (price, alpha_el_flex, quantity...) for single
               "block_length": block_length,  # length of block bid in hours
               "max_trading_rounds": 15,
                "negotiation": True,  # True: negotiation, False: auction
               "enhanced_horizon": enhanced_horizon,  # False: only block bid length, True: all 36hours
               "flex_price_delta": True,  # True: flex price delta, False: identical delta
               "descending": True,  # True: highest value of chosen has highest priority, False: lowest
               "multi_round": True,  # True: multiple trading rounds, False: single trading round
               "trading_rounds": 0,  # Number of trading rounds for multi round trading, 0 for unlimited
               "flexible_demands": False,  # True: flexible demands aren't necessarily fulfilled every step
               "number_typeWeeks": 0,  # set 0 in case no type weeks are investigated

               "grid": False,  # True -> consider grid constraints, False -> dont
               "discretization_input_data": districtData.time['timeResolution'] / 3600, # in h - for: elec, dhw and heat
               # path to the project
               "path_file": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
               # path to where the result should be stored
               "path_results": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"),
               "full_path_scenario": (
                       "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/districtgenerator/data/scenarios/" +
                       options_DG["scenario_name"] + ".csv"),  # scenario csv, name set for DG is used

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
    nodes, building_params, params, devs_pre_opti, par_rh = get_inputs(par_rh, options, districtData, scenario_name)
    # pickledump
    #with open(options["path_results"] + "/nodes_input_" + options_DG["scenario_name"] + ".p", 'wb') as file_nodes:
        #pickle.dump(nodes, file_nodes)

    # Run (rolling horizon) optimization for whole year or month
    if options["optimization"] == "P2P":
        # run optimization incl. trading
        mar_dict, characteristics, init_val, results, opti_res, opti_res_check = (
            opti_methods.rolling_horizon_opti(options=options, nodes=nodes, par_rh=par_rh,
                                              building_params=building_params,
                                              params=params, block_length=options["block_length"], scenario_name=scenario_name))

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
        elif month == 12:
            month_folder = "Dec"
            month_suffix = "_dec"
        elif month == 0:
            month_folder = "Year_r_" + str(options["max_trading_rounds"])
            month_suffix = "_year_r_" + str(options["max_trading_rounds"])
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

        with open(complete_path + "/results_P2P_" + options_DG["scenario_name"] + month_suffix + ".p",
                  'wb') as file_res_list:
            pickle.dump(results, file_res_list)

        #with open("C:/Users/jsc/Python/Results/AppliedEnergy/Year_r_1/nB=1/nCH=nB/random/opti_res.p",
        #          'wb') as file_res_list:
        #    pickle.dump(opti_res, file_res_list)


    # Run (rolling horizon) optimization for type weeks
    elif options["optimization"] == "P2P_typeWeeks":
        opti_results, typeweeks_indices, mar_dict, trade_res = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                                 building_params,
                                                                                                 params, scenario_name)
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

    return mar_dict, characteristics, init_val, results, opti_res, opti_res_check, par_rh, districtData, options

if __name__ == '__main__':
    #for scenario_name in ["old/Small_District_BOI+HP"]:  # Typquartier_1, "Quartier_2", "Quartier_3"]:
    for scenario_name in ["old/Medium_District_12houses_BOI+HP+CHP"]:
        first_run = True
        for month in [3]:  # , 7]:
            for block_length in [3]:  #1, 3, 5]:
                for enhanced_horizon in [False]: #, True]:
                    for crit_prio in ["quantity"]: #"flex_energy", "quantity", "random", "flex_quantity"
                        mar_dict, characteristics, init_val, results, opti_res, opti_res_check, par_rh, districtData, options = \
                            run_optimization(scenario_name, calcUserProfiles=first_run, crit_prio=crit_prio,
                                         block_length=block_length,
                                         enhanced_horizon=enhanced_horizon, month=month)
                        first_run = False