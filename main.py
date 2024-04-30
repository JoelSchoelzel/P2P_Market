"""
Created on 10.06.2021

@author: jsc
"""
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


#import data.time_data as time_data
from classes import Datahandler
from data import *
#from settings import *

def get_inputs(par_rh, options, districtData):
    ### Load Params
    # load rolling horizon parameters
    par_rh = parse_inputs.compute_pars_rh(par_rh, options, districtData)

    # Read economic parameters and parameters for opti/gurobi
    params = parse_inputs.read_economics()

    # Load weather parameters
    #weather = pd.read_csv(options["path_file"] + "/raw_inputs/weather_potsdam.csv")  # DWD weather data for potsdam
    #nodes, solar_irr, weather = parse_inputs.get_solar_irr(options, weather, par_rh)

    # Read demands (elec, heat, dhw, ev) and pv generation
    nodes, building_params, options = parse_inputs.read_demands(options, districtData, par_rh)
    # Read devices, economic date and other parameters
    nodes, devs, building_params = parse_inputs.map_devices(options, nodes, building_params, par_rh, districtData)

    #nodes, building_params = parse_inputs.get_pv_power(nodes, options, building_params, devs, solar_irr, par_rh)
    #nodes, building_params = parse_inputs.get_pv_power_from_DG(nodes, options, building_params, districtData)


    # Read technical data of the network
    net_data = net.create_net(options)

    return nodes, building_params, params, devs, net_data, par_rh



