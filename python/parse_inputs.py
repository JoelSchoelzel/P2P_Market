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
    params["eco"]["pr",   "el"]     = 0.319
    params["eco"]["sell", "chp"]    = 0.091
    params["eco"]["sell", "pv"]     = 0.091
    params["eco"]["gas", "chp"]     = 0.0635   # €/kWh
    params["eco"]["gas", "boiler"]  = 0.0635   # €/kWh


    params["phy"]["rho_w"]           = 1000 # [kg/m^3]
    params["phy"]["c_w"]             = 4180 # [J/(kg*K)]
    params["phy"]["beta"]            = 0.2
    params["phy"]["A_max"]           = 40   # Maximum available roof area
    
    # Further parameters
    params["gp"]["mip_gap"]         = 0.01 # https://www.gurobi.com/documentation/9.1/refman/mipgap2.html
    params["gp"]["time_limit"]      = 100 # [s]  https://www.gurobi.com/documentation/9.1/refman/timelimit.html
    params["gp"]["numeric_focus"]   = 3   # https://www.gurobi.com/documentation/9.1/refman/numericfocus.html


    return params


def compute_pars_rh(input_rh):
    param = input_rh

    param["dt"] = 1

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

        # Example to explain set up:    n_hours: 42
        #                               n_hours_ov: 36
        #                           --> n_hours_ch: 12
        #                               n_blocks: 2
        #                               resolution: [1,6]

        # Calculate duration of each time block
        param["org_block_duration"] = {}  # original block duration (for example: [12,36])
        param["block_duration"] = {}  # block duration with another resolution (for example: [12,36/6]=[12,6])

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
        if param["month"] == 0:

            # Calculate number of operational optimizations (month = 0: optimization of whole year)
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
            param["n_opt"] = int(np.ceil(hours_month / param["n_hours_ch"]))

            # Set up starting hour of each optimization
            param["hour_start"] = {}  # starting hour of each optimization
            for i in range(param["n_opt"]):
                # Starting hour of each optimization
                param["hour_start"][i] = param["month_start"][param["month"]] + i * param["n_hours_ch"]

                # Set up optimization time steps (incl. aggregated foresight time steps)
        param["time_steps"] = {}  # time steps for optimization incl. aggregation, for 1st optimization for example above:
        # [0,1,2,3,4,5,6,7,8,9,10,11, 12,13,14,15,16,17]
        param["org_time_steps"] = {}  # original time steps for optimizations, for 1st optimization for example above:
        # [0,1,2,3,4,5,6,7,8,9,10,11, 12,18,24,30,36]
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
            for t in param["time_steps"][i]:
                if count > 0:
                    param["org_time_steps"][i].append(param["org_time_steps"][i][-1] + param["duration"][i][t - 1])


    # adjust the following values
    param["start_time"] = param["month_start"][input_rh["month"]]
    param["end_time"] = param["month_start"][input_rh["month"] + 1]
    if input_rh["month"] == 0:
        param["month_start"][0] = 0
        param["obs_period"] = 365  # Observation period in days
        param["times"] = param["obs_period"] * 24
    else:
        param["obs_period"] = int((param["end_time"] - param["start_time"]) / 24)
        param["times"] = param["obs_period"]  * 24 + input_rh["n_hours_ov"]

    return param


# %% Aggregate the foresight time steps (by averaging)

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


