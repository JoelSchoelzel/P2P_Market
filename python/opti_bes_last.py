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


def compute_opti_last(node, params, par_rh, building_param, init_val, n_opt, options, id, price_signal, available_supply,
                      trade_buyer, trade_seller, trade_cost_buyer, trade_revenue_seller):
    # Define subsets
    heater = ("boiler", "chp", "eh", "hp35", "hp55")
    storage = ("bat", "tes", "ev")
    solar = ("pv",)  # , "stc"
    device = ("boiler", "chp", "eh", "hp35", "hp55", "bat", "tes", "pv")

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    if options["block_bids"] == True:
        time_steps = par_rh["time_steps"][n_opt][0:options["block_length"]]
    else:
        time_steps = par_rh["time_steps"][n_opt]
    # Durations of time steps # for aggregated RH
    # duration = par_rh["duration"][n_opt]

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
    EV_AVAIL = {}
    EV_DEM_LEAVE = {}

    for i in range(len(time_steps)):
        param00 = time_steps[i]
        param01 = int(dt[param00] / discretization_input_data)
        param02 = int(par_rh["org_time_steps"][n_opt][i] / discretization_input_data)
        if param01 < 1:
            raise ValueError("Interpolation of input data necessary")
        elif options["number_typeWeeks"] == 0:
            elec[param00] = np.mean([node["elec"][param02], node["elec"][param02 + param01 - 1]])
            heat[param00] = np.mean([node["heat"][param02], node["heat"][param02 + param01 - 1]])
            dhw[param00] = np.mean([node["dhw"][param02], node["dhw"][param02 + param01 - 1]])
            COP35[param00] = np.mean(
                [node["devs"]["COP_sh35"][param02], node["devs"]["COP_sh35"][param02 + param01 - 1]])
            COP55[param00] = np.mean(
                [node["devs"]["COP_sh55"][param02], node["devs"]["COP_sh55"][param02 + param01 - 1]])
            PV_GEN[param00] = np.mean([node["pv_power"][param02], node["pv_power"][param02 + param01 - 1]])
            EV_AVAIL[param00] = np.mean([node["ev_avail"][param02], node["ev_avail"][param02 + param01 - 1]])
            EV_DEM_LEAVE[param00] = np.mean(
                [node["ev_dem_leave"][param02], node["ev_dem_leave"][param02 + param01 - 1]])
        else:
            elec[param00] = np.mean([node["elec_appended"][param02], node["elec_appended"][param02 + param01 - 1]])
            heat[param00] = np.mean([node["heat_appended"][param02], node["heat_appended"][param02 + param01 - 1]])
            dhw[param00] = np.mean([node["dhw_appended"][param02], node["dhw_appended"][param02 + param01 - 1]])
            COP35[param00] = np.mean(
                [node["devs"]["COP_sh35_appended"][param02], node["devs"]["COP_sh35_appended"][param02 + param01 - 1]])
            COP55[param00] = np.mean(
                [node["devs"]["COP_sh55_appended"][param02], node["devs"]["COP_sh55_appended"][param02 + param01 - 1]])
            PV_GEN[param00] = np.mean([node["pv_power_appended"][param02], node["pv_power_appended"][param02 + param01 - 1]])
            EV_AVAIL[param00] = np.mean(
                [node["ev_avail_appended"][param02], node["ev_avail_appended"][param02 + param01 - 1]])
            EV_DEM_LEAVE[param00] = np.mean(
                [node["ev_dem_leave_appended"][param02], node["ev_dem_leave_appended"][param02 + param01 - 1]])

        demands = {
            "elec": elec,
            "heat": heat,
            "dhw": dhw,
            "COP35": COP35,
            "COP55": COP55,
            "PV_GEN": PV_GEN,
            "EV_AVAIL": EV_AVAIL,
            "EV_DEM_LEAVE": EV_DEM_LEAVE,
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
               for dev in ("chp", "pv")}

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
            soc[dev][t] = model.addVar(vtype="C", name="SOC_" + dev + "_" + str(t))
            p_ch[dev][t] = model.addVar(vtype="C", name="P_ch_" + dev + "_" + str(t))
            p_dch[dev][t] = model.addVar(vtype="C", name="P_dch_" + dev + "_" + str(t))

    for dev in ["hp35", "hp55", "chp", "boiler"]:
        power[dev] = {}
        heat[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))
            heat[dev][t] = model.addVar(vtype="C", lb=0, name="Q_" + dev + "_" + str(t))

    for dev in ["eh"]:
        dhw[dev] = {}
        power[dev] = {}
        for t in time_steps:
            dhw[dev][t] = model.addVar(vtype="C", name="Q_" + dev + "_" + str(t))
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    for dev in ["pv"]:
        power[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # maping storage sizes
    soc_nom = {}
    for dev in storage:
        soc_nom[dev] = node["devs"][dev]["cap"]

    # Storage initial SOC's
    soc_init = {}
    soc_init["tes"] = soc_nom["tes"] * 0.5  # kWh   Initial SOC TES
    soc_init["bat"] = soc_nom["bat"] * 0.5  # kWh   Initial SOC Battery
    soc_init["ev"] = soc_nom["ev"] * 0.75

    # Electricity imports, sold and self-used electricity
    p_imp = {}
    p_use = {}
    p_sell = {}
    y_imp = {}
    for t in time_steps:
        p_imp[t] = model.addVar(vtype="C", name="P_imp_" + str(t))
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

    # mapping PV areas
    # area = {}
    # for dev in solar:
    #    area[dev] = building_param["modules"] * node["devs"]["pv"]["area_real"]

    # Activation decision variables
    # binary variable for each house to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["bat", "ev", "house_load"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # NEW: variables for trading with participants
    c_transaction = model.addVar(vtype="C", name="c_transaction")
    revenue_transaction = model.addVar(vtype="C", name="revenue_transaction")

    trade_amount_buyer = {}  # Amount of electricity bought by buyer
    trade_expense_buyer = {}  # Cost of buying electricity by buyer
    for t in time_steps:
        trade_amount_buyer[t] = {}
        trade_expense_buyer[t] = {}
        trade_amount_buyer[t][id] = trade_buyer[t].get(id, 0) if trade_buyer[t].get(id) else 0
        # trade_amount_buyer[t][id] = trade_buyer[t].get(id, trade_buyer[t].get(0, 0))
        trade_expense_buyer[t][id] = trade_cost_buyer[t].get(id, 0) if trade_cost_buyer[t].get(id) else 0



    # p_transaction_buyer_seller = {}  # Possible transaction amount of a buyer with a seller
    demand_from_seller = {}  # Total transaction amount of seller with all buyers
    # price_signal = {}  # Price signal of seller

    # Define decision variable p_transaction to optimize the trading amount between each buyer with each seller
    # and demand_from_seller to model the total demand of a seller from all buyers
    # for t in time_steps:
    #     p_transaction_buyer_seller[t] = model.addVar(vtype="C", name="P_transaction_" + str(t))
    #     demand_from_seller[t] = model.addVar(vtype="C", name="Total_demand_from_seller_" + str(t))

    # Update
    model.update()

    # Objective
    model.setObjective(c_dem["grid"] - revenue["pv"] - revenue["chp"] + c_dem["boiler"]
                       + c_dem["chp"] + c_transaction - revenue_transaction, gp.GRB.MINIMIZE)


    ####### Define constraints

    ##### Economic constraints

    # Demand related costs (gas)
    for dev in ("boiler", "chp"):
        # model.addConstr(c_dem[dev] == params["eco"]["gas", dev] * sum(gas[dev][t] for t in time_steps),
        #                name="Demand_costs_" + dev)
        model.addConstr(c_dem[dev] == params["eco"]["gas"] * sum(gas[dev][t] for t in time_steps),
                        name="Demand_costs_" + dev)

    # Constraint to keep empty bids at zero
    for t in time_steps:
        if id not in trade_buyer[t] and id not in trade_seller[t]:
            model.addConstr(p_imp[t] == 0)
            model.addConstr(p_sell["pv"][t] == 0)
            model.addConstr(p_sell["chp"][t] == 0)
        else: pass

    # Demand related costs (electricity)    # eco["b"]["el"] * eco["crf"]
    dev = "grid"
    model.addConstr(c_dem[dev] == sum((p_imp[t] - trade_amount_buyer[t][id]) * params["eco"]["pr", "el"] for t in time_steps),
                    name="Demand_costs_" + dev)

    # Revenues for selling electricity to the grid
    # for dev in ("chp", "pv"):
    #     model.addConstr(revenue[dev] == sum((p_sell[dev][t] - trade_seller[t].get(seller, 0)) * params["eco"]["sell" + "_" + dev] for t in time_steps),
    #                     name="Feed_in_rev_" + dev)

    # Revenues for selling electricity to the grid
    for dev in ("chp", "pv"):
        model.addConstr(revenue[dev] == sum((p_sell["chp"][t] + p_sell["pv"][t] - trade_seller[t].get(id, 0)) * params["eco"]["sell" + "_" + dev] for t in time_steps),
                        name="Feed_in_rev_" + dev)


    ### Constraints for trading with participants
    # Cost of buying electricity from participants
    model.addConstr(c_transaction == sum(trade_expense_buyer[t][id] for t in time_steps), name="Transaction_cost")

    # Revenue from selling electricity to participants
    model.addConstr(revenue_transaction == sum(trade_revenue_seller[t].get(id, 0) for t in time_steps), name="Transaction_revenue")

    # Demand and supply amount
    for t in time_steps:
        # Keep buyer as buyer even if it did not make any trade
        if id in trade_buyer[t] and trade_amount_buyer[t][id] == 0.0:
            model.addConstr(y["house_load"][t] == 1.0)
        else:
            pass
        model.addConstr(p_imp[t] >= trade_amount_buyer[t][id], name="linking_constraint_demand")
        #model.addConstr(p_sell["pv"][t] + p_sell["chp"][t] >= trade_seller[t].get(id, 0), name="linking_constraint_supply")
        model.addConstr(p_sell["pv"][t] + p_sell["chp"][t] == available_supply[t].get(id, 0), name="linking_constraint_supply")

    ###### Technical constraints

    # Determine nominal heat at every timestep
    for t in time_steps:
        for dev in heater:
            if dev == "eh":
                model.addConstr(power[dev][t] <= node["devs"][dev]["cap"])
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
        # TODO: Check need of mod_lvl
        model.addConstr(heat[dev][t] >= power[dev][t] * demands["COP35"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))

        dev = "hp55"
        model.addConstr(heat[dev][t] == power[dev][t] * demands["COP55"][t],
                        name="Power_equation_" + dev + "_" + str(t))
        # TODO: Check need of mod_lvl
        model.addConstr(heat[dev][t] >= power[dev][t] * demands["COP55"][t] * node["devs"][dev]["mod_lvl"],
                        name="Min_pow_operation_" + dev + "_" + str(t))

        # CHP
        model.addConstr(heat["chp"][t] == node["devs"]["chp"]["eta_th"] * gas["chp"][t],
                        name="heat_operation_chp_" + str(t))

        model.addConstr(power["chp"][t] == node["devs"]["chp"]["eta_el"] * gas["chp"][t],
                        name="Power_equation_" + dev + "_" + str(t))
        # TODO: Check need of mod_lvl
        # model.addConstr(power["chp"][t] == node["devs"]["chp"]["eta_el"] * gas["chp"][t] * node["devs"]["chp"]["mod_lvl"],
        #                name="Min_power_equation_chp_" + str(t))

        # BOILER
        dev = "boiler"
        model.addConstr(heat["boiler"][t] == node["devs"]["boiler"]["eta_th"] * gas["boiler"][t],
                        name="Power_equation_" + dev + "_" + str(t))

    # Solar components
    # for dev in solar:
    #    for t in time_steps:
    #        model.addConstr(power[dev][t] == node["pv_power"][t],
    #                        name="Solar_electrical_" + dev + "_" + str(t))

    # Solar components
    for dev in solar:
        for t in time_steps:
            model.addConstr(power[dev][t] == demands["PV_GEN"][t],
                            name="Solar_electrical_" + dev + "_" + str(t))
    # set solar to 0
    # for t in time_steps:
    #     model.addConstr(power["pv"][t] == 0, name="Solar_electrical_pv_" + str(t))


    # %% BUILDING STORAGES # %% DOMESTIC FLEXIBILITIES

    ## Nominal storage content (SOC)
    # for dev in storage:
    #    # Inits
    #    model.addConstr(soc_init[dev] <= soc_nom[dev], name="SOC_nom_inits_"+dev)

    # Minimal and maximal charging, discharging and soc

    dev = "tes"
    eta_tes = node["devs"][dev]["eta_tes"]
    eta_ch = node["devs"][dev]["eta_ch"]
    eta_dch = node["devs"][dev]["eta_dch"]
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]
        else:
            soc_prev = soc[dev][t - 1]

        # Maximal charging
        model.addConstr(
            p_ch[dev][t] == eta_ch * (heat["chp"][t] + heat["hp35"][t] + heat["hp55"][t] + heat["boiler"][t]),
            name="Heat_charging_" + str(t))
        # Maximal discharging
        model.addConstr(p_dch[dev][t] == (1 / eta_dch) * (demands["heat"][t] + 0.5 * demands["dhw"][t]),
                        name="Heat_discharging_" + str(t))

        # Minimal and maximal soc
        model.addConstr(soc["tes"][t] <= soc_nom["tes"], name="max_cap_tes_" + str(t))
        model.addConstr(soc["tes"][t] >= node["devs"]["tes"]["min_soc"] * soc_nom["tes"], name="min_cap_" + str(t))

        # SOC coupled over all times steps (Energy amount balance, kWh)
        model.addConstr(soc[dev][t] == soc_prev * eta_tes + dt[t] * (p_ch[dev][t] - p_dch[dev][t]),
                        name="Storage_bal_" + dev + "_" + str(t))

        # TODO: soc at the end is the same like at the beginning
        # if t == last_time_step:
        #    model.addConstr(soc[device][t] == soc_init[device],
        #                    name="End_TES_Storage_" + str(t))

    # eletric heater covers 50% of the dhw
    for t in time_steps:
        model.addConstr(dhw["eh"][t] == 0.5 * demands["dhw"][t], name="El_heater_act_" + str(t))

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
        model.addConstr(
            p_dch["bat"][t] <= (1 - y["bat"][t]) * node["devs"]["bat"]["cap"] * node["devs"]["bat"]["max_dch"],
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

        # TODO:
        # if t == last_time_step:
        #    model.addConstr(soc_dom[device][n][t] == soc_init[device][n])

        model.addConstr(p_dch[dev][t] <= demands["EV_AVAIL"][t] * node["devs"][dev]["max_dch_ev"])
        model.addConstr(p_ch[dev][t] <= demands["EV_AVAIL"][t] * node["devs"][dev]["max_ch_ev"])

        model.addConstr(p_dch[dev][t] <= y[dev][t] * node["devs"][dev]["max_dch_ev"],
                        name="Binary1_ev" + "_" + str(t))
        model.addConstr(p_ch[dev][t] <= (1 - y[dev][t]) * node["devs"][dev]["max_ch_ev"],
                        name="Binary2_ev" + "_" + str(t))

        model.addConstr(soc[dev][t] >= node["devs"][dev]["min_soc"] * node["devs"][dev]["cap"])
        model.addConstr(soc[dev][t] <= node["devs"][dev]["max_soc"] * node["devs"][dev]["cap"])

    # Electricity balance (house)
    for t in time_steps:
        model.addConstr(demands["elec"][t] + p_ch["bat"][t] - p_dch["bat"][t] + p_ch["ev"][t] - p_dch["ev"][t]
                        + power["hp35"][t] + power["hp55"][t] + power["eh"][t] - p_use["chp"][t] - p_use["pv"][t]
                        == p_imp[t],
                        name="Electricity_balance_" + str(t))

    # Guarantee that just feed-in OR load is possible
    # for t in time_steps:
    #    # TODO: net params
    #    model.addConstr(y["house_load"][t] * 43.5 >= p_imp[t])  # Big M Methode --> Methodik
    #    model.addConstr(p_imp[t] >= 0)
    #    model.addConstr((1 - y["house_load"][t]) * 43.5 >= p_sell["pv"][t] + p_sell["chp"][t])  # 43.5: max Leistung am Hausanschluss

    p_rated = {}  # rated power of the house connection (elec)
    p_rated["MFH"] = 69282  # Kleinwandlermessung bis 100A
    p_rated["SFH/TH"] = 30484  # Direktmessung bis 44A

    if node["type"] == "MFH":
        ratedPower = p_rated["MFH"]
    else:
        ratedPower = p_rated["SFH/TH"]

    for t in time_steps:
        # TODO: net params
        model.addConstr(y["house_load"][t] * ratedPower >= p_imp[t])  # Big M Methode --> Methodik
        model.addConstr(p_imp[t] >= 0)
        model.addConstr((1 - y["house_load"][t]) * ratedPower >= p_sell["pv"][t] + p_sell["chp"][t])

    # Split CHP and PV generation into self-consumed and sold powers
    for dev in ("chp", "pv"):
        for t in time_steps:
            model.addConstr(p_sell[dev][t] + p_use[dev][t] == power[dev][t],
                            name="power=sell+use_" + dev + "_" + str(t))

    # Set solver parameters
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]

    # Execute calculation
    model.optimize()
    #        model.write("model.ilp")

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
    for dev in ["bat", "ev", "house_load"]:
        res_y[dev] = {(t): y[dev][t].X for t in time_steps}
    for dev in ["hp35", "hp55", "chp", "boiler"]:
        res_power[dev] = {(t): power[dev][t].X for t in time_steps}
        res_heat[dev] = {(t): heat[dev][t].X for t in time_steps}
    for dev in ["pv"]:
        res_power[dev] = {(t): power[dev][t].X for t in time_steps}

    for dev in storage:
        res_soc[dev] = {(t): soc[dev][t].X
                        for t in time_steps}

    res_p_imp = {(t): p_imp[t].X for t in time_steps}
    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {(t): p_ch[dev][t].X for t in time_steps}
        res_p_dch[dev] = {(t): p_dch[dev][t].X for t in time_steps}

    res_gas = {}
    for dev in ["boiler", "chp"]:
        res_gas[dev] = {(t): gas[dev][t].X for t in time_steps}
    res_gas_sum = {}
    res_gas_sum = {(t): sum(gas[dev][t].X for dev in ["boiler", "chp"]) for t in time_steps}

    res_c_dem = {}
    for dev in ["boiler", "chp"]:
        res_c_dem[dev] = {(t): params["eco"]["gas"] * gas[dev][t].X for t in time_steps}

    # Buyer's amount to import from the grid
    res_power_from_grid = {(t): p_imp[t].X - trade_amount_buyer[t][id] for t in time_steps}

    # Cost of trading with the grid
    res_c_dem["grid"] = {(t): (p_imp[t].X - trade_amount_buyer[t][id]) * params["eco"]["pr", "el"] for t in time_steps}

    res_rev = {}
    for dev in ["pv", "chp"]:
        res_rev = {(t): p_sell[dev][t].X * params["eco"]["sell" + "_" + dev] for t in time_steps}

    # Seller's amount to inject into the grid
    res_power_to_grid = {(t): sum(p_sell[dev][t].X for dev in ["pv", "chp"]) - trade_seller[t].get(id, 0) for t in time_steps}

    # Revenue from trading with grid
    res_rev_grid = {(t): res_power_to_grid[t] * params["eco"]["sell_chp"] for t in time_steps}

    # Revenue from trading with participants
    #res_rev_trade = {(t): trade_revenue_seller[t] for t in time_steps}

    res_soc_nom = {dev: soc_nom[dev] for dev in storage}

    res_p_use = {}
    res_p_sell = {}
    for dev in ("chp", "pv"):
        res_p_use[dev] = {(t): p_use[dev][t].X for t in time_steps}
        res_p_sell[dev] = {(t): p_sell[dev][t].X for t in time_steps}

    # res_net_cost = {}
    # res_net_cost = {(t): (p_imp[t].X - p_transaction_buyer_seller[t].X) * params["eco"]["pr", "el"]
    #                 + p_transaction_buyer_seller[t].X * price_signal[t].get(seller, 0)
    #                 + gas["boiler"][t].X * params["eco"]["gas"] + gas["chp"][t].X * params["eco"]["gas"]
    #                 for t in time_steps}

    # Amount traded by each participant
    res_trade_buyer = {}
    res_trade_seller = {}
    res_trade_buyer = {(t): trade_amount_buyer[t][id] for t in time_steps}
    res_trade_seller = {(t): trade_seller[t].get(id, 0) for t in time_steps}

    res_price_signal = {(t): price_signal[t].get(id, 0) for t in time_steps}



    obj = model.ObjVal
    print("Obj: " + str(model.ObjVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()
    #        model.computeIIS()
    #        model.write("model.ilp")
    #        print('\nConstraints:')
    #        for c in model.getConstrs():
    #            if c.IISConstr:
    #                print('%s' % c.constrName)
    #        print('\nBounds:')
    #        for v in model.getVars():
    #            if v.IISLB > 0 :
    #                print('Lower bound: %s' % v.VarName)
    #            elif v.IISUB > 0:
    #                print('Upper bound: %s' % v.VarName)

    # Return results
    # return (res_y, res_power, res_heat, res_soc,
    #         res_p_imp, res_p_ch, res_p_dch, res_p_use, res_p_sell,
    #         obj, res_c_dem, res_rev, res_soc_nom, node,
    #         objVal, runtime, soc_init_rh, res_gas_sum, res_price_signal, res_p_transaction_buyer_seller)

    return (res_y, res_soc, res_p_imp, res_power_from_grid, res_c_dem, res_p_ch, res_p_dch, res_p_use, res_p_sell,
            res_power_to_grid, res_rev_grid, res_soc_nom, node, objVal, runtime, soc_init_rh, res_price_signal,
            res_trade_buyer, res_trade_seller)

def compute_initial_values_stack(buildings, soc_res, par_rh, n_opt):

    init_val = {}
    for n in range(buildings):
        init_val["building_" + str(n)] = {}
        init_val["building_" + str(n)]["soc"] = {}
        # initial SOCs
        for dev in ["tes", "bat", "ev"]:
            init_val["building_" + str(n)]["soc"][dev] = soc_res[n][dev][par_rh["hour_start"][n_opt] + par_rh["n_hours"] - par_rh["n_hours_ov"] - 1]

    return init_val