if __name__ == '__main__':
    # Start time (time measurement)
    time = {}
    time["begin"] = datetime.datetime.now()
    print("This program begins at " + str(datetime.datetime.now()) + ".")

    # Set options for DistrictGenerator
    options_DG = {
        "scenario_name": "Quartier_3",  # name of csv input file
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
    data.generateDistrictComplete(options_DG["scenario_name"], calcUserProfiles=False, saveUserProfiles=True) #(calcUserProfiles=False, saveUserProfiles=True)
    data.designDevicesComplete(saveGenerationProfiles=True)
    data.clusterProfiles()

    districtData = data

    # Set options for MAScity
    options = {"optimization": "P2P",   # P2P, P2P_typeWeeks, central, central_typeWeeks, decentral or decentral_typeWeeks
               "bid_strategy": "zero",  # zero for zero-intelligence
               "crit_prio": "alpha_el_flex_delayed", # criteria to assign priority for trading: price, alpha_el_flex_delayed
               "descending": True, # True: highest value of chosen has highest priority, False: lowest

               "number_typeWeeks": 0, # set 0 in case no type weeks are investigated
               #"full_path_scenario": "C:\\Users\\miche\\districtgenerator_python\\data\\scenarios\\scenario4.csv", # scenario csv
               "full_path_scenario": ("C:/Users/cemca/PycharmProjects/MA/districtgenerator/data/scenarios/" + options_DG["scenario_name"] + ".csv"), # scenario csv, name set for DG is used
               # "times": 2688, #8760 * 4,  # whole year 15min resolution
               # "tweeks": 4,  # number of typical weeks
               "Dorfnetz": False,  # grid type # todo: aktuell klappt nur Vorstadtnetz, da bei Dorfnetz noch 1 Gebäude fehlt
               "neighborhood": "district01",     # name of neighborhood
               #"pv_share": 0.5,  # 0.25, 0.5, 0.75, 1.0
               "ev_share": 0.0,  # 0.25, 0.5, 0.75, 1.0
               "ev_public": True,  # Skript für Opti von öffentlichen Ladestationen
               "grid": False,  # True -> consider grid constraints, False -> dont
               # "dt": 0.25,  # dt in h for rolling horizon
               "discretization_input_data": districtData.time['timeResolution']/3600,  # in h - for: elec, dhw and heat
               "path_file": "C:/Users/cemca/PycharmProjects/MA/P2P_Market", #"C:/Users/Arbeit/Documents/WiHi_EBC/MAScity/MAScity",
               "path_results":"C:/Users/cemca/PycharmProjects/MA/P2P_Market/results", #"C:/Users/Arbeit/Documents/WiHi_EBC/MAScity/results",
               "time_zone": districtData.site['timeZone'],  # ---,      time zone
               "location": districtData.site['location'], # degree,   latitude, longitude of location
               "altitude": districtData.site['altitude'], # m,        height of location above sea level
               "stackelberg": True,  # True: Stackelberg game, False: k-pricing
              }

    # load heating devs per building
    #scenarios = scenarios.get_scenarios(options)  # Stadtnetz: 195 scenarios
    #scn = 0                                     # selected scenario

    # Set rolling horizon options
    par_rh = {
        # Parameters for operational optimization
        "n_hours": 36, # ----,      number of hours of prediction horizon for rolling horizon
        "n_hours_ov": 35, # ----,      number of hours of overlap horizon for rolling horizon
        "n_opt_max": 8760 , #8760  # -----,       maximum number of optimizations
        "month": 1,  # -----,     optimize this month 1-12 (1: Jan, 2: Feb, ...), set to 0 to optimize entire year
        # set month to 0 for clustered input data

        # Parameters for rolling horizon with aggregated foresight
        "n_blocks": 2,    # ----, number of blocks with different resolution: minimum 2 (control horizon and overlap horizon)
        #"resolution": [0.25, 1],  # h,    time resolution of each resolution block, insert list
        "resolution": [1, 1],  # h,    time resolution of each resolution block, insert list
        # [0.25, 1] resembles: control horizon with 15min, overlap horizon with 1h discretization
        "overlap_block_duration": [0, 0],} # h, duration of overlap time blocks, insert 0 for default: half of overlap horizon

    # Get following inputs:
    nodes, building_params, params, devs_pre_opti, net_data, par_rh = get_inputs(par_rh, options, districtData)


    '''
    ### Master version:
    # Run (rolling horizon) optimization
    if options["optimization"] == "central_typeWeeks":
        central_opti_results, typeweeks_indices = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

        # Compute plots
        criteria_typeweeks, criteria_year = output.compute_out(options, options_DG, par_rh, central_opti_results,
                                                               districtData.weights, params, building_params)

        # Safe results
        with open(options["path_results"] + "/central_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
            pickle.dump(central_opti_results, fp)

    if options["optimization"] == "decentral_typeWeeks":
        decentral_opti_results, typeweeks_indices = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

        # Compute plots
        criteria_typeweeks, criteria_year = output.compute_out_decentral(options, options_DG, par_rh, decentral_opti_results,
                                                               districtData.weights, params, building_params)

        # Safe results
        with open(options["path_results"] + "/decentral_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
            pickle.dump(decentral_opti_results, fp)

    elif options["optimization"] == "central":
        central_opti_results = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

    elif options["optimization"] == "decentral": # neither adapted to 15min input data nor to clustered data yet
        decentral_opti = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

    elif options["optimization"] == "P2P":
        opti_results, mar_dict, trade_res, characteristics = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                                building_params, params)


        # Compute plots
        criteria = output.compute_out_P2P(options, options_DG, par_rh, opti_results, params, building_params,
                                               trade_res, mar_dict)

        # Safe results
        with open(options["path_results"] + "/P2P_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
            pickle.dump(opti_results, fp)
        with open(options["path_results"] + "/P2P_characteristics/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
            pickle.dump(characteristics, fp)
        with open(options["path_results"] + "/P2P_mar_dict/" + options_DG["scenario_name"] + "_" + options["crit_prio"] + ".p", 'wb') as fp:
            pickle.dump(mar_dict, fp)

    elif options["optimization"] == "P2P_typeWeeks":
        opti_results, typeweeks_indices, mar_dict, trade_res = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                                building_params, params)

        # Compute plots
        criteria_typeweeks, criteria_year = output.compute_out_P2P_typeWeeks(options, options_DG, par_rh, opti_results,
                                                    districtData.weights, params, building_params, trade_res, mar_dict)


        # Safe results
        with open(options["path_results"] + "/P2P_typeWeeks_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
            pickle.dump(opti_results, fp)

    # Compute plots
    #criteria_typeweeks, criteria_year = output.compute_out(options, options_DG, par_rh, central_opti_results, districtData.weights, params, building_params)

    # Safe results
    #with open(options["path_results"] + "/central_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
    #    pickle.dump(central_opti_results, fp)

    '''

    #Newly added from dev_Michel
    # Run (rolling horizon) optimization for whole year or month
    if options["optimization"] == "P2P":
        # run optimization incl. trading
        mar_dict, characteristics, opti_results = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                    building_params, params)

        # opti_results, mar_dict, trade_res, characteristics = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

        print('Opti results:', opti_results)
        print('Mar dict:', mar_dict)
        # print('Trade res:', trade_res)
        # print('Characteristics:', characteristics)

        # Compute plots
        # criteria = output.compute_out_P2P(options, options_DG, par_rh, opti_results, params, building_params, trade_res,
        #                                   mar_dict)
        #
        # try:
        #     # Save results
        #     with open(options["path_results"] + "/P2P_opti_output/" + options_DG["scenario_name"] + ".p", 'wb') as fp:
        #         pickle.dump(opti_results, fp)
        #     with open(options["path_results"] + "/P2P_characteristics/" + options_DG["scenario_name"] + ".p",
        #               'wb') as fp:
        #         pickle.dump(characteristics, fp)
        #     with open(options["path_results"] + "/P2P_mar_dict/" + options_DG["scenario_name"] + "_" +
        #               options["crit_prio"] + ".p", 'wb') as fp:
        #         pickle.dump(mar_dict, fp)
        #
        # except Exception as e:
        #     print("Error while trying to save:", str(e))

    # Run (rolling horizon) optimization for type weeks
    elif options["optimization"] == "P2P_typeWeeks":
        opti_results, typeweeks_indices, mar_dict, trade_res = opti_methods.rolling_horizon_opti(options, nodes, par_rh,
                                                                                                 building_params,
                                                                                                 params)

        # Compute plots
        criteria_typeweeks, criteria_year = output.compute_out_P2P_typeWeeks(options, options_DG, par_rh, opti_results,
                                                                             districtData.weights, params,
                                                                             building_params, trade_res, mar_dict)

        # Save results
        with open(options["path_results"] + "/P2P_typeWeeks_opti_output/" + options_DG["scenario_name"] + ".p",
                  'wb') as fp:
            pickle.dump(opti_results, fp)

    # Run (rolling horizon) optimization for decentral approach
    elif options["optimization"] == "decentral":  # neither adapted to 15min input data nor to clustered data yet
        decentral_opti = opti_methods.rolling_horizon_opti(options, nodes, par_rh, building_params, params)

    # End time (Time measurement)
    time["end"] = datetime.datetime.now()
    print("Finished rolling horizon. " + str(datetime.datetime.now()))