def read_demands(options, nodes):
        
    # Define path for use case input data
    path_file = options["path_file"]
    path_input = path_file + "/raw_inputs/demands_vorstadtnetz/"
    #path_nodes = path_input + name_nodefile
    #path_demands = path_input + "demands\\"

    # todo: days within month * 24 * dt
    datapoints = options["times"]
    #time_hor = options["time_hor"]
    #tweeks = options["tweeks"]
    ev_share = options["ev_share"]

    # todo: in options wird ein Netz ausgewählt, damit werden Netz- (Grenzen des ONS, Stränge, etc.) und Gebäudeinformationen gebündelt eingelesen --> z.B. number_bes
    # Possible selection of typical grids
    if options["Dorfnetz"]:
        grid = "dorfnetz"
    else:
        grid = "vorstadtnetz"

    # Building parameters
    building_params = pd.read_csv(path_input + "buildings_" + grid + ".csv",delimiter=";")
    options["nb_bes"] = len(building_params)

    # Get heatloads of building categories
    heatloads = {}
    for cat in range(1,7):
        heatloads[cat] = np.loadtxt(
            open(path_input + "cat_" + str(cat) + ".csv","rb"), delimiter=";", skiprows=1) / 1000  # kW, heat demand

    # Fill nodes dictionairy with demands (electricity, drinking hot water, heat load)
    demands = {}
    for i in range(options["nb_bes"]):
        demands[i] = {
            "elec": np.loadtxt(
                open(path_input + "/elec_" + str(i) + ".csv", "rb"),
                delimiter=",", skiprows=1, usecols=1) / 1000,  # kW, electricity demand
            "dhw": np.loadtxt(
                open(path_input + "/dhw_" + str(i) + ".csv","rb"),
                skiprows=1) / 1000,  # kW, domestic hot water demand
        }

        for cat in range(1,7):
            if cat == building_params["cat"][i]:
                demands[i]["heat"] = heatloads[cat][:,1]
            else:
                pass

    for n in range(options["nb_bes"]):
        nodes["building_" + str(n)] = {
            "elec": demands[n]["elec"],
            "heat": demands[n]["heat"],
            "dhw": demands[n]["dhw"].T,
        }
    
    # Check small demand values
    for n in nodes:
        for t in range(len(nodes["building_" + str(0)]["heat"])):
            if nodes[n]["heat"][t] < 0.01:
                nodes[n]["heat"][t] = 0
            if nodes[n]["dhw"][t] < 0.01:
                nodes[n]["dhw"][t] = 0
            if nodes[n]["elec"][t] < 0.01:
                nodes[n]["elec"][t] = 0

    # Electric Vehicles
    ev_data = ev_param.ev_load(options, options["nb_bes"])
    ev_exists = ev_param.ev_share(ev_share, options["nb_bes"])

    #for n in nodes:
    #    nodes["building_" + str(n)]["ev_avail"] = np.zeros(shape=(time_hor, tweeks))
    #    nodes["building_" + str(n)]["ev_dem_arrive"] = np.zeros(shape=(time_hor, tweeks))
    #    nodes["building_" + str(n)]["ev_dem_leave"] = np.zeros(shape=(time_hor, tweeks))
    #    for m in range(tweeks):
    #        for t in range(time_hor):
    for n in range(options["nb_bes"]):
        nodes["building_" + str(n)]["ev_avail"]      = ev_exists[n] * ev_data["avail"][:, n]
        nodes["building_" + str(n)]["ev_dem_arrive"] = ev_exists[n] * ev_data["dem_arrive"][:, n]
        nodes["building_" + str(n)]["ev_dem_leave"]  = ev_exists[n] * ev_data["dem_leave"][:, n]

    building_params["ev_exists"] = ev_exists

                
    return nodes, building_params, options

def get_solar_irr(options, weather):

    # Define path for use case input data
    path_file = options["path_file"]
    path_input = path_file + "/raw_inputs/demands_vorstadtnetz/"

    # todo: days within month * 24 * dt
    datapoints = 8760

    # todo: in options wird ein Netz ausgewählt, damit werden Netz- (Grenzen des ONS, Stränge, etc.) und Gebäudeinformationen gebündelt eingelesen --> z.B. number_bes
    # Possible selection of typical grids
    if options["Dorfnetz"]:
        grid = "dorfnetz"
    else:
        grid = "vorstadtnetz"

    # Building parameters
    building_params = pd.read_csv(path_input + "buildings_" + grid + ".csv",delimiter=";")
    options["nb_bes"] = len(building_params)

    vorher = [i for i in range(0,datapoints,4)]
    nachher = [i for i in range(0,datapoints)]
    weather_param = {}
    weather_param["T_air"] = weather["T_air"]   # np.interp(nachher, vorher, weather["T_air"])
    weather_param["G_dir"] = weather["sol_dir"] # np.interp(nachher, vorher, weather["sol_dir"])
    weather_param["G_dif"] = weather["sol_diff"]# np.interp(nachher, vorher, weather["sol_diff"])
    weather_param["G_sol"] = weather_param["G_dir"] + weather_param["G_dif"]

    # todo: check if annual calc works on 15min basis
    # get solar irradiance on tilted surface
    solar_irr = np.zeros(shape=(options["nb_bes"], datapoints))

    for n in range(options["nb_bes"]):
        solar_irr[n] = solar.get_irrad_profile(weather_param, building_params["azimuth"][n],
                                               building_params["elevation"][n])

    nodes = {}
    for n in range(options["nb_bes"]):
        nodes["building_" + str(n)] = {
                "T_air": weather_param["T_air"]
        }

    return nodes, solar_irr, weather_param

