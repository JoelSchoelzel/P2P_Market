#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subproblem optimization model for hierarchical central supply system (CSS) optimization.
@author: Joel Schölzel, based on Sarah Henn and Thomas Schütz
"""

from __future__ import division

import gurobipy as gp
import numpy as np
import datetime


# computes the optimal operation of the BES for the given prediction horizon
def compute(node, params, par_rh, building_param, init_val, n_opt, options):
    # nodes: dict, contains all relevant information about the
    # params:  dict, economic parameters, such as costs of electricity or gas, and technical parameters for optimization
    # par_rh: dict, contains information about the prediction horizon (time-related parameters).
    # E.g. duration, time steps, month, etc.
    # building_param: dict, contains information about the building, such as the type, the number of apartments, etc.
    # init_val: dict, contains the initial values for the storage devices, such as the initial SOC
    # n_opt: int, number of the optimization horizon
    # options: dict, contains information about the optimization, such as the discretization of the input data

    # Define subsets
    heater = ("s_hp35", "s_hp55") # Large-scale heat pumps
    storage = ("s_bat") # Shared battery storage
    renewables = ("s_pv", "s_wind")    # Solar park, wind turbine.
    device = ("s_hp35", "s_hp55", "s_bat", "s_pv", "s_wind" )

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    time_steps = par_rh["time_steps"][n_opt]
    # last time step for soc_end
    first_time_step = time_steps[0]
    last_time_step = time_steps[-1]
    time_steps_block_bid = [time_steps[0], time_steps[1], time_steps[2], time_steps[3]]
    # Durations of time steps # for aggregated RH
    # duration = par_rh["duration"][n_opt]

    # get relevant input data for prediction horizon
    discretization_input_data = options["discretization_input_data"]

    # get elec, heat etc. for optimization n_opt
    demands = {}
    PV_GEN = {}
    WIND_GEN = {}
    s_COP35 = {}
    s_COP55 = {}

    for i in range(len(time_steps)):
        param00 = time_steps[i]
        param01 = int(dt[param00]/discretization_input_data)
        param02 = int(par_rh["org_time_steps"][n_opt][i]/discretization_input_data)
        if param01 < 1:
            raise ValueError("Interpolation of input data necessary")
        elif options["number_typeWeeks"] == 0:
            if "pv_power" in node and "wind_power" in node:
                PV_GEN[param00] = np.mean([node["pv_power"][param02], node["pv_power"][param02 + param01 - 1]])
                WIND_GEN[param00] = np.mean([node["wind_power"][param02], node["wind_power"][param02 + param01 - 1]])
            else:
                node["pv_power"] = [0] * (param02 + param01)  # or some default value
                node["wind_power"] = [0] * (param02 + param01)  # or some default value
                PV_GEN[param00] = np.mean([node["pv_power"][param02], node["pv_power"][param02 + param01 - 1]])
                WIND_GEN[param00] = np.mean([node["wind_power"][param02], node["wind_power"][param02 + param01 - 1]])
            s_COP35[param00] = np.mean([node["css"]["devs"]["s_COP_sh35"][param02],
                                        node["css"]["devs"]["s_COP_sh35"][param02 + param01 - 1]])
            s_COP55[param00] = np.mean([node["css"]["devs"]["s_COP_sh55"][param02],
                                        node["css"]["devs"]["s_COP_sh55"][param02 + param01 - 1]])
        else:
            if "pv_power" in node and "wind_power" in node:
                PV_GEN[param00] = np.mean([node["pv_power_appended"][param02],
                                           node["pv_power_appended"][param02 + param01 - 1]])
                WIND_GEN[param00] = np.mean([node["wind_power_appended"][param02],
                                             node["wind_power_appended"][param02 + param01 - 1]])
            else:
                node["pv_power"] = [0] * (param02 + param01)  # or some default value
                node["wind_power"] = [0] * (param02 + param01)  # or some default value
                PV_GEN[param00] = np.mean([node["pv_power_appended"][param02],
                                           node["pv_power_appended"][param02 + param01 - 1]])
                WIND_GEN[param00] = np.mean([node["wind_power_appended"][param02],
                                             node["wind_power_appended"][param02 + param01 - 1]])
            s_COP35[param00] = np.mean([node["css"]["devs"]["s_COP_sh35_appended"][param02],
                                        node["css"]["devs"]["s_COP_sh35_appended"][param02 + param01 - 1]])
            s_COP55[param00] = np.mean([node["css"]["devs"]["s_COP_sh55_appended"][param02],
                                        node["css"]["devs"]["s_COP_sh55_appended"][param02 + param01 - 1]])

        demands = {
        "PV_GEN": PV_GEN,
        "WIND_GEN": WIND_GEN,
        "s_COP35": s_COP35,
        "s_COP55": s_COP55,
        }

    model = gp.Model("Operation computation")

    # Initialization: only if initial values have been generated in previous prediction horizon
    soc_init_rh = {}
    if bool(init_val) == True:  #If init_val exists, the initial state of charge (SOC) for the battery (bat) is used in the model.
        # initial SOCs
        for dev in storage:
            soc_init_rh[dev] = init_val["soc"][dev]

    if par_rh["month"] == 0:
        par_rh["month"] = par_rh["month"] + 1

    # Define variables
    # Costs and Revenues
    c_dem = {dev: model.addVar(vtype="C", name="c_dem_" + dev)
            for dev in ("s_bat", "s_hp35", "s_hp55")}

    revenue = {dev: model.addVar(vtype="C", name="revenue_" + dev)
            for dev in ("s_bat", "s_hp35", "s_hp55",  "s_pv", "s_wind")}

    # SOC, charging, discharging, power and heat
    soc = {}
    p_ch = {}
    p_dch = {}
    power = {}
    heat = {}
    for dev in storage:  # All storage devices
        soc[dev] = {}
        p_ch[dev] = {}
        p_dch[dev] = {}
        for t in time_steps:  # All time steps of all days
            soc[dev][t] = model.addVar(vtype="C", name="SOC_" + dev + "_" + str(t))
            p_ch[dev][t] = model.addVar(vtype="C", name="p_ch_" + dev + "_" + str(t))
            p_dch[dev][t] = model.addVar(vtype="C", name="p_dch_" + dev + "_" + str(t))

    for dev in heater:
        power[dev] = {}
        heat[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))
            heat[dev][t] = model.addVar(vtype="C", lb=0, name="Q_" + dev + "_" + str(t))

    for dev in renewables:
        power[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # mapping storage sizes
    soc_nom = {}
    for dev in storage:
        soc_nom[dev] = node["devs"][dev]["cap"] # kWh  Nominal storage capacity

    # Storage initial SOC's
    soc_init = {}
    #soc_init["tes"] = soc_nom["tes"] * 0.1  # kWh   Initial SOC TES
    soc_init["s_bat"] = soc_nom["s_bat"] * 0.1  # kWh   Initial SOC Battery
    #soc_init["ev"] = soc_nom["ev"] * 0.75

    # Dicts for the variables of traded power and trading price
    power_trade = {} # Power traded
    prev_trade = {} # Previous power traded
    # VARIABLE FOR TRADING POWER
    for peer in ["buyer", "seller"]:
        power_trade[peer] = {}
        prev_trade[peer] = {}
        for t in time_steps:
            power_trade[peer][t] = model.addVar(vtype="C", name="Power_trade_" + peer + "_" + str(t))
            prev_trade[peer][t] = model.addVar(vtype="C", name="Previous_power_trade_" + peer + "_" + str(t))

    # Electricity imports, sold and self-used electricity
    p_imp = {} # Total electricity imported
    p_use = {} # Electricity self-used
    p_sell = {} # Total electricity sold
    y_imp = {} # Binary variable for electricity import
    p_grid_buy = {} # Electricity bought from the grid
    p_grid_sell = {} # Electricity sold to the grid
    for t in time_steps:
        p_imp[t] = model.addVar(vtype="C", name="p_imp_" + str(t))
        y_imp[t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_imp_exp_" + str(t))
        p_grid_buy[t] = model.addVar(vtype="C", name="p_grid_buy" + str(t))
        p_grid_sell[t] = model.addVar(vtype="C", name="p_grid_sell" + str(t))
    for dev in ("s_pv", "s_wind"):
        p_use[dev] = {}
        p_sell[dev] = {}
        for t in time_steps:
            p_use[dev][t] = model.addVar(vtype="C", name="p_use_" + dev + "_" + str(t))
            p_sell[dev][t] = model.addVar(vtype="C", name="p_sell_" + dev + "_" + str(t))


    # Activation decision variables
    # binary variable for each css block to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["css_load"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # Update model
    model.update()

    # Objective function
    model.setObjective(c_dem["s_hp35"] + c_dem["s_hp55"] + c_dem["s_bat"]
                       - revenue["s_pv"] - revenue["s_wind"] - revenue["s_hp35"] - revenue["s_hp55"] - revenue["s_bat"],
                       gp.GRB.MINIMIZE)


    # Define constraints
    # Economic constraints

    # Demand related costs (electricity)
    for dev in ("s_hp35", "s_hp55", "s_bat"):
        model.addConstr(c_dem[dev] == sum(p_imp[t] * params["eco"]["pr", "el"] for t in time_steps),
                    name="Demand_costs_" + dev)

    # Revenues for selling electricity to the grid / neighborhood
    for dev in ("s_pv", "s_wind", "s_bat"):
        model.addConstr(revenue[dev] == sum(p_sell[dev][t] * params["eco"]["sell" + "_" + dev] for t in time_steps),
                        name="Feed_in_rev_" + dev)

    # Revenue for selling heat to the grid / neighborhood
    for dev in heater:
        model.addConstr(revenue[dev] == sum(heat[dev][t] * params["eco"]["sell" + "_" + dev] for t in time_steps),
                        name="Heat_rev_" + dev)


    # Devices operation

    for t in time_steps:
    # Heat pumps
        # Heat output between mod_lvl*Q_nom and Q_nom (P_nom for heat pumps)
        # Power and Energy directly result from Heat output
        dev = "s_hp35"
        model.addConstr(heat[dev][t] == power[dev][t] * demands["s_COP35"][t],
                        name="Power_equation_" + dev + "_" + str(t))
        # TODO: Check need of mod_lvl
        model.addConstr(heat[dev][t] >= power[dev][t] * demands["s_COP35"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))
        dev = "s_hp55"
        model.addConstr(heat[dev][t] == power[dev][t] * demands["s_COP55"][t],
                        name="Power_equation_" + dev + "_" + str(t))
        # TODO: Check need of mod_lvl
        model.addConstr(heat[dev][t] >= power[dev][t] * demands["s_COP55"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))

    # Solar park and wind turbine
        dev = "s_pv"
        model.addConstr(power[dev][t] == demands["PV_GEN"][t],
                        name="Solar_electrical_" + dev + "_" + str(t))

        dev = "s_wind"
        model.addConstr(power[dev][t] == demands["WIND_GEN"][t],
                        name="Wind_electrical_" + dev + "_" + str(t))

    # Storage devices flexibility
    """
    for dev in storage:
        model.addConstr(soc[dev][t] == soc_init[dev] + sum(p_ch[dev][t] * dt - p_dch[dev][t] * dt), 
                        name="SOC_equation_" + dev + "_" + str(t))
        model.addConstr(soc[dev][t] <= soc_nom[dev], name="SOC_max_" + dev + "_" + str(t))
        model.addConstr(soc[dev][t] >= 0, name="SOC_min_" + dev + "_" + str(t))
    """

    dev = "s_bat"
    k_loss = node["devs"][dev]["k_loss"]  # Battery degradation loss factor
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]  # Start of optimization window (hour)
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]  # Start of month
        else:
            soc_prev = soc[dev][t - 1]  # Previous SOC

        # Charging and discharging power limits based on battery capacity and usage (y is a binary variable controlling operation modes)
        # Maximal charging
        model.addConstr(p_ch["s_bat"][t] <= y["s_bat"][t] * node["devs"]["s_bat"]["cap"] * node["devs"]["s_bat"]["max_ch"],
                        name="max_ch_s_bat_" + str(t))
        # Maximal discharging
        model.addConstr(p_dch["s_bat"][t] <= (1 - y["s_bat"][t]) * node["devs"]["s_bat"]["cap"] * node["devs"]["s_bat"]["max_dch"],
                        name="max_dch_s_bat_" + str(t))

        # Battery SOC constraints: Minimal and maximal soc
        model.addConstr(soc["s_bat"][t] <= node["devs"]["s_bat"]["max_soc"] * node["devs"]["s_bat"]["cap"],
                        name="max_soc_s_bat_" + str(t))
        model.addConstr(soc["s_bat"][t] >= node["devs"]["s_bat"]["min_soc"] * node["devs"]["s_bat"]["cap"],
                        name="max_soc_s_bat_" + str(t))

        #SoC degradation over time
        model.addConstr(soc[dev][t] == (1 - k_loss) * soc_prev +
                        dt[t] * (node["devs"][dev]["eta_bat"] * p_ch[dev][t] - 1 / node["devs"][dev]["eta_bat"] *
                                 p_dch[dev][t]),
                        name="Storage_balance_" + dev + "_" + str(t))

    # Electricity balance for the central supply system
    for t in time_steps:
        model.addConstr(p_ch["s_bat"][t] + power["s_hp35"][t] + power["s_hp55"][t]
                        - p_dch["s_bat"][t] - p_use["s_wind"][t] - p_use["s_pv"][t] - p_sell["s_wind"][t] - p_sell["s_pv"][t]
                        == p_imp[t],
                        name="Electricity_balance_" + str(t))
        #Electricity import of the central supply system
        #todo: check and correct p_imp[t] == power_trade["buyer"][t] + prev_trade["buyer"][t]
        model.addConstr(p_imp[t] == p_grid_buy[t] + power_trade["buyer"][t] + prev_trade["buyer"][t])
        model.addConstr(power_trade["buyer"][t] == 0)
        model.addConstr(prev_trade["buyer"][t] == 0)
        
    # Split generation into self-used and sold electricity for the central supply system
    for dev in renewables:
        for t in time_steps:
            model.addConstr(power[dev][t] == p_use[dev][t] + p_sell[dev][t],
                            name="Renewable_power=sell+use_" + dev + "_" + str(t))
            
    # Power trading constraints: selling and buying power from/to the grid
    for t in time_steps:
        model.addConstr(p_sell["s_pv"][t] + p_sell["s_wind"][t] ==
                        p_grid_sell[t] + power_trade["seller"][t] + prev_trade["seller"][t])
        model.addConstr(power_trade["seller"][t] == 0)
        model.addConstr(prev_trade["seller"][t] == 0)

    # Set solver parameters (e.g., time limit, MIP gap)
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]

    # Execute the optimization model
    model.optimize()

    # Write errorfile if optimization problem is infeasible or unbounded
    if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:
        model.computeIIS()
        f = open('errorfile_hp.txt', 'w')
        f.write(str(datetime.datetime.now()) + '\nThe following constraint(s) cannot be satisfied:\n')
        for c in model.getConstrs():
            if c.IISConstr:
                f.write('%s' % c.constrName)
                f.write('\n')
        f.close()

    # Retrieve results
    res_y = {}
    res_power = {}
    res_heat = {}
    res_soc = {}

    for dev in heater:
        res_power[dev] = {t: power[dev][t].X for t in time_steps}
        res_heat[dev] = {t: heat[dev][t].X for t in time_steps}
    for dev in renewables:
        res_power[dev] = {t: power[dev][t].X for t in time_steps}
    for dev in storage:
        res_soc[dev] = {t: soc[dev][t].X for t in time_steps}

    res_p_imp = {}
    res_p_imp["p_imp"] = {t: p_imp[t].X for t in time_steps}
    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {t: p_ch[dev][t].X for t in time_steps}
        res_p_dch[dev] = {t: p_dch[dev][t].X for t in time_steps}

    res_c_dem = {}
    res_rev = {}
    res_soc_nom = {dev: soc_nom[dev] for dev in storage}

    res_p_use = {}
    res_p_sell = {}
    for dev in renewables:
        res_p_use[dev] = {t: p_use[dev][t].X for t in time_steps}
        res_p_sell[dev] = {t: p_sell[dev][t].X for t in time_steps}

    res_p_grid_buy = {(t): p_grid_buy[t].X for t in time_steps}
    res_p_grid_sell = {(t): p_grid_sell[t].X for t in time_steps}
    res_p_trade = {(t): power_trade["buyer"][t].X + power_trade["seller"][t].X for t in time_steps}
    res_prev_trade = {(t): prev_trade["buyer"][t].X + prev_trade["seller"][t].X for t in time_steps}

    obj = model.objVal
    print("Obj: " + str(model.objVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()

    # Return results
    return {"res_y": res_y, "res_power": res_power, "res_heat": res_heat, "res_soc": res_soc,
            "res_p_imp": res_p_imp, "res_p_ch": res_p_ch, "res_p_dch": res_p_dch,
            "res_p_use": res_p_use, "res_p_sell": res_p_sell, "obj": obj,
            "res_c_dem": res_c_dem, "res_rev": res_rev, "res_soc_nom": res_soc_nom,
            "objVal": objVal, "runtime": runtime, "soc_init_rh": soc_init_rh,
            "res_p_grid_buy": res_p_grid_buy, "res_p_grid_sell": res_p_grid_sell,
            "res_p_trade": res_p_trade, "res_prev_trade": res_prev_trade}