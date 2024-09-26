#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subproblem optimization model for hierarchical district control
@author: Joel Schölzel based on Sarah Henn and Thomas Schütz
"""

from __future__ import division

import gurobipy as gp
import numpy as np
import datetime
from itertools import islice


def compute_opti(node, params, par_rh, init_val, n_opt, options, matched_bids_info, prev_traded, r,
                 is_buying, delta_price, block_length, opti_res, opti_bes_res_buyer):

    """Optimization model for the buyers and sellers participating in the negotiation. It is the same as the initial
    optimization model run in opti_bes, but with the difference that there are additional constraints and variables
    regarding trading price and power.

    Returns: opti_bes_res (dict): Dictionary containing the results of the optimization model.
      """

    # Define subsets
    heater = ("boiler", "chp", "eh", "hp35", "hp55")
    storage = ("bat", "tes", "ev")
    solar = ("pv",)    #, "stc"
    device = ("boiler", "chp", "eh", "hp35", "hp55", "bat", "tes", "pv")

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    if options["enhanced_horizon"]:
        time_steps = par_rh["time_steps"][n_opt]
    else:
        time_steps = par_rh["time_steps"][n_opt][0:block_length]

    # Durations of time steps # for aggregated RH
    #duration = par_rh["duration"][n_opt]

    # get relevant input data (elec, dhw, heat) for prediction horizon
    discretization_input_data = options["discretization_input_data"]

    # get elec, heat etc. for optimization n_opt
    demands = {}
    elec = {}
    dhw = {}
    heat = {}
    COP35 = {}
    COP55 = {}
    PV_GEN = {}
    #EV_AVAIL = {}
    #EV_DEM_LEAVE = {}

    for i in range(len(time_steps)):
        param00 = time_steps[i]
        param01 = int(dt[param00]/discretization_input_data)
        param02 = int(par_rh["org_time_steps"][n_opt][i]/discretization_input_data)
        if param01 < 1:
            raise ValueError("Interpolation of input data necessary")
        elif options["number_typeWeeks"] == 0:
            elec[param00] = np.mean([node["elec"][param02], node["elec"][param02 + param01 - 1]])
            heat[param00] = np.mean([node["heat"][param02], node["heat"][param02 + param01 - 1]])
            dhw[param00] = np.mean([node["dhw"][param02], node["dhw"][param02 + param01 - 1]])
            COP35[param00] = np.mean([node["devs"]["COP_sh35"][param02], node["devs"]["COP_sh35"][param02 + param01 - 1]])
            COP55[param00] = np.mean([node["devs"]["COP_sh55"][param02], node["devs"]["COP_sh55"][param02 + param01 - 1]])
            PV_GEN[param00] = np.mean([node["pv_power"][param02], node["pv_power"][param02 + param01 - 1]])
            #EV_AVAIL[param00] = np.mean([node["ev_avail"][param02], node["ev_avail"][param02 + param01 - 1]])
            #EV_DEM_LEAVE[param00] = np.mean([node["ev_dem_leave"][param02], node["ev_dem_leave"][param02 + param01 - 1]])
        else:
            elec[param00] = np.mean([node["elec_appended"][param02], node["elec_appended"][param02 + param01 - 1]])
            heat[param00] = np.mean([node["heat_appended"][param02], node["heat_appended"][param02 + param01 - 1]])
            dhw[param00] = np.mean([node["dhw_appended"][param02], node["dhw_appended"][param02 + param01 - 1]])
            COP35[param00] = np.mean([node["devs"]["COP_sh35_appended"][param02], node["devs"]["COP_sh35_appended"][param02 + param01 - 1]])
            COP55[param00] = np.mean([node["devs"]["COP_sh55_appended"][param02], node["devs"]["COP_sh55_appended"][param02 + param01 - 1]])
            PV_GEN[param00] = np.mean([node["pv_power_appended"][param02], node["pv_power_appended"][param02 + param01 - 1]])
            #EV_AVAIL[param00] = np.mean([node["ev_avail_appended"][param02], node["ev_avail_appended"][param02 + param01 - 1]])
            #EV_DEM_LEAVE[param00] = np.mean([node["ev_dem_leave_appended"][param02], node["ev_dem_leave_appended"][param02 + param01 - 1]])

        demands = {
        "elec": elec,
        "heat": heat,
        "dhw": dhw,
        "COP35": COP35,
        "COP55": COP55,
        "PV_GEN": PV_GEN,
        #"EV_AVAIL": EV_AVAIL,
        #"EV_DEM_LEAVE": EV_DEM_LEAVE,
        }

    model = gp.Model("Operation computation")

    # Initialization: only if initial values have been generated in previous prediction horizon
    soc_init_rh = {}
    if bool(init_val) == True:
        # initial SOCs
        # Buildings
        for dev in storage:
            soc_init_rh[dev] = init_val["soc"][dev]

    if par_rh["month"] == 0:
        par_rh["month"] = par_rh["month"] + 1

    # Define variables
    # Costs and Revenues
    c_dem = {dev: model.addVar(vtype="C", name="c_dem_" + dev)
             for dev in ("boiler", "chp", "grid")}

    revenue = {dev: model.addVar(vtype="C", name="revenue_" + dev)
               for dev in ("grid", "chp", "pv")}

    cost_trade = model.addVar(vtype="C", name="cost_trade")

    revenue_trade = model.addVar(vtype="C", name="revenue_trade")

    # SOC, charging, discharging, power and heat
    soc = {}
    p_ch = {}
    p_dch = {}
    power = {}
    heat = {}
    dhw = {}
    for dev in storage:  # All storage devices
        soc[dev] = {}
        p_ch[dev] = {}
        p_dch[dev] = {}
        for t in time_steps:  # All time steps of all days
            soc[dev][t] = model.addVar(vtype="C", lb=0, name="SOC_" + dev + "_" + str(t))
            p_ch[dev][t] = model.addVar(vtype="C", lb=0, name="P_ch_" + dev + "_" + str(t))
            p_dch[dev][t] = model.addVar(vtype="C", lb=0, name="P_dch_" + dev + "_" + str(t))

    for dev in ["hp35", "hp55", "chp", "boiler"]:
        power[dev] = {}
        heat[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))
            heat[dev][t] = model.addVar(vtype="C", lb=0, name="Q_" + dev + "_" + str(t))

    for dev in ["eh"]:
        heat[dev] = {}
        power[dev] = {}
        for t in time_steps:
            heat[dev][t] = model.addVar(vtype="C", name="Q_" + dev + "_" + str(t))
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    for dev in ["pv"]:
        power[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # heating system and temperatures
    t_tes = {}
    t_tes_sup = {}
    t_sup = {}
    loss_tes = {}
    greater_0 = {}
    for t in time_steps:
        t_tes[t] = model.addVar(vtype="C", name="T_TES_" + str(t)) # Average Temperature of Tes after discharging
        t_tes_sup[t] = model.addVar(vtype="C", name="T_TES_" + str(t)) # Average Temperature of Tes before discharging
        t_sup[t] = model.addVar(vtype="C", name="T_supply_" + str(t))  # Supply Temperature of the heatpump
        loss_tes[t] = model.addVar(vtype="C", name="Q_loss_tes_" + str(t))  # Energy losses in the TES
        greater_0[t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="Demand_greater_0_" + str(t))
    
    # Initial storage temperature at the start of the month
    #if node["devs"]["hp55"]["cap"] > 0:
    t_tes_init = 40 + 273.15
    #else: 
        #t_tes_init = 30 + 273.15
    # Storage temperature at the beginning of n_opt
    if bool(init_val) == True:
        t_tes_init_rh = init_val["t_tes"]

    # maping storage sizes
    soc_nom = {}
    for dev in storage:
        soc_nom[dev] = node["devs"][dev]["cap"]

    # Storage initial SOC's
    soc_init = {}
    soc_init["tes"] = soc_nom["tes"] * 0.1  # kWh   Initial SOC TES
    soc_init["bat"] = soc_nom["bat"] * 0.1  # kWh   Initial SOC Battery
    soc_init["ev"] = soc_nom["ev"] * 0.75

    # VARIABLE FOR TRADING POWER
    power_trade = {}
    prev_trade = {}
    for peer in ["buyer", "seller"]:
        power_trade[peer] = {}
        prev_trade[peer] = {}
        for t in time_steps:
            power_trade[peer][t] = model.addVar(vtype="C", name="Power_trade_" + peer + "_" + str(t))
            prev_trade[peer][t] = model.addVar(vtype="C", name="Previous_power_trade_" + peer + "_" + str(t))

    # Import bid power quantity and bid price of matched trading partners
    quantity_bid_seller = {}
    quantity_bid_buyer = {}
    price_bid_buyer = {}
    price_bid_seller = {}

    # quantity and price of the buyer and seller is only set for block length
    if options["enhanced_horizon"]:
        for t in time_steps[0:block_length]:
            price_bid_buyer[t] = matched_bids_info[0][t][0]
            quantity_bid_buyer[t] = matched_bids_info[0][t][1]
            price_bid_seller[t] = matched_bids_info[1][t][0]
            quantity_bid_seller[t] = matched_bids_info[1][t][1]
        for t in time_steps[block_length:]:
            price_bid_buyer[t] = 0
            quantity_bid_buyer[t] = 0
            price_bid_seller[t] = 0
            quantity_bid_seller[t] = 0
    else:
        for t in time_steps:
            price_bid_buyer[t] = matched_bids_info[0][t][0]
            quantity_bid_buyer[t] = matched_bids_info[0][t][1]
            price_bid_seller[t] = matched_bids_info[1][t][0]
            quantity_bid_seller[t] = matched_bids_info[1][t][1]

    # Electricity imports, sold and self-used electricity
    p_imp = {}
    p_use = {}
    p_sell = {}
    y_imp = {}
    p_grid_buy = {}
    p_grid_sell = {}
    for t in time_steps:
        p_imp[t] = model.addVar(vtype="C", name="P_imp_" + str(t))
        p_grid_buy[t] = model.addVar(vtype="C", name="P_grid_buy" + str(t))
        p_grid_sell[t] = model.addVar(vtype="C", name="P_grid_sell" + str(t))
        y_imp[t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_imp_exp_" + str(t))

    for dev in ("chp", "pv"):
        p_use[dev] = {}
        p_sell[dev] = {}
        for t in time_steps:
            p_use[dev][t] = model.addVar(vtype="C", name="P_use_" + dev + "_" + str(t))
            p_sell[dev][t] = model.addVar(vtype="C", name="P_sell_" + dev + "_" + str(t))

    # Gas imports to devices
    gas = {}
    for dev in ["chp", "boiler"]:
        gas[dev] = {}
        for t in time_steps:
            gas[dev][t] = model.addVar(vtype="C", name="gas" + dev + "_" + str(t))

    # Activation decision variables
    # binary variable for each house to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["bat", "house_load"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # Update
    model.update()
    # Objective
    if is_buying:
        model.setObjective(c_dem["grid"] - revenue["grid"] + c_dem["boiler"]
                       + c_dem["chp"] + cost_trade, gp.GRB.MINIMIZE)
    else:
        model.setObjective(c_dem["grid"] - revenue["grid"] + c_dem["boiler"]
                       + c_dem["chp"] - revenue_trade, gp.GRB.MINIMIZE)

    ####### Define constraints

    # --------------- ECONOMIC CONSTRAINTS ---------------

    # Demand related costs (gas)
    for dev in ("boiler", "chp"):
        model.addConstr(c_dem[dev] == params["eco"]["gas"] * sum(gas[dev][t] for t in time_steps),
                        name="Demand_costs_" + dev)

    # Demand related costs (electricity)
    dev = "grid"
    model.addConstr(c_dem[dev] == sum(p_grid_buy[t] * params["eco"]["pr", "el"] for t in time_steps),
                    name="Demand_costs_" + dev)

    # Revenues for selling electricity to the grid / neighborhood
    #for dev in ("chp", "pv"):
    dev = "grid"
    model.addConstr(revenue[dev] == sum(p_grid_sell[t] * params["eco"]["sell" + "_pv"] for t in time_steps),
                        name="Feed_in_rev_" + dev)

    # Costs and revenues of trade
    if is_buying:
        model.addConstr(cost_trade == sum(power_trade["buyer"][t] * delta_price[t] for t in time_steps),
                        name="Power_trade_costs")
    else:
        model.addConstr(revenue_trade == sum(power_trade["seller"][t] * delta_price[t] for t in time_steps),
                        name="Power_trade_revenue")

    # --------------- TECHNICAL CONSTRAINTS ---------------

    # Determine nominal heat at every timestep
    for t in time_steps:
        for dev in heater:
            if dev == "eh":
                model.addConstr(power[dev][t] <= node["devs"][dev]["cap"],
                                name="Max_heat_operation_" + dev)
            else:
                model.addConstr(heat[dev][t] <= node["devs"][dev]["cap"],
                                name="Max_heat_operation_" + dev)

    ### Devices operation
    # Heat output between mod_lvl*Q_nom and Q_nom (P_nom for heat pumps)
    # Power and Energy directly result from Heat output
    for t in time_steps:
        # Heatpumps
        dev = "hp35"
        model.addConstr(heat[dev][t] == power[dev][t] * demands["COP35"][t],
                        name="Power_equation_" + dev + "_" + str(t))

        model.addConstr(heat[dev][t] >= power[dev][t] * demands["COP35"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))

        dev = "hp55"
        model.addConstr(heat[dev][t] == power[dev][t] * demands["COP55"][t],
                        name="Power_equation_" + dev + "_" + str(t))

        model.addConstr(heat[dev][t] >= power[dev][t] * demands["COP55"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))

        # CHP
        model.addConstr(heat["chp"][t] == node["devs"]["chp"]["eta_th"] * gas["chp"][t],
                        name="heat_operation_chp_" + str(t))

        model.addConstr(power["chp"][t] == node["devs"]["chp"]["eta_el"] * gas["chp"][t],
                        name="Power_equation_" + dev + "_" + str(t))
        #model.addConstr(power["chp"][t] == node["devs"]["chp"]["eta_el"] * gas["chp"][t] * node["devs"]["chp"]["mod_lvl"],
        #                name="Min_power_equation_chp_" + str(t))

        # BOILER
        dev = "boiler"
        model.addConstr(heat["boiler"][t] == node["devs"]["boiler"]["eta_th"] * gas["boiler"][t],
                        name="Power_equation_" + dev + "_" + str(t))

        # EH (electrical heater)
        # The EH is only used in combination with HPs to increase DHW temperature.
        if node["devs"]["eh"]["cap"] > 0:
            # Get the max output temperature of the HP, depending on the HP type (HP35 or HP55).
            if node["devs"]["hp35"]["cap"] > 0:
                hp_temp = 35
            elif node["devs"]["hp55"]["cap"] > 0:
                hp_temp = 55
            else:
                # The EH should only exist, when a HP is used. Therefore, either HP35 or HP55 should be found.
                raise Exception("EH capacity is not 0 but no HP is found.")

            # The HP heats from 25°C to the maximum temperature hp_temp.
            # EH provides the remaining heat required to raise the DHW temperature to 60°C.
            model.addConstr(heat["eh"][t] == (60 - hp_temp) / (60 - 25) * demands["dhw"][t],
                            name="Heat_operation_EH_" + str(t))

        # Degree of efficiency of EH is 1
        model.addConstr(power["eh"][t] == heat["eh"][t], name="Power_equation_EH_" + str(t))

    # Solar components
    for dev in solar:
        for t in time_steps:
            model.addConstr(power[dev][t] == demands["PV_GEN"][t],
                            name="Solar_electrical_" + dev + "_" + str(t))

    # Heating System
    #if options["mpc"]:  
    if node["devs"]["chp"]["cap"] != 0:
        m_flow = 0.8 # in kg/s 
    else:
        m_flow = 0.2 # in kg/s 
    t_flow_min = 37 + 273.15 #TODO ??
    cp = params["phy"]["c_w"]
    big_m = 100000
    for t in time_steps:
        # Necessary Supply Temperature
        model.addConstr(demands["heat"][t] == (t_sup[t] - t_flow_min) * cp * m_flow,
                            name="T_supply_HP_" + str(t))
        # Binary that indicates existing Demand
        model.addConstr(greater_0[t] * big_m >= demands["heat"][t], 
                        name="HeatDem_greater_0_" + str(t))
        # If ther is heat demand, the storage average temperature must be higher than the supply temperature. Assures that supply can be fulfilled
        #model.addGenConstrIndicator(greater_0[t], 1, (t_tes_sup[t] >= t_sup[t]), name="Meet_T_sup" + str(t))
        model.addGenConstrIndicator(greater_0[t], 1, (t_tes[t] >= t_sup[t]), name="Meet_T_sup" + str(t))

    # %% BUILDING STORAGES # %% DOMESTIC FLEXIBILITIES

    dev = "tes"
    eta_tes = node["devs"][dev]["eta_tes"]
    eta_ch = node["devs"][dev]["eta_ch"]
    eta_dch = node["devs"][dev]["eta_dch"]
    t_tes_min = 18 + 273.15
    t_tes_max = 55 + 273.15
    rho = params["phy"]["rho_w"]
    #vol = 0.188 #in m3 TODO Checken, welches Volumen genau
    vol = (3600 * node["devs"]["tes"]["cap"])/(cp * rho * (t_tes_max - t_tes_min))
    for t in time_steps:
        #if options["mpc"]:
        # Initial temperature is the temperature at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            t_tes_prev = t_tes_init_rh
        elif t == par_rh["month_start"][par_rh["month"]]:
            t_tes_prev = t_tes_init
        else:
            t_tes_prev = t_tes[t - 1]
            

        # Energy balance of the TES
        model.addConstr((t_tes[t] - t_tes_prev) * vol * rho * cp / 3600 == dt[t] * (eta_ch * p_ch[dev][t] - eta_dch * p_dch[dev][t] - loss_tes[t]) , 
                        name="Storage_bal" + dev + "_" + str(t))
        
        #model.addConstr((t_tes_sup[t] - t_tes_prev) * vol * rho * cp / 3600 == dt[t] * (eta_ch * p_ch[dev][t] - loss_tes[t]) , 
                        #name="Storage_ch_" + dev + "_" + str(t))
        #model.addConstr((t_tes[t] - t_tes_sup[t]) * vol * rho * cp / 3600 == dt[t] * (- eta_dch * p_dch[dev][t]), 
                        #name="Storage_dch_" + dev + "_" + str(t))
        # # Heat loss
        model.addConstr(loss_tes[t] == (t_tes_prev - t_tes_min) * (1 - eta_tes) * vol * rho * cp / 3600, 
                        name="loss_tes" + str(t))
        # SOC 
        model.addConstr(soc[dev][t] == (t_tes[t] - t_tes_min) / (t_tes_max - t_tes_min), 
                        name="SOC" + str(t))
        # Min T
        #model.addConstr(t_tes_sup[t] >= t_tes_min, 
                        #name="Min_T_tes_sup_" + str(t))
        # Max T
        #model.addConstr(t_tes_sup[t] <= t_tes_max, 
                        #name="Max_T_sup_tes_" + str(t))
        # Min T
        model.addConstr(t_tes[t] >= t_tes_min, 
                        name="Min_T_tes" + str(t))
        # Max T
        model.addConstr(t_tes[t] <= t_tes_max, 
                        name="Max_T_tes" + str(t))
        # TES charging
        model.addConstr(p_ch[dev][t] == eta_ch * (heat["chp"][t] + heat["hp35"][t] + heat["hp55"][t] + heat["boiler"][t]+ heat["eh"][t]),
                        name="Heat_charging_" + str(t))
        # TES discharging
        model.addConstr(p_dch[dev][t] == (1 / eta_dch) * (demands["heat"][t] + demands["dhw"][t]),
                        name="Heat_discharging_" + str(t))
        """
        else:
            # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
            if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init_rh[dev]
            elif t == par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init[dev]
            else:
                soc_prev = soc[dev][t - 1]

            # Maximal charging
            model.addConstr(p_ch[dev][t] == eta_ch * (heat["chp"][t] + heat["hp35"][t] + heat["hp55"][t] + heat["boiler"][t]
                                                    + heat["eh"][t]),
                            name="Heat_charging_" + str(t))
            # Maximal discharging
            model.addConstr(p_dch[dev][t] == (1 / eta_dch) * (demands["heat"][t] + demands["dhw"][t]),
                            name="Heat_discharging_" + str(t))

            # Minimal and maximal soc
            model.addConstr(soc["tes"][t] <= soc_nom["tes"], name="max_cap_tes_" + str(t))
            model.addConstr(soc["tes"][t] >= node["devs"]["tes"]["min_soc"] * soc_nom["tes"], name="min_cap_" + str(t))

            # SOC coupled over all times steps (Energy amount balance, kWh)
            model.addConstr(soc[dev][t] == soc_prev * eta_tes + dt[t] * (p_ch[dev][t] - p_dch[dev][t]),
                            name="Storage_bal_" + dev + "_" + str(t))

            # soc at the end is the same like at the beginning: in this opti not needed
            # since constraint for block bid quantity is added
            # if t == last_time_step:
            #    model.addConstr(soc[device][t] == soc_init[device],
            #                    name="End_TES_Storage_" + str(t))
        """

    dev = "bat"
    k_loss = node["devs"][dev]["k_loss"]
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]
        else:
            soc_prev = soc[dev][t - 1]

        # Maximal charging
        model.addConstr(p_ch["bat"][t] <= y["bat"][t] * node["devs"]["bat"]["cap"] * node["devs"]["bat"]["max_ch"],
                        name="max_ch_bat_" + str(t))
        # Maximal discharging
        model.addConstr(p_dch["bat"][t] <= (1 - y["bat"][t]) * node["devs"]["bat"]["cap"] * node["devs"]["bat"]["max_dch"],
                        name="max_dch_bat_" + str(t))

        # Minimal and maximal soc
        model.addConstr(soc["bat"][t] <= node["devs"]["bat"]["max_soc"] * node["devs"]["bat"]["cap"],
                        name="max_soc_bat_" + str(t))
        model.addConstr(soc["bat"][t] >= node["devs"]["bat"]["min_soc"] * node["devs"]["bat"]["cap"],
                        name="max_soc_bat_" + str(t))

        # SOC coupled over all times steps (Energy amount balance, kWh)
        model.addConstr(soc[dev][t] == (1 - k_loss) * soc_prev +
                        dt[t] * (node["devs"][dev]["eta_bat"] * p_ch[dev][t] - 1 / node["devs"][dev]["eta_bat"] *
                              p_dch[dev][t]),
                        name="Storage_balance_" + dev + "_" + str(t))

    """
    # %% EV CONSTRAINTS CONSTRAINTS
    dev = "ev"
    # Energy balance
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]
        else:
            soc_prev = soc[dev][t - 1]

        model.addConstr(soc[dev][t] == soc_prev
                        + p_ch[dev][t] * node["devs"][dev]["eta_ch_ev"] * dt[t]
                        - p_dch[dev][t] / node["devs"][dev]["eta_dch_ev"] * dt[t]
                        - demands["EV_DEM_LEAVE"][t])

        model.addConstr(p_dch[dev][t] <= demands["EV_AVAIL"][t] * node["devs"][dev]["max_dch_ev"])
        model.addConstr(p_ch[dev][t] <= demands["EV_AVAIL"][t] * node["devs"][dev]["max_ch_ev"])

        model.addConstr(p_dch[dev][t] <= y[dev][t] * node["devs"][dev]["max_dch_ev"],
                        name="Binary1_ev" + "_" + str(t))
        model.addConstr(p_ch[dev][t] <= (1 - y[dev][t]) * node["devs"][dev]["max_ch_ev"],
                        name="Binary2_ev" + "_" + str(t))

        model.addConstr(soc[dev][t] >= node["devs"][dev]["min_soc"] * node["devs"][dev]["cap"])
        model.addConstr(soc[dev][t] <= node["devs"][dev]["max_soc"] * node["devs"][dev]["cap"])
    """

    for t in time_steps:
        # Electricity balance (house)
        model.addConstr(demands["elec"][t] + p_ch["bat"][t] - p_dch["bat"][t]
                        + power["hp35"][t] + power["hp55"][t] + power["eh"][t] - p_use["chp"][t] - p_use["pv"][t]
                        == p_imp[t],
                        name="Electricity_balance_" + str(t))
        # Split CHP and PV generation into self-consumed and sold powers
        for dev in ("chp", "pv"):
            model.addConstr(p_sell[dev][t] + p_use[dev][t] == power[dev][t],
                            name="power=sell+use_" + dev + "_" + str(t))
        # SOC and the end time step of block bid == SOC of opti with prediction horizon
        if t == time_steps[-1]:
            for dev in ("bat", "tes"):
                model.addConstr(soc[dev][t] == opti_res[3][dev][t], name="soc_bb=soc_ph")
        #"""
        if is_buying:
            model.addConstr(p_imp[t] == p_grid_buy[t] + power_trade["buyer"][t] + prev_trade["buyer"][t],
                            name="import=grid+trade+prev_" + str(t))
            model.addConstr(prev_traded["buy"][t] == prev_trade["buyer"][t], name="prev_trade_sell==0_" + str(t))
            model.addConstr(opti_res[18][t] == p_grid_sell[t], name="p_grid_sell==0_" + str(t))
            model.addConstr(prev_traded["sell"][t]  == prev_trade["seller"][t], name="prev_trade_sell==0_" + str(t))
            # power the buyer can trade is limited by the quantity the seller is willing to sell
            model.addConstr(power_trade["buyer"][t] <= quantity_bid_seller[t], name="max_Power_trade_buyer")
            model.addConstr(power_trade["buyer"][t] >= 0, name="min_Power_trade_buyer")
        else:
            model.addConstr(p_sell["chp"][t] + p_sell["pv"][t] == p_grid_sell[t] + power_trade["seller"][t]
                            + prev_trade["seller"][t],
                                name="sold=grid+trade+prev_" + str(t))
            model.addConstr(prev_traded["sell"][t] == prev_trade["seller"][t], name="prev_trade_buy==0_" + str(t))
            model.addConstr(opti_res[17][t] == p_grid_buy[t], name="p_grid_buy==0_" + str(t))
            model.addConstr(prev_traded["buy"][t] == prev_trade["buyer"][t], name="prev_trade_buy==0_" + str(t))
            #
            model.addConstr(power_trade["seller"][t] <= opti_bes_res_buyer["res_power_trade"][t],
                            name="max_Power_trade_seller")
            model.addConstr(power_trade["seller"][t] >= 0, name="min_Power_trade_seller_1")
            if quantity_bid_seller[t] <= opti_bes_res_buyer["res_power_trade"][t] and quantity_bid_seller[t] != 0:
                model.addConstr(power_trade["seller"][t] >= quantity_bid_seller[t], name="min_Power_trade_seller_2")
            

        # for inflexible market participants with buy and sell quantities in a bidding period
        if is_buying:
            if matched_bids_info[0]["ignored_demand"] == True:
                model.addConstr(p_imp[t] == opti_res[4]["p_imp"][t], name="A1")
                model.addConstr(p_sell["chp"][t] == opti_res[8]["chp"][t], name="A2")
                model.addConstr(p_sell["pv"][t] == opti_res[8]["pv"][t], name="A3")
        else:
            if matched_bids_info[1]["ignored_demand"] == True:
                model.addConstr(p_imp[t] == opti_res[4]["p_imp"][t], name="B1")
                model.addConstr(p_sell["chp"][t] == opti_res[8]["chp"][t], name="B2")
                model.addConstr(p_sell["pv"][t] == opti_res[8]["pv"][t], name="B3")

    if is_buying:
        # Trading quantity during negotiation is limited by the bid quantity
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) <= sum(quantity_bid_buyer.values()),
                        name="sum_p_buy")
        # Allow the operation to be adjusted --> operation becomes less energy efficient
        #model.addConstr(sum(p_imp[t] for t in time_steps) <= sum(opti_res[4]["p_imp"][t] for t in time_steps)*1.2,
        #                name="sum_p_imp")
        # todo: Ineffizienz als Sensitivitätsanalyse
        ## Buyer is not allowed to trade a sell quantity
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) == 0,
                        name="sum_p_sell")
    else:
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) == 0,
                        name="sum_p_buy")
        #model.addConstr(sum(p_sell["pv"][t] for t in time_steps) <= sum(opti_res[8]["pv"][t]for t in time_steps)*1.2,
        #                name="sum_p_sell_pv")
        #model.addConstr(sum(p_sell["chp"][t] for t in time_steps) <= sum(opti_res[8]["chp"][t]for t in time_steps)*1.2,
        #                name="sum_p_sell_chp")
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) <= sum(quantity_bid_seller.values()),
                        name="sum_p_sell")
        for t in time_steps:
            model.addConstr(p_sell["chp"][t] <= max(opti_res[8]["chp"][t]for t in time_steps), f"MaxConstraint_{t}")

    #"""
    """
    # Old version:

    if is_buying:
        model.addConstr(p_imp[t] == p_grid_buy[t] + power_trade["buyer"][t] + prev_trade["buyer"][t],
                        name="import=grid+trade+prev_" + str(t))
        model.addConstr(prev_traded[t] == prev_trade["buyer"][t], name="prev_trade_sell==0_" + str(t))
        model.addConstr(0 == p_grid_sell[t], name="p_grid_sell==0_" + str(t))
        model.addConstr(0 == prev_trade["seller"][t], name="prev_trade_sell==0_" + str(t))
        # power the buyer can trade is limited by the quantity the seller is willing to sell
        model.addConstr(power_trade["buyer"][t] <= quantity_bid_seller[t], name="max_Power_trade_buyer")
        model.addConstr(power_trade["buyer"][t] >= 0, name="min_Power_trade_buyer")
    else:
        model.addConstr(p_sell["chp"][t] + p_sell["pv"][t] == p_grid_sell[t] + power_trade["seller"][t]
                        + prev_trade["seller"][t],
                            name="sold=grid+trade+prev_" + str(t))
        model.addConstr(prev_traded[t] == prev_trade["seller"][t], name="prev_trade_buy==0_" + str(t))
        model.addConstr(0 == p_grid_buy[t], name="p_grid_buy==0_" + str(t))
        model.addConstr(0 == prev_trade["buyer"][t], name="prev_trade_buy==0_" + str(t))
        #
        model.addConstr(power_trade["seller"][t] <= opti_bes_res_buyer["res_power_trade"][t],
                        name="max_Power_trade_seller")
        model.addConstr(power_trade["seller"][t] >= 0, name="min_Power_trade_seller_1")
        if quantity_bid_seller[t] <= opti_bes_res_buyer["res_power_trade"][t] and quantity_bid_seller[t] != 0:
            model.addConstr(power_trade["seller"][t] >= quantity_bid_seller[t], name="min_Power_trade_seller_2")
        # ignored demand
        model.addConstr(p_imp[t] == opti_res[4]["p_imp"][t])

    if is_buying:
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) <= sum(quantity_bid_buyer.values()),
                        name="sum_p_imp")
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) == 0,
                        name="sum_p_sell")
    else:
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) == 0,
                        name="sum_p_imp")
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) <= sum(quantity_bid_seller.values()),
                        name="sum_p_sell")
    """
    p_rated = {}  # rated power of the house connection (elec)
    p_rated["MFH"] = 69282  # Kleinwandlermessung bis 100A
    p_rated["SFH/TH"] = 30484  # Direktmessung bis 44A

    if node["type"] == "MFH":
        ratedPower = p_rated["MFH"]
    else:
        ratedPower = p_rated["SFH/TH"]
    # Guarantee that just feed-in OR load is possible
    for t in time_steps:
        model.addConstr(y["house_load"][t] * ratedPower >= p_imp[t], name="binary_import_" + str(t))  #  + power_trade["buyer"][t]
        model.addConstr(p_imp[t] >= 0, name="p_imp>=0_" + str(t))
        model.addConstr((1 - y["house_load"][t]) * ratedPower >= p_sell["pv"][t] + p_sell["chp"][t],
                        name="binary_export_" + str(t))  #+ power_trade["seller"][t]



    # Set solver parameters
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]
    model.Params.NonConvex = 2

    # Execute calculation
    model.optimize()


    # Write errorfile if optimization problem is infeasible or unbounded
    if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:
        print(matched_bids_info[1]["bes_id"])
        print(matched_bids_info[0]["bes_id"])
        model.computeIIS()
        model.write("model.ilp")
        f = open('errorfile.txt', 'w')
        f.write(str(datetime.datetime.now()) + '\nThe following constraint(s) cannot be satisfied:\n')
        for c in model.getConstrs():
            if c.IISConstr:
                f.write('%s' % c.constrName)
                f.write('\n')
        f.close()

    epsilon = 1e-04
    # Retrieve results
    res_y = {}
    res_power = {}
    res_heat = {}
    res_soc = {}

    #for dev in ["bat", "house_load"]:
    #    res_y[dev] = {(t): y[dev][t].X for t in time_steps}

    for dev in ["hp35", "hp55", "chp", "boiler", "eh"]:
        res_power[dev] = {(t): power[dev][t].X for t in time_steps}
        res_heat[dev] = {(t): heat[dev][t].X for t in time_steps}
    for dev in ["pv"]:
        res_power[dev] = {(t): power[dev][t].X for t in time_steps}

    for dev in storage:
        res_soc[dev] = {(t): soc[dev][t].X for t in time_steps}

    res_p_imp = {(t): p_imp[t].X if p_imp[t].X >= epsilon else 0 for t in time_steps}
    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {(t): p_ch[dev][t].X if p_ch[dev][t].X >= epsilon else 0 for t in time_steps}
        res_p_dch[dev] = {(t): p_dch[dev][t].X if p_dch[dev][t].X >= epsilon else 0 for t in time_steps}

    #res_gas = {}
    #for dev in ["boiler", "chp"]:
    #    res_gas[dev] = {(t): gas[dev][t].X for t in control_horizon}
    res_gas_sum = {}
    res_gas_sum = {(t): sum(gas[dev][t].X for dev in ["boiler", "chp"]) for t in time_steps}


    res_c_dem = {}
    #for dev in ["boiler", "chp"]:
    #    res_c_dem[dev] = {(t): params["eco"]["gas"] * gas[dev][t].X for t in time_steps}
    #res_c_dem["grid"] = {(t): p_imp[t].X * params["eco"]["pr", "el"] for t in time_steps}

    res_rev = {}
    #for dev in ["pv", "chp"]:
    #    res_rev = {(t): p_sell[dev][t].X * params["eco"]["sell" + "_" + dev] for t in time_steps}

    res_soc_nom = {dev: soc_nom[dev] for dev in storage}

    res_p_use = {}
    res_p_sell = {}
    for dev in ("chp", "pv"):
        res_p_use[dev] = {(t): p_use[dev][t].X for t in time_steps}
        #res_p_sell[dev] = {(t): p_sell[dev][t].X for t in time_steps}
        res_p_sell[dev] = {t: p_sell[dev][t].X for t in time_steps}

    res_p_grid_buy = {(t): p_grid_buy[t].X for t in time_steps}
    res_p_grid_sell = {(t): p_grid_sell[t].X for t in time_steps}

    if is_buying:
        res_price_trade = {(t): delta_price[t] for t in time_steps}
        res_power_trade = {(t): power_trade["buyer"][t].X for t in time_steps}
        res_prev_trade = {(t): prev_trade["buyer"][t].X for t in time_steps}
    else:
        res_price_trade = {(t): delta_price[t] for t in time_steps}
        res_power_trade = {(t): power_trade["seller"][t].X for t in time_steps}
        res_prev_trade = {(t): prev_trade["seller"][t].X for t in time_steps}
    
    res_t_tes = {(t): t_tes[t].X for t in time_steps}
    #res_t_tes_sup = {(t): t_tes_sup[t].X for t in time_steps}
    res_t_sup = {(t): t_sup[t].X for t in time_steps}

    obj = model.ObjVal
    print("Obj: " + str(model.ObjVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()
    #        model.computeIIS()
     #       model.write("model.ilp")
     #       print('\nConstraints:')
     #       for c in model.getConstrs():
    #          if c.IISConstr:
    #                print('%s' % c.constrName)
    #        print('\nBounds:')
    #        for v in model.getVars():
    #            if v.IISLB > 0 :
    #                print('Lower bound: %s' % v.VarName)
    #            elif v.IISUB > 0:
    #                print('Upper bound: %s' % v.VarName)

    # Return results
    opti_bes_res = {
        "res_y": res_y,
        "res_power": res_power,
        "res_heat": res_heat,
        "res_soc": res_soc,
        "res_p_imp": res_p_imp,
        "res_p_ch": res_p_ch,
        "res_p_dch": res_p_dch,
        "res_p_use": res_p_use,
        "res_p_sell": res_p_sell,
        "res_gas_sum": res_gas_sum,
        "obj": obj,
        "res_c_dem": res_c_dem,
        "res_rev": res_rev,
        "res_soc_nom": res_soc_nom,
        #"node": node,
        "objVal": objVal,
        "runtime": runtime,
        "soc_init_rh": soc_init_rh,
        "res_gas_sum": res_gas_sum,
        "res_power_trade": res_power_trade,
        "res_price_trade": res_price_trade,
        "res_p_grid_buy": res_p_grid_buy,
        "res_p_grid_sell": res_p_grid_sell,
        "res_prev_trade": res_prev_trade,
        "res_t_tes": res_t_tes,
        #"res_t_tes_sup": res_t_tes_sup,
        "res_t_sup": res_t_sup
    }

    return opti_bes_res

def replace_opti_res(opti_res, opti_res_block_bid, par_rh, n_opt):

    control_horizon = []
    for t_ch in range(par_rh["n_hours"] - par_rh["n_hours_ov"]):
        control_horizon.append(par_rh["time_steps"][n_opt][t_ch]
        )

    for t in control_horizon:
        for dev in ["hp35", "hp55", "chp", "boiler", "eh"]:
            # power
            opti_res[1][dev][t] = opti_res_block_bid["res_power"][dev][t]
            # heat
            opti_res[2][dev][t] = opti_res_block_bid["res_heat"][dev][t]
        for dev in ["pv"]:
            # power
            opti_res[1][dev][t] = opti_res_block_bid["res_power"][dev][t]
        for dev in ["bat", "tes", "ev"]:
            # soc
            opti_res[3][dev][t] = opti_res_block_bid["res_soc"][dev][t]
            # ch
            opti_res[5][dev][t] = np.round(np.absolute(opti_res_block_bid["res_p_ch"][dev][t]), 5)
            # dch
            opti_res[6][dev][t] = np.round(np.absolute(opti_res_block_bid["res_p_dch"][dev][t]), 5)
        # p_imp
        opti_res[4]["p_imp"][t] = opti_res_block_bid["res_p_imp"][t]
        for dev in ["pv", "chp"]:
            opti_res[7][dev][t] = opti_res_block_bid["res_p_use"][dev][t]
            # p_sell
            opti_res[8][dev][t] = opti_res_block_bid["res_p_sell"][dev][t]
        opti_res[16][t] = opti_res_block_bid["res_gas_sum"][t]

    for t in control_horizon:
        opti_res[17][t] = opti_res_block_bid["res_p_grid_buy"][t]
        opti_res[18][t] = opti_res_block_bid["res_p_grid_sell"][t]
        opti_res[19][t] = opti_res_block_bid["res_power_trade"][t] + opti_res_block_bid["res_prev_trade"][t]
        opti_res[20][t] = opti_res_block_bid["res_prev_trade"][t]
        opti_res[21][t] = opti_res_block_bid["res_t_tes"][t]
        opti_res[22][t] = opti_res_block_bid["res_t_sup"][t]
        #opti_res[23][t] = opti_res_block_bid["res_t_tes_sup"][t]

    return opti_res

def compute_initial_values_block(nb_buildings, opti_res, last_time_step, length_block_bid):
    """
    Computes the SoC values for each BES at the last time step of the block bid
    for the current optimization step.
    First all SoC resulting from initial optimization (in opti_methods) are stored in a dict.
    Then, for each BES listed in transaction in nego_transactions, the SoC values of the buyer and seller are
    updated with the SoC resulting from the last time step of the negotiation optimization (in matching_negotiation).
    Returns:
    init_val_block: dict with SoC values of all BES at the last time step of the block bid for the
    current optimization step
    """
    init_val_block = {}
    # create dict to store initial values of all BES
    import random
    for n in range(nb_buildings):
        init_val_block["building_" + str(n)] = {}
        #init_val_block["building_" + str(n)]["t_tes"] = random.randint(30, 50) + 273.15
        init_val_block["building_" + str(n)]["t_tes"] = opti_res[n][21][last_time_step]
        #init_val_block["building_" + str(n)]["t_tes"] = opti_res[n][21][last_time_step]
        init_val_block["building_" + str(n)]["soc"] = {}
        # fill this dict with initial SoC values of first optimisation
        for dev in ["tes", "bat", "ev"]:
            init_val_block["building_" + str(n)]["soc"][dev] = opti_res[n][3][dev][last_time_step]

    ### ----------------------- Reduction of saved data ----------------------- ###

    for n in range(nb_buildings):
        for dev in ["hp35", "hp55", "chp", "boiler", "eh"]:
            # power
            opti_res[n][1][dev] = slice_dict(opti_res[n][1][dev], length_block_bid)
            # heat
            opti_res[n][2][dev] = slice_dict(opti_res[n][2][dev], length_block_bid)
        for dev in ["pv"]:
            # power
            opti_res[n][1][dev] = slice_dict(opti_res[n][1][dev], length_block_bid)
        for dev in ["bat", "tes", "ev"]:
            # soc
            opti_res[n][3][dev] = slice_dict(opti_res[n][3][dev], length_block_bid)
            # ch
            opti_res[n][5][dev] = slice_dict(opti_res[n][5][dev], length_block_bid)
            # dch
            opti_res[n][6][dev] = slice_dict(opti_res[n][6][dev], length_block_bid)
        # p_imp
        opti_res[n][4]["p_imp"] = slice_dict(opti_res[n][4], length_block_bid)
        for dev in ["pv", "chp"]:
            opti_res[n][7][dev] = slice_dict(opti_res[n][7][dev], length_block_bid)
            # p_sell
            opti_res[n][8][dev] = slice_dict(opti_res[n][8][dev], length_block_bid)
        #opti_res[n][16] = slice_dict(opti_res[n][16], length_block_bid)
        #opti_res[n][17] = slice_dict(opti_res[n][17], length_block_bid)
        #opti_res[n][18] = slice_dict(opti_res[n][18], length_block_bid)
        #opti_res[n][19] = slice_dict(opti_res[n][19], length_block_bid)

    return init_val_block

def slice_dict(d, timestep):
    # Convert dictionary to a list of tuples (key, value)
    items = list(d.items())
    # Slice the list of tuples
    sliced_items = items[:timestep]
    # Convert the sliced list of tuples back to a dictionary
    return dict(sliced_items)