def get_pv_power(nodes, options, building_params, devs, solar_irr):

    pv_share = options["pv_share"]

    # todo: days within month * 24 * dt
    datapoints = 8760

    # calculate PV power
    pv_power = np.zeros(shape=(options["nb_bes"], datapoints))
    for n in range(options["nb_bes"]):
        for t in range(datapoints):
            pv_power[n, t] = solar_irr[n, t] * devs["pv"]["eta_el"][t] * devs["pv"]["area_real"] \
                             * building_params["modules"][n] / 1000  # kW,       PV output

        nodes["building_" + str(n)]["pv_power"] = pv_power[n, :]

    # calculate availability of pv system considerung pv_share
    pv_exists = pv.pv_share(pv_share, options["nb_bes"])
    building_params["pv_exists"] = pv_exists

    #for n in range(options["nb_bes"]):
    #    nodes["building_" + str(n)] = {
    #        "pv_power": generation["building_" + str(n)]["pv_power"],
    #    }

    # Check small demand values
    for n in range(options["nb_bes"]):
        for t in range(datapoints):
            if nodes["building_" + str(n)]["pv_power"][t] < 0.01:
                nodes["building_" + str(n)]["pv_power"][t] = 0

    return nodes, building_params
    

    
def map_devices(options, nodes, building_params, weather_param, params, scenarios, scn):

    building_params = get_design_heat(options, nodes, building_params)
    datapoints = 8760

    devs = {}
    devs["pv"] = dict(eta_el_stc=0.199, area_real=1.6, eta_inv=0.96, t_cell_stc=25, G_stc=1000, t_cell_noct=44,
                      t_air_noct=20, G_noct=800, gamma=-0.003, eta_opt=0.9)

    # calculate time variant efficiency
    t_cell = np.zeros(shape=(datapoints, 1))
    eta_el = np.zeros(shape=(datapoints, 1))
    for t in range(datapoints):
        t_cell[t] = (weather_param["T_air"][t] + (devs["pv"]["t_cell_noct"] - devs["pv"]["t_air_noct"])
                     * (weather_param["G_sol"][t] / devs["pv"]["G_noct"])
                     * (1 - (devs["pv"]["eta_el_stc"] * (1 - devs["pv"]["gamma"] * devs["pv"]["t_cell_stc"])) /
                        devs["pv"]["eta_opt"])) / \
                    ((1 + (devs["pv"]["t_cell_noct"] - devs["pv"]["t_air_noct"])
                      * (weather_param["G_sol"][t] / devs["pv"]["G_noct"]) *
                      ((devs["pv"]["gamma"] * devs["pv"]["eta_el_stc"]) / devs["pv"]["eta_opt"])))

        eta_el[t] = devs["pv"]["eta_el_stc"] * (1 + devs["pv"]["gamma"] * (t_cell[t] - devs["pv"]["t_cell_stc"]))

        devs["pv"]["eta_el"] = eta_el[:]


    devs["bat"] = {}
    devs["boiler"] = {}
    devs["hp35"] = {}
    devs["hp55"] = {}
    devs["chp"] = {}
    devs["bz"] = {}
    devs["eh"] = {}
    devs["tes"] = {}
    devs["ev"] = {}

    for n in range(options["nb_bes"]):
        """
            - eta = Q/P
            - omega = (Q+P) / E
        """
        # BATTERY
        # TODO: k_loss
        devs["bat"][n] = dict(cap=0.0, min_soc=0.1, max_ch=0.6, max_dch=0.6, max_soc=0.9, eta_bat=0.957, k_loss=0)
        # BOILER
        devs["boiler"][n] = dict(cap=0.0, eta_th=0.94)
        # HEATPUMP
        # TODO: mod_lvl
        devs["hp35"][n] = dict(cap=0.0, dT_max=15, exists=0, mod_lvl=1)
        devs["hp55"][n] = dict(cap=0.0,dT_max=15, exists=0, mod_lvl=1)
        # CHP FOR MULTI-FAMILY HOUSES
        # TODO: mod_lvl
        devs["chp"][n] = dict(cap=0.0, eta_th=0.62, eta_el=0.30, mod_lvl=0.6)
        devs["bz"][n] = dict(cap=0.0, eta_th=0.53, eta_el=0.39)
        # ELECTRIC HEATER
        devs["eh"][n] = dict(cap=0.0)
        # THERMAL ENERGY STORAGE
        # TODO: k_loss
        devs["tes"][n] = dict(cap=0.0, dT_max=35, min_soc=0.0, eta_tes=0.98, eta_ch=1, eta_dch=1)
        # ELECTRIC VEHICLE
        devs["ev"][n] = dict(cap=0.0, eta_ch_ev=0.95, eta_dch_ev=0.97, min_soc=0.1, max_soc=0.9, max_ch_ev=45,
                          max_dch_ev=40)

        nodes["building_" + str(n)]["devs"] = {}

        nodes["building_" + str(n)]["devs"]["bat"] = devs["bat"][n]
        nodes["building_" + str(n)]["devs"]["eh"] = devs["eh"][n]
        nodes["building_" + str(n)]["devs"]["hp35"] = devs["hp35"][n]
        nodes["building_" + str(n)]["devs"]["hp55"] = devs["hp55"][n]
        nodes["building_" + str(n)]["devs"]["tes"] = devs["tes"][n]
        nodes["building_" + str(n)]["devs"]["chp"] = devs["chp"][n]
        nodes["building_" + str(n)]["devs"]["boiler"] = devs["boiler"][n]
        nodes["building_" + str(n)]["devs"]["ev"] = devs["ev"][n]
        nodes["building_" + str(n)]["devs"]["pv"] = devs["pv"]


        nodes["building_" + str(n)]["devs"]["tes"]["cap"] = params["phy"]["beta"] * building_params["mean_heat"][n]

        if building_params["ev_exists"][n] == 1:
            nodes["building_" + str(n)]["devs"]["ev"]["cap"] = 35.0

        if scenarios.iloc[n, scn] == "gas":
            nodes["building_" + str(n)]["devs"]["boiler"]["cap"] = building_params["design"][n]

        elif scenarios.iloc[n, scn] == "hp" and building_params["cat"][n] == 1:
            nodes["building_" + str(n)]["devs"]["eh"]["cap"] = building_params["design_dhw"][n]
            nodes["building_" + str(n)]["devs"]["hp35"]["cap"] = building_params["design"][n]
            nodes["building_" + str(n)]["devs"]["hp35"]["exists"] = 1

        elif scenarios.iloc[n,scn] == "hp" and building_params["cat"][n] == 2:
            nodes["building_" + str(n)]["devs"]["eh"]["cap"] = building_params["design_dhw"][n]
            nodes["building_" + str(n)]["devs"]["hp55"]["cap"] = building_params["design"][n]
            nodes["building_" + str(n)]["devs"]["hp55"]["exists"] = 1

        elif scenarios.iloc[n, scn] == "chp":
            nodes["building_" + str(n)]["devs"]["chp"]["cap"] = building_params["design"][n]

        else:
            pass

    # Calculation of Coefficient of Power
    for n in range(options["nb_bes"]):
        nodes["building_" + str(n)]["devs"]["COP_sh35"] = np.zeros(datapoints)
        nodes["building_" + str(n)]["devs"]["COP_sh55"] = np.zeros(datapoints)
        for t in range(datapoints):
                nodes["building_" + str(n)]["devs"]["COP_sh35"][t] = 0.4 * (273.15 + 35) / (35 - weather_param["T_air"][t])
                nodes["building_" + str(n)]["devs"]["COP_sh55"][t] = 0.4 * (273.15 + 55) / (55 - weather_param["T_air"][t])

    return nodes, devs, building_params

