#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subproblem optimization model for hierarchical district control
@ based on opti_bes_negotiation.py and opti_css
"""

from __future__ import division

import gurobipy as gp
import numpy as np
import datetime
from itertools import islice


def compute_opti(params, par_rh, init_val, n_opt, options, matched_bids_info, prev_traded, r,
                 is_buying, trading_price, block_length, opti_bes_res_buyer, opti_res_css, mar_agent_css):

    """Optimization model for the central supply system participating in the negotiation as buyer or seller. It is the same as the initial
    optimization model run in opti_css, but with the difference that there are additional constraints and variables
    regarding trading price and power.

    Returns: opti_css_res (dict): Dictionary containing the results of the optimization model.
      """

    # Define subsets
    storage = ["s_bat"]  # Shared battery storage
    renewables = ("s_pv", "s_wind")  # Solar park, wind turbine.
    devices = ("s_bat", "s_pv", "s_wind")

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    time_steps = par_rh["time_steps"][n_opt][0:block_length]

    # get elec, heat etc. for optimization n_opt
    #demands = {
    #    "elec": node["elec"],
    #    "heat": node["heat"],
    #    "dhw": node["dhw"],
    #    "COP35": node["devs"]["COP_sh35"],
    #    "COP55": node["devs"]["COP_sh55"],
    #    "PV_GEN": node["pv_power"],
        #"EV_AVAIL": EV_AVAIL,
        #"EV_DEM_LEAVE": EV_DEM_LEAVE,
    #    }

    model = gp.Model("Operation computation")

    # Initialization: only if initial values have been generated in previous prediction horizon
    soc_init_rh = {}
    if bool(init_val):
        # initial SOCs
        for dev in storage:
            soc_init_rh[dev] = init_val["soc"][dev]

    if par_rh["month"] == 0:
        par_rh["month"] = par_rh["month"] + 1

    # Define variables
    # Costs and Revenues
    revenue = {}
    c_imp = {}  # Costs of electricity import
    for rev in ["grid", "trading"]:
        revenue[rev] = {}
        revenue[rev] = model.addVar(vtype="C", name="revenue_" + rev)
        c_imp[rev] = model.addVar(vtype="C", name="cost_import_" + rev)

    cost_trade = model.addVar(vtype="C", name="cost_trade")

    revenue_trade = model.addVar(vtype="C", name="revenue_trade")

    # SOC, charging, discharging, power and heat
    soc = {}
    p_ch = {}
    p_dch = {}
    power = {}
    for dev in storage:  # All storage devices
        soc[dev] = {}
        p_ch[dev] = {}
        p_dch[dev] = {}
        for t in time_steps:  # All time steps of all days
            soc[dev][t] = model.addVar(vtype="C", lb=0, name="SOC_" + dev + "_" + str(t))
            p_ch[dev][t] = model.addVar(vtype="C", lb=0, name="P_ch_" + dev + "_" + str(t))
            p_dch[dev][t] = model.addVar(vtype="C", lb=0, name="P_dch_" + dev + "_" + str(t))

    # PV and Wind
    for dev in renewables:
        power[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # maping storage sizes
    soc_nom = {}
    for dev in storage:
        soc_nom[dev] = mar_agent_css.bat_capacity # kWh  Nominal storage capacity

    # Storage initial SOC's
    soc_init = {}
    soc_init["s_bat"] = soc_nom["s_bat"] * 0.1  # kWh   Initial SOC Battery

    # Electricity export
    p_exp = {}  # Total electricity exported
    p_grid_sell = {}  # Electricity sold to the grid
    # Dicts for the variables of traded power and trading price
    # power_trade_sell = {}  # Power traded
    # prev_trade["seller"] = {}  # Previous power traded
    for t in time_steps:
        p_exp[t] = model.addVar(vtype="C", name="total_power_exported" + str(t))
        p_grid_sell[t] = model.addVar(vtype="C", name="p_grid_sell" + str(t))
        # power_trade_sell[t] = model.addVar(vtype="C", name="power_trade_sell_" + str(t))
        # prev_trade["seller"][t] = model.addVar(vtype="C", name="Previous_power_trade_sell_" + str(t))

    # Electricity import
    p_imp = {}
    p_grid_buy = {}
    # power_trade_buy = {}
    # prev_trade_buy = {}
    for t in time_steps:
        p_imp[t] = model.addVar(vtype="C", name="total_power_imported_" + str(t))
        p_grid_buy[t] = model.addVar(vtype="C", name="p_grid_buy_" + str(t))
        # power_trade_buy[t] = model.addVar(vtype="C", name="power_trade_buy_" + str(t))
        # prev_trade_buy[t] = model.addVar(vtype="C", name="Previous_power_trade_buy_" + str(t))

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
    # todo: check if this is correct
    quantity_bid_seller = {}
    quantity_bid_buyer = {}

    # quantity and price of the buyer and seller is only set for block length
    for t in time_steps:
        quantity_bid_buyer[t] = matched_bids_info[0][t][1]
        quantity_bid_seller[t] = matched_bids_info[1][t][1]

    # Activation decision variables
    # binary variable for each css block to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["s_bat", "css_load"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # Electricity imports, sold and self-used electricity
    #p_imp = {}
    #p_use = {}
    #p_sell = {}
    #y_imp = {}
    #p_grid_buy = {}
    #p_grid_sell = {}
    #for t in time_steps:
    #    p_imp[t] = model.addVar(vtype="C", name="P_imp_" + str(t))
    #    p_grid_buy[t] = model.addVar(vtype="C", name="P_grid_buy" + str(t))
    #    p_grid_sell[t] = model.addVar(vtype="C", name="P_grid_sell" + str(t))
    #    y_imp[t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_imp_exp_" + str(t))

    # sold and self-used electricity
    p_use = {}
    p_sell = {}
    for dev in renewables:
        p_use[dev] = {}
        p_sell[dev] = {}
        for t in time_steps:
            p_use[dev][t] = model.addVar(vtype="C", name="P_use_" + dev + "_" + str(t))
            p_sell[dev][t] = model.addVar(vtype="C", name="P_sell_" + dev + "_" + str(t))

    # Gas imports to devices
    #gas = {}
    #for dev in ["chp", "boiler"]:
    #    gas[dev] = {}
    #    for t in time_steps:
    #        gas[dev][t] = model.addVar(vtype="C", name="gas" + dev + "_" + str(t))

    # Activation decision variables
    # binary variable for each house to avoid simultaneous feed-in and purchase of electric energy
    #y = {}
    #for dev in ["bat", "house_load"]:
    #    y[dev] = {}
    #    for t in time_steps:
    #        y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # Update
    model.update()
    # Objective
    if is_buying:
        model.setObjective(c_imp["grid"] - revenue["grid"] + cost_trade, gp.GRB.MINIMIZE)
    else:
        model.setObjective(c_imp["grid"] - revenue["grid"] - revenue_trade, gp.GRB.MINIMIZE)

    ####### Define constraints

    # --------------- ECONOMIC CONSTRAINTS ---------------

    # Demand related costs (electricity)
    dev = "grid"
    model.addConstr(c_imp[dev] == sum(p_grid_buy[t] * params["eco"]["pr", "el"] for t in time_steps),
                    name="Demand_costs_" + dev)

    # Revenues for selling electricity to the grid / neighborhood
    dev = "grid"
    model.addConstr(revenue[dev] == sum(p_grid_sell[t] * params["eco"]["sell" + "_pv"] for t in time_steps),
                        name="Feed_in_rev_" + dev)

    # Costs and revenues of trade
    if is_buying:
        model.addConstr(cost_trade == sum(power_trade["buyer"][t] * trading_price[t] for t in time_steps),
                        name="Power_trade_costs")
    else:
        model.addConstr(revenue_trade == sum(power_trade["seller"][t] * trading_price[t] for t in time_steps),
                        name="Power_trade_revenue")

    # --------------- TECHNICAL CONSTRAINTS ---------------

    ### Devices operation
    for t in time_steps:
        # Solar park and wind turbine
        dev = "s_pv"
        model.addConstr(power[dev][t] == mar_agent_css.pv_power[t],
                        name="Solar_electrical_" + dev + "_" + str(t))

        dev = "s_wind"
        model.addConstr(power[dev][t] == mar_agent_css.wind_power[t],
                        name="Wind_electrical_" + dev + "_" + str(t))


    # %%  STORAGES # %%  FLEXIBILITIES
    dev = "s_bat"
    k_loss = mar_agent_css.k_loss  # Battery degradation loss factor
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]  # Start of optimization window (hour)
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]  # Start of month
        else:
            soc_prev = soc[dev][t - 1]  # Previous time step SoC

        # Maximal charging and prevent negative charging
        model.addConstr(p_ch["s_bat"][t] <= y["s_bat"][t] * mar_agent_css.bat_capacity * mar_agent_css.bat_soc_ch_max,
                        name="max_ch_s_bat_" + str(t))  # maximum charging power 150 kW
        model.addConstr(p_ch["s_bat"][t] >= 0, name="min_ch_s_bat_" + str(t))
        # Maximal discharging
        model.addConstr(p_dch["s_bat"][t] <= (1 - y["s_bat"][t]) * mar_agent_css.bat_capacity * mar_agent_css.bat_soc_dch_max,
                        name="max_dch_s_bat_" + str(t))
        model.addConstr(p_dch["s_bat"][t] >= 0, name="min_dch_s_bat_" + str(t))

        # Battery SOC constraints: Minimal and maximal soc
        model.addConstr(soc["s_bat"][t] <= mar_agent_css.bat_soc_max * mar_agent_css.bat_capacity,
                        name="max_soc_s_bat_" + str(t))
        model.addConstr(soc["s_bat"][t] >= mar_agent_css.bat_soc_min * mar_agent_css.bat_capacity,
                        name="min_soc_s_bat_" + str(t))

        # SOC coupled over all times steps (Energy amount balance, kWh)
        model.addConstr(soc[dev][t] == (1 - k_loss) * soc_prev +
                        (p_ch[dev][t] * mar_agent_css.bat_eta - p_dch[dev][t] / mar_agent_css.bat_eta) * dt[t],
                        name="Storage_balance_" + dev + "_" + str(t))

    for t in time_steps:
        # Electricity balance for the central supply system
        model.addConstr(p_exp[t] + p_ch["s_bat"][t] ==
                        p_imp[t] + p_dch["s_bat"][t] + power["s_wind"][t] + power["s_pv"][t],
                        name="Electricity_balance_" + str(t))
        # Split Wind and PV generation into self-consumed and sold powers
        for dev in renewables:
            model.addConstr(p_sell[dev][t] + p_use[dev][t] == power[dev][t],
                            name="power=sell+use_" + dev + "_" + str(t))

        model.addConstr(p_exp[t] == p_sell["s_wind"][t] + p_sell["s_pv"][t] + p_dch["s_bat"][t],
                        name="Power_export_split_" + str(t))
        model.addConstr(p_imp[t] == p_ch["s_bat"][t] - p_use["s_wind"][t] - p_use["s_pv"][t],
                        name="Power_import_split_" + str(t))
        # Power trading constraints: split exported power into trading power, previous traded power and power to the grid
        # model.addConstr(p_exp[t] == p_grid_sell[t] + power_trade["seller"][t] + prev_trade["seller"][t],
        #                 name="Power_export_split_" + str(t))
            # if first trading:
            #model.addConstr(power_trade["seller"][t] == 0)
            #model.addConstr(prev_trade_sell[t] == 0)
            # model.addConstr(prev_trade_sell[t] == prev_traded["css"][t], name="Previous_traded_electricity_css_" + str(t))

        # SOC and the end time step of block bid == SOC of opti with prediction horizon
        if t == time_steps[-1]:
            for dev in storage:
                model.addConstr(soc[dev][t] == opti_res_css["res_soc"][dev][t], name="soc_bb=soc_ph")

        if is_buying:
            model.addConstr(p_imp[t] == p_grid_buy[t] + power_trade["buyer"][t] + prev_trade["buyer"][t],
                            name="import=grid+trade+prev_" + str(t))
            model.addConstr(prev_traded["buy"][t] == prev_trade["buyer"][t], name="prev_trade_sell==0_" + str(t))
            model.addConstr(opti_res_css["res_p_grid_sell"][t] == p_grid_sell[t], name="p_grid_sell==0_" + str(t))
            model.addConstr(prev_traded["sell"][t] == prev_trade["seller"][t], name="prev_trade_sell==0_" + str(t))
            # power the buyer can trade is limited by the quantity the seller is willing to sell
            model.addConstr(power_trade["buyer"][t] <= quantity_bid_seller[t], name="max_Power_trade_buyer")
            model.addConstr(power_trade["buyer"][t] >= 0, name="min_Power_trade_buyer")
        else:
            model.addConstr(p_exp[t] == p_grid_sell[t] + power_trade["seller"][t] + prev_trade["seller"][t],
                            name="sold=grid+trade+prev_" + str(t))
            model.addConstr(prev_traded["sell"][t] == prev_trade["seller"][t], name="prev_trade_buy==0_" + str(t))
            model.addConstr(opti_res_css["res_p_grid_buy"][t] == p_grid_buy[t], name="p_grid_buy==0_" + str(t))
            model.addConstr(prev_traded["buy"][t] == prev_trade["buyer"][t], name="prev_trade_buy==0_" + str(t))
            #
            model.addConstr(power_trade["seller"][t] <= opti_bes_res_buyer["res_power_trade"][t], name="max_Power_trade_seller")
            model.addConstr(power_trade["seller"][t] >= 0, name="min_Power_trade_seller_1")
            if quantity_bid_seller[t] <= opti_bes_res_buyer["res_power_trade"][t] and quantity_bid_seller[t] != 0:
                model.addConstr(power_trade["seller"][t] >= quantity_bid_seller[t], name="min_Power_trade_seller_2")

        # for inflexible market participants with buy and sell quantities in a bidding period
        if is_buying:
            if matched_bids_info[0]["ignored_demand"]:
                model.addConstr(p_imp[t] <= opti_res_css["res_p_ch"][t], name="A1")
                model.addConstr(p_sell["s_wind"][t] == opti_res_css["res_p_sell"]["s_wind"][t], name="A2")
                model.addConstr(p_sell["s_pv"][t] == opti_res_css["res_p_sell"]["s_pv"][t], name="A3")
                # todo: make sure p_sell wind and pv are correct
        else:
            if matched_bids_info[1]["ignored_demand"]:
                model.addConstr(p_imp[t] <= opti_res_css["res_p_ch"][t], name="B1")
                model.addConstr(p_sell["s_wind"][t] == opti_res_css["res_p_sell"]["s_wind"][t], name="B2")
                model.addConstr(p_sell["s_pv"][t] == opti_res_css["res_p_sell"]["s_pv"][t], name="B3")

    if is_buying:
        # Trading quantity during negotiation is limited by the bid quantity
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) <= sum(quantity_bid_buyer.values()),
                        name="sum_p_buy")
        # Limitation of imported electricity volumes (more electricity needed through flexibility
        # utilisation and heat losses) based on the initial bids
        # todo: Ineffizienz als Sensitivitätsanalyse
        model.addConstr(sum(p_imp[t] for t in time_steps) <= sum(opti_res_css["res_p_ch"][t] for t in time_steps)*1.2,
                        name="sum_p_imp")
        ## Buyer is not allowed to trade a sell quantity
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) == 0,
                        name="sum_p_sell")
    else:
        model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) == 0,
                        name="sum_p_buy")
        # Limitation of exported electricity volumes based on the initial bids
        model.addConstr(sum(p_sell["s_wind"][t] for t in time_steps) <=
                        sum(opti_res_css["res_p_sell"]["s_wind"][t] for t in time_steps)*1.2,
                        name="sum_p_sell_s_wind")
        model.addConstr(sum(p_sell["s_pv"][t] for t in time_steps) <=
                        sum(opti_res_css["res_p_sell"]["s_pv"][t] for t in time_steps)*1.2,
                        name="sum_p_sell_s_pv")
        # The sum of power_trade cannot be greater than total trading quantity of the block bid
        model.addConstr(sum(power_trade["seller"][t] for t in time_steps) <= sum(quantity_bid_seller.values()),
                        name="sum_p_sell")
        # Limiting the load peak within the block bid based on the initial bids
        for t in time_steps:
            model.addConstr(p_sell["s_wind"][t] <= max(opti_res_css["res_p_sell"]["s_wind"][t] for t in time_steps),
                            f"MaxConstraint_Wind_{t}")
            model.addConstr(p_sell["s_pv"][t] <= max(opti_res_css["res_p_sell"]["s_pv"][t] for t in time_steps),
                            f"MaxConstraint_PV_{t}")

    # Set solver parameters
    ratedPower = 150000
    # Guarantee that just feed-in OR load is possible
    for t in time_steps:
        model.addConstr(y["css_load"][t] * ratedPower >= p_imp[t], name="binary_import_" + str(t))  #  + power_trade["buyer"][t]
        model.addConstr(p_imp[t] >= 0, name="p_imp>=0_" + str(t))
        model.addConstr((1 - y["css_load"][t]) * ratedPower >= p_exp[t], name="binary_export_" + str(t))  # + power_trade["seller"][t]
        model.addConstr(p_exp[t] >= 0, name="p_exp>=0_" + str(t))

    if is_buying:
        for t in time_steps:
            model.addConstr(y["css_load"][t] == 1, name="sum_y_css_load")
    else:
        for t in time_steps:
            model.addConstr(y["css_load"][t] == 0, name="sum_y_css_load")

    # Set solver parameters
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]
    model.Params.NonConvex = 2

    # Execute calculation
    model.optimize()

    # Write errorfile if optimization problem is infeasible or unbounded
    if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:
        print(matched_bids_info[1]["css_id"])
        print(matched_bids_info[0]["bes_id"])
        model.computeIIS()
        model.write("model.ilp")
        f = open('errorfile_2.txt', 'w')
        f.write(str(datetime.datetime.now()) + '\nThe following constraint(s) cannot be satisfied:\n')
        for c in model.getConstrs():
            if c.IISConstr:
                f.write('%s' % c.constrName)
                f.write('\n')
        f.close()
    # elif model.status == gp.GRB.Status.UNBOUNDED:
    #     print('Model is unbounded')
    #     f = open('errorfile_2.txt', 'w')
    #     f.write(str(datetime.datetime.now()) + '\nModel is unbounded')
    #     f.close()
    # elif model.status == gp.GRB.Status.INF_OR_UNBD:
    #     print('Model is infeasible or unbounded')
    #     f = open('errorfile_2.txt', 'w')
    #     f.write(str(datetime.datetime.now()) + '\nModel is infeasible or unbounded')
    #     f.close()

    # Retrieve results
    res_y = {}
    res_power = {}
    res_soc = {}

    for dev in renewables:
        res_power[dev] = {(t): power[dev][t].X for t in time_steps}
    for dev in storage:
        res_soc[dev] = {(t): soc[dev][t].X for t in time_steps}

    res_p_imp = {(t): p_imp[t].X for t in time_steps}
    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {(t): p_ch[dev][t].X for t in time_steps}
        res_p_dch[dev] = {(t): p_dch[dev][t].X for t in time_steps}

    res_c_dem = {}
    #res_c_dem["grid"] = {(t): p_imp[t].X * params["eco"]["pr", "el"] for t in time_steps}

    res_rev = {}
    #for dev in ["pv", "chp"]:
    #    res_rev = {(t): p_sell[dev][t].X * params["eco"]["sell" + "_" + dev] for t in time_steps}

    res_soc_nom = {dev: soc_nom[dev] for dev in storage}
    res_price_trade = {(t): trading_price[t] for t in time_steps}

    res_p_use = {}
    res_p_sell = {}
    for dev in renewables:
        res_p_use[dev] = {t: p_use[dev][t].X for t in time_steps}
        res_p_sell[dev] = {t: p_sell[dev][t].X for t in time_steps}

    res_p_grid_buy = {t: p_grid_buy[t].X for t in time_steps}
    res_p_grid_sell = {t: p_grid_sell[t].X for t in time_steps}
    res_p_trade_buy = {t: power_trade["buyer"][t].X for t in time_steps}
    res_p_trade_sell = {t: power_trade["seller"][t].X for t in time_steps}

    if is_buying:
        res_power_trade = {(t): power_trade["buyer"][t].X for t in time_steps}
        res_prev_trade = {(t): prev_trade["buyer"][t].X for t in time_steps}
    else:
        res_power_trade = {(t): power_trade["seller"][t].X for t in time_steps}
        res_prev_trade = {(t): prev_trade["seller"][t].X for t in time_steps}

    obj = model.ObjVal
    print("Obj: " + str(model.ObjVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()
    #        model.computeIIS()
    #        model.write("model.ilp")
    #        print('\nConstraints:')
    #        for c in model.getConstrs():
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
        "res_soc": res_soc,
        "res_p_imp": res_p_imp,
        "res_p_ch": res_p_ch,
        "res_p_dch": res_p_dch,
        "res_p_use": res_p_use,
        "res_p_sell": res_p_sell,
        "obj": obj,
        "res_c_dem": res_c_dem,
        "res_rev": res_rev,
        "res_soc_nom": res_soc_nom,
        "objVal": objVal,
        "runtime": runtime,
        "soc_init_rh": soc_init_rh,
        "res_price_trade": res_price_trade,
        "res_power_trade": res_power_trade,
        "res_p_trade_buy": res_p_trade_buy,
        "res_p_trade_sell": res_p_trade_sell,
        "res_p_grid_buy": res_p_grid_buy,
        "res_p_grid_sell": res_p_grid_sell,
        "res_prev_trade": res_prev_trade,
    }

    return opti_bes_res


def replace_opti_res_css(opti_res_css, opti_res_block_bid, par_rh, n_opt):

    control_horizon = []
    for t_ch in range(par_rh["n_hours"] - par_rh["n_hours_ov"]):
        control_horizon.append(par_rh["time_steps"][n_opt][t_ch])

    for t in control_horizon:
        for dev in ["s_pv", "s_wind"]:
            # power
            opti_res_css["res_power"][dev][t] = opti_res_block_bid["res_power"][dev][t]
        for dev in ["s_bat"]:
            # soc
            opti_res_css["res_soc"][dev][t] = opti_res_block_bid["res_soc"][dev][t]
            # ch
            opti_res_css["res_p_ch"][dev][t] = np.round(np.absolute(opti_res_block_bid["res_p_ch"][dev][t]), 5)
            # dch
            opti_res_css["res_p_dch"][dev][t] = np.round(np.absolute(opti_res_block_bid["res_p_dch"][dev][t]), 5)
        # p_imp
        opti_res_css["res_p_imp"][t] = opti_res_block_bid["res_p_imp"][t]
        for dev in ["s_pv", "s_wind"]:
            opti_res_css["res_p_use"][dev][t] = opti_res_block_bid["res_p_use"][dev][t]
            # p_sell
            opti_res_css["res_p_sell"][dev][t] = opti_res_block_bid["res_p_sell"][dev][t]

    for t in control_horizon:
        opti_res_css["res_p_grid_buy"][t] = opti_res_block_bid["res_p_grid_buy"][t]
        opti_res_css["res_p_grid_sell"][t] = opti_res_block_bid["res_p_grid_sell"][t]
        opti_res_css["res_p_trade"][t] = opti_res_block_bid["res_power_trade"][t] + opti_res_block_bid["res_prev_trade"][t]
        opti_res_css["res_prev_trade"][t] = opti_res_block_bid["res_prev_trade"][t]

    return opti_res_css


def initial_values_block(nb_buildings, opti_res, block_bid_time_steps, length_block_bid, opti_res_css, n_opt):
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
    # Get the last time step of the block bid
    last_time_step = block_bid_time_steps[-1]

    init_val_block = {}
    # create dict to store initial values of all BES
    for n in range(nb_buildings):
        init_val_block["building_" + str(n)] = {}
        init_val_block["building_" + str(n)]["soc"] = {}
        # fill this dict with initial SoC values of first optimisation
        for dev in ["tes", "bat", "ev"]:
            init_val_block["building_" + str(n)]["soc"][dev] = opti_res[n][3][dev][last_time_step]

    # create dict to store initial values of CSS
    init_val_block["css"] = {"soc": {"s_bat": {}}}
    # fill this dict with initial SoC values of first optimisation
    init_val_block["css"]["soc"]["s_bat"] = opti_res_css[n_opt]["res_soc"]["s_bat"][last_time_step]


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

