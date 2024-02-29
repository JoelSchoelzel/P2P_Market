#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 18:42:33 2015

@author: Thomas
"""
from __future__ import division

import xlrd
import numpy as np
import scipy.stats as stats
import pandas as pd
import copy
import pickle

import python.pv_buildings as pv
import python.ev_param as ev_param
import python.solar as solar

def read_economics():
    """
    Read in economic parameters and update residual values of devices.
    
    Returns
    -------
    eco : dictionary
        Information on economic parameters.
    par : dictionary
        All non-economic and non-technical parameters.
    """

    params = {}
    params["eco"] = {}
    params["phy"] = {}
    params["gp"] = {}
    
#    kWh2J = 3600 * 1000 # Factor from kWh to Joule
    
    # Economics
    params["eco"]["t_calc"] = 10   # [a] observation period
    params["eco"]["tax"]    = 1.19 # German value added tax
    params["eco"]["rate"]   = 0.05 # Interest rate
    params["eco"]["q"]      = 1 + params["eco"]["rate"]
    params["eco"]["crf"]    = ((params["eco"]["q"] ** params["eco"]["t_calc"] * params["eco"]["rate"]) /
                     (params["eco"]["q"] ** params["eco"]["t_calc"] - 1))
    
    params["eco"]["prChange"] = {}  # Price change factors per year
    params["eco"]["prChange"]["el"]   = 1.057    # for electricity
    params["eco"]["prChange"]["gas"]  = 1.041    # for natural gas
    params["eco"]["prChange"]["eex"]  = 1.0252   # for EEX compensation
    params["eco"]["prChange"]["infl"] = 1.017    # for inflation

    pC = params["eco"]["prChange"]
    params["eco"]["b"] = {key: ((1 - (pC[key] / params["eco"]["q"]) ** params["eco"]["t_calc"]) /
                      (params["eco"]["q"] - pC[key]))
                for key in pC.keys()}
    
    # Always EUR per kWh (meter per anno)
    params["eco"]["sell_pv"]    = 0.081 # €/kWh valid for pv systems with < 10 kWp 0.082
    params["eco"]["sell_chp"] = 0.191 # €/kWh (average Q4 2021 - Q2 2022 + avoided costs for grid usage)
    params["eco"]["co2_gas"] = 0.411 # kg/kWh (Germany, 2019; https://de.statista.com/statistik/daten/studie/38897/umfrage/co2-emissionsfaktor-fuer-den-strommix-in-deutschland-seit-1990/)
    params["eco"]["co2_el"] = 0.241 # kg/kWh (https://www.umweltbundesamt.de/publikationen/emissionsbilanz-erneuerbarer-energietraeger-2020)
    params["eco"]["co2_pv"] = 0.056 # kg/kWh (https://www.umweltbundesamt.de/publikationen/emissionsbilanz-erneuerbarer-energietraeger-2020)

    # calculate costs with prices of Q3+Q4 2021
    params["eco"]["pr",   "el"]     = 0.4627 # 0.3287 €/kWh, Q3+Q4 2021 (https://www-genesis.destatis.de/genesis/online?operation=previous&levelindex=1&step=1&titel=Ergebnis&levelid=1663949631295&acceptscookies=false#abreadcrumb)
    params["eco"]["gas"]     = 0.0683   # €/kWh, Q3+Q4 2021 (https://www-genesis.destatis.de/genesis/online?sequenz=tabelleErgebnis&selectionname=61243-0010&language=de#abreadcrumb)

    # calculate costs with raised el/gas prices of Q3 2022
    #params["eco"]["pr",   "el"] = 0.4403 # Verivox Q3 2022 (https://www.verivox.de/strom/verbraucherpreisindex/)
    #params["eco"]["gas"] = 0.1853 # Verivox Q3 2022 (https://www.verivox.de/gas/verbraucherpreisindex/)

    params["phy"]["rho_w"]           = 1000 # [kg/m^3]
    params["phy"]["c_w"]             = 4180 # [J/(kg*K)]
    params["phy"]["beta"]            = 0.2
    params["phy"]["A_max"]           = 40   # Maximum available roof area
    
    # Further parameters
    params["gp"]["mip_gap"]         = 0.01 # https://www.gurobi.com/documentation/9.1/refman/mipgap2.html
    params["gp"]["time_limit"]      = 100 # [s]  https://www.gurobi.com/documentation/9.1/refman/timelimit.html
    params["gp"]["numeric_focus"]   = 3   # https://www.gurobi.com/documentation/9.1/refman/numericfocus.html


    return params

def compute_pars_rh(param, options, districtData): # computes parameters for rolling horizon optimization

    # Months and starting hours of months
    param["month_start"] = {}
    param["month_start"][1] = 0
    param["month_start"][2] = 744
    param["month_start"][3] = 1416
    param["month_start"][4] = 2160
    param["month_start"][5] = 2880
    param["month_start"][6] = 3624
    param["month_start"][7] = 4344
    param["month_start"][8] = 5088
    param["month_start"][9] = 5832
    param["month_start"][10] = 6552
    param["month_start"][11] = 7296
    param["month_start"][12] = 8016
    param["month_start"][13] = 8760    # begin of next year

    # %% ROLLING HORIZON SET UP: Time steps, etc.

    param["operational_optim"] = 1
    if param["operational_optim"]:

        # Example to explain set up:    n_hours: 48
        #                               n_hours_ov: 36
        #                           --> n_hours_ch: 12
        #                               n_blocks: 2
        #                               resolution: [1,6]

        # Calculate duration of each time block
        param["org_block_duration"] = {}  # original block duration (for example: [12,36])
        param["block_duration"] = {}  # block duration with another resolution (for example: [12/1,36/6]=[12,6])

        # First block (block 0): control horizon (detailed time series)
        param["org_block_duration"][0] = param["n_hours"] - param["n_hours_ov"]
        param["n_hours_ch"] = param["org_block_duration"][0]
        param["block_duration"][0] = int(param["org_block_duration"][0] / param["resolution"][0])

        # Remaining blocks: overlap horizon (aggregated time series)
        # Default duration of overlap block: total duration of overlap horizon equally split up to number of blocks (only if division yields integer)
        if sum(param["overlap_block_duration"][i] for i in range(param["n_blocks"])) == 0:
            # take default
            for b in range(1, param["n_blocks"]):
                param["org_block_duration"][b] = int(np.floor(param["n_hours_ov"] / (param["n_blocks"] - 1)))
                param["block_duration"][b] = int(param["org_block_duration"][b] / param["resolution"][b])
        else:
            # take durations specified above
            for b in range(1, param["n_blocks"]):
                param["org_block_duration"][b] = int(param["overlap_block_duration"][b])

        # Set up time steps

        # optimize any period of length n_opt_max*n_hours_ch or entire year starting at hour 0
        if param["month"] == 0: # optimize entire year

            # Calculate number of operational optimizations
            if options["number_typeWeeks"] > 0:
                param["n_opt_total"] = int(np.ceil(districtData.time["clusterLength"] / 3600 / param["n_hours_ch"])) #districtData.time["clusterHorizon"]
            else:
                param["n_opt_total"] = int(np.ceil(8760 / param["n_hours_ch"]))

            # Number of optimizations: Take minimum out of maximum optimizations or total optimizations needed to cover entire year
            param["n_opt"] = min(param["n_opt_total"], param["n_opt_max"])

            # Set up starting hour of each optimization
            param["hour_start"] = {}  # starting hour of each optimization
            for i in range(param["n_opt"]):
                # Starting hour of each optimization
                param["hour_start"][i] = i * param["n_hours_ch"]

        else:  # optimize only selected month (param["month"] specifies number of selected month)

            # Calculate total number of hours within chosen month
            hours_month = param["month_start"][param["month"] + 1] - param["month_start"][param["month"]]

            # Calculate number of optimizations
            #param["n_opt"] = int(np.ceil(hours_month / param["n_hours_ch"]))
            param["n_opt"] = min(int(np.ceil(hours_month / param["n_hours_ch"])), param["n_opt_max"])

            # Set up starting hour of each optimization
            param["hour_start"] = {}  # starting hour of each optimization
            for i in range(param["n_opt"]):
                # Starting hour of each optimization
                param["hour_start"][i] = param["month_start"][param["month"]] + i * param["n_hours_ch"]

        param["end_time_org"] = param["n_opt"] * param["n_hours_ch"] # relevant for soc_end = soc_init

                # Set up optimization time steps (incl. aggregated foresight time steps)
        param["time_steps"] = {}  # time steps for optimization incl. aggregation, for 1st optimization for example above:
        # [0,1,2,3,4,5,6,7,8,9,10,11, 12,13,14,15,16,17]
        param["org_time_steps"] = {}  # original time steps for optimizations, for 1st optimization for example above:
        # [0,1,2,3,4,5,6,7,8,9,10,11, 12,18,24,30,36,42]
        param["duration"] = {}  # indicates duration of each time step

        # Set up time steps for each optimization
        for i in range(param["n_opt"]):

            param["time_steps"][i] = []
            param["duration"][i] = {}

            # for each block, set up time steps
            # only time steps where the original corresponding time steps are still within 8760 hours are set up
            count = param["hour_start"][i]  # corresponding original time step
            step = param["hour_start"][i]  # number of time step
            for b in range(param["n_blocks"]):
                for t in range(param["block_duration"][b]):
                    h_end = count + param["resolution"][b]  # ending hour of original time step
                    if h_end < 8760:  # only if ending hour of original time step smaller than 8760
                        param["time_steps"][i].append(step)  # append optimization time step
                        param["duration"][i][step] = param["resolution"][
                            b]  # duration of optimization time step is resolution of respective block
                    else:  # if ending hour of original time step is >= 8760
                        rest = param["resolution"][b] - (
                                    h_end - 8760)  # remaining original time steps still lying within the year
                        if rest > 0:  # are remaining time steps existing?
                            param["time_steps"][i].append(step)  # append optimization time step
                            param["duration"][i][
                                step] = rest  # duration of optimization time step is number of remaining time steps
                    count = h_end  # set ending hour of one time step as starting hour of next one
                    step = step + 1  # next optimization time step

        # Set up original time steps (for each optimization time step, corresponding starting hour of original time step)
        for i in range(param["n_opt"]):
            param["org_time_steps"][i] = []
            param["org_time_steps"][i].append(param["time_steps"][i][0])  # first original time step
            count = 0

            # add original time steps for each optimization time step using starting hour and duration of previous time step
            for t in range(param["time_steps"][i][0], param["time_steps"][i][-1]):
                #if count > 0:
                    param["org_time_steps"][i].append(param["org_time_steps"][i][-1] + param["duration"][i][t])


    # adjust the following values
        param["datapoints"] = int(8760/options["discretization_input_data"])

       # if param["month"] == 0:
       #     param["start_time"] = param["month_start"][1]
       #     param["end_time"] = param["month_start"][13]
            # param["obs_period"] = 365  # Observation period in days
       # else:
       #     param["start_time"] = param["month_start"][param["month"]]
       #     param["end_time"] = param["month_start"][param["month"] + 1]
            # param["obs_period"] = int((param["end_time"] - param["start_time"]) / 24)


    #param["start_time"] = param["month_start"][input_rh["month"]]
    #param["end_time"] = param["month_start"][input_rh["month"] + 1]
    #if input_rh["month"] == 0:
    #    param["month_start"][0] = 0
    #    param["obs_period"] = 365  # Observation period in days
    #    param["times"] = param["obs_period"] * 24
    #else:
    #    param["obs_period"] = int((param["end_time"] - param["start_time"]) / 24)
    #    param["times"] = param["obs_period"]  * 24 + input_rh["n_hours_ov"]

    return param

def aggregate_foresight(nodes, param, n_opt):
    """
    Aggregates time series for RH approach with aggregated foresight.

    input: nodes, param, index of optimization n_opt
    output: nodes, param (modified)

    """
    # Save original time series in copy
    org_nodes = copy.deepcopy(nodes)
    org_param = copy.deepcopy(param)

    # time steps (number of time steps already contains aggregation)
    # e.g. [0,1,2,3,4,5] correspond to original time steps [0,   1,   2,   3,4,5,   6,7,8,   9,10,11]
    # time step 3 corresponds to original time steps 3,4,5; time step 4 to 6,7,8, etc.
    time_steps = param["time_steps"][n_opt]
    # duration of time steps
    # e.g. [1,1,1,3,3,3] for example above
    duration = param["duration"][n_opt]

    # Weather data & other time series
    for series in ["T_air", "T_soil", "G_sol", "G_dif", "price_el", "revenue_feed_in_CHP", "revenue_feed_in_PV",
                   "T_soil_deep", "power_pumps", "ext_power_dem"]:
        # Set up count to keep track of which time steps of original time series are aggregated
        # e.g. for time step 4 of example above, corresponding count would be 6, etc.
        count = time_steps[0]
        # Aggregation, for each aggregated time step
        for t in time_steps:
            h_start = count
            h_end = count + duration[t]
            if duration[t] >= 1:  # calculate average values if duration of time step is longer or equal than 1h
                h_start = int(h_start)
                h_end = int(h_end)
                if h_end > 8760:
                    h_end = 8760
                avg = sum(org_param[series][s] for s in range(h_start, h_end)) / duration[t]
            else:  # if duration is less than 1h, take original hourly value (only within control horizon)
                avg = org_param[series][int(np.floor(count))]
            count = h_end

            # set value of time series to this average
            param[series][t] = avg

    # Nodal heat data and supply temperatures, analog
    for n in nodes:
        for dat in ["heat", "cool", "T_heating_supply", "T_heating_return", "T_cooling_supply", "T_cooling_return"]:
            count = time_steps[0]
        for t in time_steps:
            h_start = count
            h_end = int(count + duration[t])
            if duration[t] >= 1:  # calculate average values if duration of time step is longer or equal than 1h
                h_start = int(h_start)
                h_end = int(h_end)
                if h_end > 8760:
                    h_end = 8760
                avg = sum(org_nodes[n][dat][s] for s in range(h_start, h_end)) / duration[t]
            else:  # if duration is less than 1h, take original hourly value (only within control horizon)
                avg = org_nodes[n][dat][int(np.floor(count))]
            count = h_end

            # set value of time series to calculated average
            nodes[n][dat][t] = avg

    return nodes, param

def read_demands(options, districtData,par_rh): # rea
        
    # Define path for use case input data
    #path_file = options["path_file"]
    #path_input = path_file + "/raw_inputs/demands_" + options["neighborhood"] + "/"
    #path_nodes = path_input + name_nodefile
    #path_demands = path_input + "demands\\"

    #datapoints = options["times"]
    #time_hor = options["time_hor"]
    #tweeks = options["tweeks"]


    # todo: in options wird ein Netz ausgewählt, damit werden Netz- (Grenzen des ONS, Stränge, etc.) und Gebäudeinformationen gebündelt eingelesen --> z.B. number_bes
    # Possible selection of typical grids
    #if options["Dorfnetz"]:
        #grid = "dorfnetz"
    #else:
        #grid = "vorstadtnetz"

    # Building parameters
    #building_params = pd.read_csv(path_input + "buildings_" + options["neighborhood"] + ".csv",delimiter=";")

    options["nb_bes"] = districtData.district.__len__() # number of building energy systems
    #datapoints = par_rh["datapoints"]


    # Get heatloads of building categories
    #heatloads = {}
   # for cat in range(1,7):
   #     heatloads[cat] = np.loadtxt(
   #         open(path_input + "cat_" + str(cat) + ".csv","rb"), delimiter=";", skiprows=1) / 1000  # kW, heat demand

    #building_list = ["EFH_1860_adv", "EFH_1860_retr", "EFH_1861_1918_adv", "EFH_1861_1918_retr", "EFH_1919_1948_adv",
    #                 "EFH_1919_1948_def",
    #                 "EFH_1919_1948_retr", "EFH_1949_1957_adv", "EFH_1949_1957_def", "EFH_1949_1957_retr",
    #                 "EFH_1949_1957_adv",
    #                 "EFH_1958_1968_adv", "EFH_1958_1968_retr", "EFH_1958_1968_def", "EFH_1969_1978_adv",
    #                 "EFH_1969_1978_retr",
    #                 "EFH_1969_1978_def", "EFH_1979_1983_adv", "EFH_1979_1983_retr", "EFH_1979_1983_def",
    #                 "EFH_1984_1994_adv",
    #                 "EFH_1984_1994_retr", "EFH_1984_1994_def", "EFH_1995_2001_adv", "EFH_1995_2001_def",
    #                 "EFH_2002_2009_adv",
    #                 "EFH_2002_2009_def", "EFH_2010_2019_def",
    #                 "MFH_1860_adv", "MFH_1860_def", "MFH_1861_1918_adv", "MFH_1861_1918_retr", "MFH_1919_1948_adv",
    #                 "MFH_1919_1948_def",
    #                 "MFH_1919_1948_retr", "MFH_1949_1957_adv", "MFH_1949_1957_def", "MFH_1949_1957_retr",
    #                 "MFH_1949_1957_adv",
    #                 "MFH_1958_1968_adv", "MFH_1958_1968_retr", "MFH_1958_1968_def", "MFH_1969_1978_adv",
    #                 "MFH_1969_1978_retr", "MFH_1969_1978_def", "MFH_1979_1983_adv", "MFH_1979_1983_retr",
    #                 "MFH_1979_1983_def", "MFH_1984_1994_adv", "MFH_1984_1994_retr", "MFH_1984_1994_def",
    #                 "MFH_1995_2001_adv", "MFH_1995_2001_def", "MFH_2002_2009_adv", "MFH_2002_2009_def",
    #                 "MFH_2010_2019_def"
    #                 ]

    #for cat in building_list:
    #    heatloads[cat] = np.loadtxt(
    #        open(path_input + "/" + str(cat) + ".csv","rb"), delimiter=";", skiprows=1) / 1000  # kW, heat demand

    # Fill nodes dictionairy with demands (electricity, drinking hot water, heat load)
    #demands = {}
    #for i in range(options["nb_bes"]):
    #    demands[i] = {
    #        "elec": np.loadtxt(
    #            open(path_input + "/elec_" + str(i) + ".csv", "rb"),
    #            delimiter=",", skiprows=1, usecols=1) / 1000,  # kW, electricity demand
    #        "dhw": np.loadtxt(
    #            open(path_input + "/dhw_" + str(i) + ".csv","rb"),
    #            skiprows=1) / 1000,  # kW, domestic hot water demand
    #    }

       # for cat in range(1,7):
       #     if cat == building_params["cat"][i]:
       #         demands[i]["heat"] = heatloads[cat][:,1]
       #     else:
       #         pass

     #   for cat in building_list:
     #    if cat == building_params["type"][i]:
     #       demands[i]["heat"] = heatloads[cat]
     #    else:
     #       pass

    # Electric Vehicles # todo: read EV data from district generator
    ev_share = options["ev_share"]
    ev_data = ev_param.ev_load(options, options["nb_bes"])
    ev_exists = ev_param.ev_share(ev_share, options["nb_bes"])

    building_params = {}
    nodes = {}

    if options["number_typeWeeks"] == 0: # input data not clustered
        pv_exists = np.zeros(shape=(options["nb_bes"], 1))
        for n in range(options["nb_bes"]):
            nodes[n] = {
                "elec": districtData.district[n]['user'].elec,
                "heat": districtData.district[n]['user'].heat,
                "dhw": districtData.district[n]['user'].dhw,
                "T_air": districtData.site['T_e'],
                "type": districtData.district[n]['user'].building,
                "ev_avail": ev_exists[n] * ev_data["avail"][:, n],
                "ev_dem_arrive": ev_exists[n] * ev_data["dem_arrive"][:, n],
                "ev_dem_leave": ev_exists[n] * ev_data["dem_leave"][:, n],
                "pv_power": districtData.district[n]['generationPV'],
                "devs": {}
            }
            nodes[n]["devs"]["COP_sh35"] = np.zeros(len(nodes[0]["T_air"]))
            nodes[n]["devs"]["COP_sh55"] = np.zeros(len(nodes[0]["T_air"]))
            pv_exists[n] = districtData.scenario.PV[n]

            # Check small demand values
            for t in range(len(nodes[0]["heat"])):
                if nodes[n]["heat"][t] < 0.01:
                    nodes[n]["heat"][t] = 0
                if nodes[n]["dhw"][t] < 0.01:
                    nodes[n]["dhw"][t] = 0
                if nodes[n]["elec"][t] < 0.01:
                    nodes[n]["elec"][t] = 0
                if nodes[n]["pv_power"][t] < 0.01:
                    nodes[n]["pv_power"][t] = 0

                # Calculation of Coefficient of Power
                nodes[n]["devs"]["COP_sh35"][t] = 0.4 * (273.15 + 35) / (35 - nodes[n]["T_air"][t])
                nodes[n]["devs"]["COP_sh55"][t] = 0.4 * (273.15 + 55) / (55 - nodes[n]["T_air"][t])

        building_params["ev_exists"] = np.zeros(shape=(options["nb_bes"], 1))
        building_params["pv_exists"] = pv_exists

    else: # clustered input data
        pv_exists = np.zeros(shape=(options["nb_bes"], 1))
        for k in range(options["number_typeWeeks"]):
            nodes[k] = {}
            for n in range(options["nb_bes"]):
                nodes[k][n] = {
                    "elec": districtData.district[n]['user'].elec_cluster[k],
                    "heat": districtData.district[n]['user'].heat_cluster[k],
                    "dhw": districtData.district[n]['user'].dhw_cluster[k],
                    "T_air": districtData.site['T_e_cluster'][k],
                    "type": districtData.district[n]['user'].building,
                    "ev_avail": ev_exists[n] * ev_data["avail"][:, n],
                    "ev_dem_arrive": ev_exists[n] * ev_data["dem_arrive"][:, n],
                    "ev_dem_leave": ev_exists[n] * ev_data["dem_leave"][:, n],
                    #"pv_power": districtData.district[n]['generation_cluster'][k],
                    "devs": {}
                }
                nodes[k][n]["devs"]["COP_sh35"] = np.zeros(len(nodes[0][0]["T_air"]))
                nodes[k][n]["devs"]["COP_sh55"] = np.zeros(len(nodes[0][0]["T_air"]))
                pv_exists[n] = districtData.scenario.PV[n]

                # Check small demand values
                for t in range(len(nodes[0][0]["heat"])):
                    if nodes[k][n]["heat"][t] < 0.01:
                        nodes[k][n]["heat"][t] = 0
                    if nodes[k][n]["dhw"][t] < 0.01:
                        nodes[k][n]["dhw"][t] = 0
                    if nodes[k][n]["elec"][t] < 0.01:
                        nodes[k][n]["elec"][t] = 0
                    #if nodes[k][n]["pv_power"][t] < 0.01:
                    #    nodes[k][n]["pv_power"][t] = 0

                    # Calculation of Coefficient of Power
                    nodes[k][n]["devs"]["COP_sh35"][t] = 0.4 * (273.15 + 35) / (35 - nodes[k][n]["T_air"][t])
                    nodes[k][n]["devs"]["COP_sh55"][t] = 0.4 * (273.15 + 55) / (55 - nodes[k][n]["T_air"][t])

                append_demands = True # double data for rolling horizon opti
                if append_demands:
                    nodes[k][n]["heat_appended"] = np.append(nodes[k][n]["heat"], nodes[k][n]["heat"])
                    nodes[k][n]["dhw_appended"] = np.append(nodes[k][n]["dhw"], nodes[k][n]["dhw"])
                    nodes[k][n]["elec_appended"] = np.append(nodes[k][n]["elec"], nodes[k][n]["elec"])
                    #nodes[k][n]["pv_power_appended"] = np.append(nodes[k][n]["pv_power"], nodes[k][n]["pv_power"])
                    nodes[k][n]["devs"]["COP_sh35_appended"] = np.append(nodes[k][n]["devs"]["COP_sh35"], nodes[k][n]["devs"]["COP_sh35"])
                    nodes[k][n]["devs"]["COP_sh55_appended"] = np.append(nodes[k][n]["devs"]["COP_sh55"], nodes[k][n]["devs"]["COP_sh55"])
                    nodes[k][n]["ev_avail_appended"] = np.append(nodes[k][n]["ev_avail"], nodes[k][n]["ev_avail"])
                    nodes[k][n]["ev_dem_leave_appended"] = np.append(nodes[k][n]["ev_dem_leave"], nodes[k][n]["ev_dem_leave"])


        building_params["ev_exists"] = np.zeros(shape=(options["nb_bes"], 1))
        building_params["pv_exists"] = pv_exists

    #for n in nodes:
    #    nodes["building_" + str(n)]["ev_avail"] = np.zeros(shape=(time_hor, tweeks))
    #    nodes["building_" + str(n)]["ev_dem_arrive"] = np.zeros(shape=(time_hor, tweeks))
    #    nodes["building_" + str(n)]["ev_dem_leave"] = np.zeros(shape=(time_hor, tweeks))
    #    for m in range(tweeks):
    #        for t in range(time_hor):

    #building_params["ev_exists"] = ev_exists

    return nodes, building_params, options




    
def map_devices(options, nodes, building_params, par_rh, districtData): # maps devices from district generator to nodes



    devs = {}


    #devs["bat"] = {}
    #devs["boiler"] = {}
    #devs["hp35"] = {}
    #devs["hp55"] = {}
    #devs["chp"] = {}
    #devs["bz"] = {}
    #devs["eh"] = {}
    #devs["tes"] = {}
    #devs["ev"] = {}

    # get Sunfire fuel cell distribution in district from file
    district = pd.read_csv(options["full_path_scenario"],
        header=0, delimiter=";")  # todo: path has to be adjusted

    T_e_mean = [] # mean of outdoor temperature

    for k in range(options["number_typeWeeks"]):
        T_e_mean.append(np.mean(nodes[k][0]["T_air"]))

    for n in range(options["nb_bes"]):
        devs[n] = {}
        """
            - eta = Q/P
            - omega = (Q+P) / E
        """
        # BATTERY
        # TODO: k_loss
        devs[n]["bat"] = dict(cap=0.0, min_soc=0.05, max_ch=0.6, max_dch=0.6, max_soc=0.95, eta_bat=0.97, k_loss=0)
        # BOILER
        devs[n]["boiler"] = dict(cap=0.0, eta_th=0.97)
        # HEATPUMP
        # TODO: mod_lvl
        devs[n]["hp35"] = dict(cap=0.0, dT_max=15, exists=0, mod_lvl=1)
        devs[n]["hp55"] = dict(cap=0.0,dT_max=15, exists=0, mod_lvl=1)
        # CHP FOR MULTI-FAMILY HOUSES
        # TODO: mod_lvl
        devs[n]["chp"] = dict(cap=0.0, eta_th=0.62, eta_el=0.30, mod_lvl=0.6)
        devs[n]["bz"] = dict(cap=0.0, eta_th=0.53, eta_el=0.39)
        # ELECTRIC HEATER
        devs[n]["eh"] = dict(cap=0.0)
        # THERMAL ENERGY STORAGE
        # TODO: k_loss
        devs[n]["tes"] = dict(cap=0.0, dT_max=35, min_soc=0.0, eta_tes=0.98, eta_ch=1, eta_dch=1)
        # ELECTRIC VEHICLE
        devs[n]["ev"] = dict(cap=0.0, eta_ch_ev=0.97, eta_dch_ev=0.97, min_soc=0.05, max_soc=0.95, max_ch_ev=45,
                          max_dch_ev=40)

        #nodes[n]["devs"] = {}


        devs[n]["tes"]["cap"] = districtData.district[n]['capacities']['TES']

        if districtData.district[n]['capacities']['EV'] :
            devs[n]["ev"]["cap"] = districtData.district[n]['capacities']['EV']

        if districtData.district[n]['capacities']['FC'] :
            devs[n]["bz"]["cap"] = districtData.district[n]['capacities']['FC']

        if districtData.scenario.heater[n] == "BOI":
            devs[n]["boiler"]["cap"] = districtData.district[n]['capacities']['BOI']

        elif districtData.scenario.heater[n] == "HP":
            if (districtData.district[n]['envelope'].construction_year > 1994) or (districtData.district[n]['envelope'].construction_year > 1983 and districtData.district[n]['envelope'].retrofit ==1) or (districtData.district[n]['envelope'].construction_year > 1958 and districtData.district[n]['envelope'].retrofit ==2):
                # heat pump with 35C supply temperature todo: adjust parameters above
                devs[n]["eh"]["cap"] = districtData.district[n]['capacities']['EH']
                devs[n]["hp35"]["cap"] = districtData.district[n]['capacities']['HP']
                devs[n]["hp35"]["exists"] = 1

            else: # heat pump with 55C supply temperature
                devs[n]["eh"]["cap"] = districtData.district[n]['capacities']['EH']
                devs[n]["hp55"]["cap"] = districtData.district[n]['capacities']['HP']
                devs[n]["hp55"]["exists"] = 1

        elif districtData.scenario.heater[n] == "CHP":
            devs[n]["chp"]["cap"] = districtData.district[n]['capacities']['CHP']

        else:
            pass



        if options["number_typeWeeks"] == 0:
            nodes[n]["devs"]["bat"] = devs[n]["bat"]
            nodes[n]["devs"]["eh"] = devs[n]["eh"]
            nodes[n]["devs"]["hp35"] = devs[n]["hp35"]
            nodes[n]["devs"]["hp55"] = devs[n]["hp55"]
            nodes[n]["devs"]["tes"] = devs[n]["tes"]
            nodes[n]["devs"]["chp"] = devs[n]["chp"]
            nodes[n]["devs"]["boiler"] = devs[n]["boiler"]
            nodes[n]["devs"]["ev"] = devs[n]["ev"]
            nodes[n]["devs"]["bz"] = devs[n]["bz"]


        else:
            for k in range(options["number_typeWeeks"]):

                nodes[k][n]["devs"]["bat"] = devs[n]["bat"].copy()
                nodes[k][n]["devs"]["eh"] = devs[n]["eh"].copy()
                nodes[k][n]["devs"]["hp35"] = devs[n]["hp35"].copy()
                nodes[k][n]["devs"]["hp55"] = devs[n]["hp55"].copy()
                nodes[k][n]["devs"]["tes"] = devs[n]["tes"].copy()
                nodes[k][n]["devs"]["chp"] = devs[n]["chp"].copy()
                nodes[k][n]["devs"]["boiler"] = devs[n]["boiler"].copy()
                nodes[k][n]["devs"]["ev"] = devs[n]["ev"].copy()
                nodes[k][n]["devs"]["bz"] = devs[n]["bz"].copy()


    building_params["T_e_mean"] = T_e_mean

    return nodes, devs, building_params

def get_design_heat(options, demands, building_params): # gets

    buildings = options["nb_bes"]

    # Calculation of design heat loads per building
    design_heat = np.zeros(shape=buildings)
    design_dhw = np.zeros(shape=buildings)
    daily_mean_heat = np.zeros(shape=buildings)
    daily_mean_temp = np.zeros(shape=(buildings, 365))
    for n in range(buildings):
        design_heat[n] = 1.2 * np.max(demands[n]["heat"] + demands[n]["dhw"])
        design_dhw[n] = 2 * np.max(demands[n]["dhw"])
        for t in range(365):
            # calc daily heat demand in kWh
            daily_mean_temp[n, t] = np.sum(demands[n]["heat"][24*t:24*t+24]) \
                                    + np.sum(demands[n]["dhw"][24*t:24*t+24])
        daily_mean_heat[n] = np.mean(daily_mean_temp[n, :])

    building_params["design"] = design_heat
    building_params["design_dhw"] = design_dhw
    building_params["mean_heat"] = daily_mean_heat

    return building_params

def get_ev_dat(ev_raw): # gets EV data from district generator

    # manual parameters for ev
    ev_param = {}
    ev_param["soc_nom_ev"] = 35.0  # 35 kWh are the average EV battery capcity # todo: outdated
    ev_param["soc_init_ev"] = 0.05 * ev_param["soc_nom_ev"]
    ev_param["eta_ch_ev"] = 0.97
    ev_param["p_max_ev"] = 11.0  # in kW
    ev_param["p_min_ev"] = 0
    ev_param["ev_operation"] = "grid_reactive"  # possible entries are "on_demand", "grid_reactive" and "bi-directional"

    ev_dat = {}
    # convert 15 min data to hourly data # resolution
    ev_dat["bed"] = {}
    ev_dat["bed"]["avail"] = np.zeros(shape=(len(ev_raw["EV_occurrence"][0]), 8760))
    ev_dat["bed"]["dem_arrive"] = np.zeros(shape=(len(ev_raw["EV_uncontrolled_charging_profile"][0]), 8760))
    for n in range(len(ev_raw["EV_occurrence"][0])):
        for t in range(8760):
            ev_dat["bed"]["avail"][n, t] = np.round(np.sum(ev_raw["EV_occurrence"][t * 4:(t * 4 + 4), n]) / 4)

    daily_dem = ev_raw["EV_daily_demand"]

    # map demand to end of available phase (grid-ractive and bi directional charging)
    index_leave = {}
    for i in range(len(ev_dat["bed"]["avail"])):
        index_leave[i] = ev_dat["bed"]["avail"][i, :-1] > ev_dat["bed"]["avail"][i, 1:]
        # last charging phase of the year ends with t=T -> set last entry True
        index_leave[i] = np.append(index_leave[i], True)

    # EVs are still available at t=0 but have been charged the evening before -> delete first True entry
    for i in range(len(ev_dat["bed"]["avail"])):
        temp = next(x for x, val in enumerate(index_leave[i]) if val == True)
        index_leave[i][temp] = False

    ev_dat["bed"]["dem_leave"] = np.zeros([20, 8760]) # resolution
    for n in range(20):
        for i in range(1, 365):
            ev_dat["bed"]["dem_leave"][n, (24 * i):(24 * i + 24)] = index_leave[n][(24 * i):(24 * i + 24)] * daily_dem[
                n - 1, 0]
        ev_dat["bed"]["dem_leave"][n, 8759] = index_leave[n][8759] * daily_dem[n, 0]

    # map demands to beginning of available phase (on-demand charging)
    index_arrive = {}
    index_temp = {}
    for i in range(len(ev_dat["bed"]["avail"])):
        index_temp[i] = ev_dat["bed"]["avail"][i, :-1] < ev_dat["bed"]["avail"][i, 1:]
        index_arrive[i] = False
        index_arrive[i] = np.append(index_arrive[i], index_temp[i])

    ev_dat["bed"]["dem_arrive"] = np.zeros([20, 8760])
    for n in range(20):
        for i in range(0, 365):
            ev_dat["bed"]["dem_arrive"][n, (24 * i):(24 * i + 24)] = index_arrive[n][(24 * i):(24 * i + 24)] * \
                                                                     daily_dem[n, 0]

    ev_dat["demands"] = {}
    ev_dat["demands"]["bed"] = {}
    ev_dat["demands"]["bed"]["ev"] = {}

    number_evs_max = len(ev_dat["bed"]["avail"])

    return ev_param, ev_dat, number_evs_max


def learning_bidding(): #
    pars_li = {
                "rec": 0.08,   # recency parameter for learning intelligence agent [0,1]
                "exp": 0.99,   # experimentation parameter for learning intelligence agent [0,1]
                "step": 0.01,  # step size for bidding (zero, learning)
                "init_prop": dict(buy=0.01, sell=0.01) # initial propensities for learning intelligence agent
    }
    #try:
    #    filename = "results//0.08_scn_1.pkl"  # change name!!!!!!!!!!!!!!!!!!
    #    with open(filename, "rb") as f:
    #        init_prop = p.load(f)
    #
    #    pars_li["init_prop"] = init_prop
    #except Exception as e:
    #    print(e, "Setting new inital propensities.")
    #    pars_li["init_prop"] = dict(buy=0.01, sell=0.01)  # initial propensities for learning intelligence agent

    return pars_li