def get_design_heat(options, demands, building_params):

    buildings = options["nb_bes"]

    # Calculation of design heat loads per building
    design_heat = np.zeros(shape=buildings)
    design_dhw = np.zeros(shape=buildings)
    daily_mean_heat = np.zeros(shape=buildings)
    daily_mean_temp = np.zeros(shape=(buildings, 365))
    for n in range(buildings):
        design_heat[n] = 1.2 * np.max(demands["building_" + str(n)]["heat"] + demands["building_" + str(n)]["dhw"])
        design_dhw[n] = 2 * np.max(demands["building_" + str(n)]["dhw"])
        for t in range(365):
            # calc daily heat demand in kWh
            daily_mean_temp[n, t] = np.sum(demands["building_" + str(n)]["heat"][24*t:24*t+24]) \
                                    + np.sum(demands["building_" + str(n)]["dhw"][24*t:24*t+24])
        daily_mean_heat[n] = np.mean(daily_mean_temp[n, :])

    building_params["design"] = design_heat
    building_params["design_dhw"] = design_dhw
    building_params["mean_heat"] = daily_mean_heat

    return building_params



def get_ev_dat(ev_raw):

    # manual parameters for ev
    ev_param = {}
    ev_param["soc_nom_ev"] = 35.0  # 35 kWh are the average EV battery capcity
    ev_param["soc_init_ev"] = 0.05 * ev_param["soc_nom_ev"]
    ev_param["eta_ch_ev"] = 0.97
    ev_param["p_max_ev"] = 11.0  # in kW
    ev_param["p_min_ev"] = 0
    ev_param["ev_operation"] = "grid_reactive"  # possible entries are "on_demand", "grid_reactive" and "bi-directional"

    ev_dat = {}
    # convert 15 min data to hourly data
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

    ev_dat["bed"]["dem_leave"] = np.zeros([20, 8760])
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



if __name__ == "__main__":
    timesteps = 24
    days = 5
    # Random temperatures between -10 and +20 degC:
    temperature_ambient = np.random.rand(timesteps) * 30 - 10
    
    temperature_design = -12 # Aachen
    
    solar_irradiation = np.random.rand(timesteps) * 800
    solar_irradiation
    
    devs = read_devices(timesteps, temperature_ambient, 
                        temperature_flow=35,
                        temperature_design=temperature_design,
                        solar_irradiation=solar_irradiation)
                        
    (eco, par, devs) = read_economics(devs)
