#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subproblem optimization model for hierarchical central supply system (CSS) optimization.

"""
from __future__ import division
import gurobipy as gp
import datetime


def compute(mar_agent_css, params, par_rh, init_val, n_opt,  matched_bids, prev_traded, trading_price,  block_length,
            opti_res, options, res_soc_prev):
    # params:  dict, economic parameters, such as costs of electricity or gas, and technical parameters for optimization
    # par_rh: dict, contains information about the prediction horizon (time-related parameters).
    # init_val: dict, contains the initial values for the storage devices, such as the initial SOC
    # n_opt: int, number of the optimization horizon

    # Define subsets
    storage = ["s_bat"]  # Shared battery storage
    renewables = ("s_pv", "s_wind")    # Solar park, wind turbine.
    devices = ("s_bat", "s_pv", "s_wind")

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    time_steps = par_rh["time_steps"][n_opt]  #[0:block_length]

    model = gp.Model("Operation computation")

    # Initialization: only if initial values have been generated in previous prediction horizon
    soc_init_rh = {}
    if bool(init_val[n_opt]["css"]):  #If init_val exists, the initial state of charge (SOC) for the battery (bat) is used in the model.
        # initial SOCs
        for dev in storage:
            soc_init_rh[dev] = init_val[n_opt]["css"]["soc"][dev]

    if par_rh["month"] == 0:
        par_rh["month"] = par_rh["month"] + 1

    # Define variables
    revenue = {}  # Revenues
    c_imp = {}  # Costs of electricity import
    for rev in ["grid", "trading"]:
        revenue[rev] = model.addVar(vtype="C", name="revenue_" + rev)
        c_imp[rev] = model.addVar(vtype="C", name="cost_import_" + rev)

    # SOC, charging, discharging, power
    soc = {}
    p_ch = {}
    p_dch = {}
    power = {}
    for dev in storage:  # All storage devices
        soc[dev] = {}
        p_ch[dev] = {}
        p_dch[dev] = {}
        for t in time_steps:
            soc[dev][t] = model.addVar(vtype="C", name="SOC_" + dev + "_" + str(t))
            p_ch[dev][t] = model.addVar(vtype="C", name="p_ch_" + dev + "_" + str(t))
            p_dch[dev][t] = model.addVar(vtype="C", name="p_dch_" + dev + "_" + str(t))

    for dev in renewables:
        power[dev] = {}
        for t in time_steps:
            power[dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # mapping storage sizes
    soc_nom = {}
    for dev in storage:
        soc_nom[dev] = mar_agent_css.bat_capacity # kWh  Nominal storage capacity

    # Storage initial SOC's
    soc_init = {}
    soc_init["s_bat"] = soc_nom["s_bat"] * 0.1  # kWh   Initial SOC Battery

    # VARIABLE FOR TRADING POWER
    power_trade = {}
    prev_trade = {}
    for peer in ["buyer", "seller"]:
        power_trade[peer] = {}
        prev_trade[peer] = {}
        for t in time_steps:
            power_trade[peer][t] = model.addVar(vtype="C", name="Power_trade_" + peer + "_" + str(t))
            prev_trade[peer][t] = model.addVar(vtype="C", name="Previous_power_trade_" + peer + "_" + str(t))

    # Electricity export
    p_exp = {}  # Total electricity exported
    p_grid_sell = {}  # Electricity sold to the grid
    # Dicts for the variables of traded power and trading price
    # power_trade_sell = power_trade["seller"]  # Power traded
    # prev_trade_sell = prev_trade["seller"]  # Previous power traded
    for t in time_steps:
        p_exp[t] = model.addVar(vtype="C", name="total_power_exported" + str(t))
        p_grid_sell[t] = model.addVar(vtype="C", name="p_grid_sell" + str(t))
        # power_trade_sell[t] = model.addVar(vtype="C", name="power_trade_sell_" + str(t))
        # prev_trade_sell[t] = model.addVar(vtype="C", name="Previous_power_trade_sell_" + str(t))
        
    # Electricity import
    p_imp = {}
    p_grid_buy = {}
    # power_trade_buy = power_trade["buyer"]
    # prev_trade_buy = prev_trade["buyer"]
    for t in time_steps:
        p_imp[t] = model.addVar(vtype="C", name="total_power_imported_" + str(t))
        p_grid_buy[t] = model.addVar(vtype="C", name="p_grid_buy_" + str(t))
        # power_trade_buy[t] = model.addVar(vtype="C", name="power_trade_buy_" + str(t))
        # prev_trade_buy[t] = model.addVar(vtype="C", name="Previous_power_trade_buy_" + str(t))

    # # Todo: Currently empty: Import bid power quantity and bid price of matched trading partners
    # quantity_bid_seller = {}
    # quantity_bid_buyer = {}
    # # Todo: quantity and price of the buyer and seller is only set for block length
    # for t in time_steps[0:block_length]:
    #     quantity_bid_buyer[t] = matched_bids[1][t][1]
    #     quantity_bid_seller[t] = matched_bids[0][t][1]
    #for t in time_steps[0]:
    price = trading_price[time_steps[0]]  # Trading price

    p_use = {}
    p_sell = {}
    for dev in renewables:
        # Electricity use and sell
        p_use[dev] = {}
        p_sell[dev] = {}
        for t in time_steps:
            p_use[dev][t] = model.addVar(vtype="C", name="P_use_" + dev + "_" + str(t))
            p_sell[dev][t] = model.addVar(vtype="C", name="P_sell_" + dev + "_" + str(t))

    # Activation decision variables
    # binary variable for each css block to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["s_bat"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))


    # export coefficients
    #exp_co = {}
    #for dev in renewables:
    #    exp_co[dev] = {}
    #    for t in time_steps:
    #        exp_co[dev][t] = model.addVar(vtype="C", lb=0.0, ub=1.0, name="exp_co_" + dev + "_" + str(t))

    # Update model
    model.update()

    # Objective function
    model.setObjective(c_imp["grid"] + c_imp["trading"] - revenue["grid"] - revenue["trading"], gp.GRB.MINIMIZE)

    # Define constraints
    # Economic constraints
    # Revenues for selling electricity to the grid
    model.addConstr(revenue["grid"] == sum(p_grid_sell[t] * params["eco"]["sell_pv"] for t in time_steps),
                            name="Feed_in_rev_" + dev)
    # Todo: How to calc revenues of trading within community?
    model.addConstr(revenue["trading"] == sum(power_trade["seller"][t] * price for t in time_steps),
                            name="power_trade_sell_revenue")

    # Cost of electricity import
    model.addConstr(c_imp["grid"] == sum(p_imp[t] * params["eco"]["pr", "el"] for t in time_steps),
                        name="Cost_imported_electricity_grid")
    model.addConstr(c_imp["trading"] == sum(power_trade["buyer"][t] * price for t in time_steps),
                        name="Cost_imported_electricity_trade")

    # Devices operation
    for t in time_steps:
        # Solar park and wind turbine
        dev = "s_pv"
        model.addConstr(power[dev][t] == mar_agent_css.pv_power[t],
                        name="Solar_electrical_" + dev + "_" + str(t))
        dev = "s_wind"
        model.addConstr(power[dev][t] == mar_agent_css.wind_power[t],
                        name="Wind_electrical_" + dev + "_" + str(t))

    dev = "s_bat"
    k_loss = mar_agent_css.k_loss  # Battery degradation loss factor
    for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
        if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init_rh[dev]  # [t-1]  # Start of optimization window (hour)
        elif t == par_rh["month_start"][par_rh["month"]]:
            soc_prev = soc_init[dev]  # Start of month
        else:
            soc_prev = soc[dev][t - 1]  # Previous SOC
            # soc_prev = res_soc_prev

        # Charging and discharging power limits based on battery capacity and usage
        # (y is a binary variable controlling operation modes)
        # Maximal charging
        model.addConstr(p_ch["s_bat"][t] <= y["s_bat"][t] * mar_agent_css.bat_capacity * mar_agent_css.bat_soc_ch_max,
                        name="max_ch_s_bat_" + str(t)) # maximum charging power 150 kW
        # Maximal discharging
        model.addConstr(p_dch["s_bat"][t] <= (1 - y["s_bat"][t]) * mar_agent_css.bat_capacity * mar_agent_css.bat_soc_dch_max,
                        name="max_dch_s_bat_" + str(t))
        # Prevent negative charging and discharging
        model.addConstr(p_ch["s_bat"][t] >= 0, name="min_ch_s_bat_" + str(t))
        model.addConstr(p_dch["s_bat"][t] >= 0, name="min_dch_s_bat_" + str(t))

        # Battery SOC constraints: Minimal and maximal soc
        model.addConstr(soc["s_bat"][t] <= mar_agent_css.bat_soc_max * mar_agent_css.bat_capacity,
                        name="max_soc_s_bat_" + str(t))
        model.addConstr(soc["s_bat"][t] >= mar_agent_css.bat_soc_min * mar_agent_css.bat_capacity,
                        name="min_soc_s_bat_" + str(t))
        model.addConstr(soc[dev][t] == (1 - k_loss) * soc_prev +
                        (p_ch[dev][t] * mar_agent_css.bat_eta - p_dch[dev][t] / mar_agent_css.bat_eta) * dt[t],
                        name="Storage_balance_" + dev + "_" + str(t))

    # Split Wind and PV power into self-used and sold powers
    for dev in renewables:
        for t in time_steps:
            model.addConstr(power[dev][t] == p_use[dev][t] + p_sell[dev][t], name="power=sell+use_" + dev + "_" + str(t))

    # Electricity balance for the central supply system
    for t in time_steps:
        model.addConstr(p_exp[t] + p_ch["s_bat"][t] == p_imp[t] + p_dch["s_bat"][t] + power["s_wind"][t] + power["s_pv"][t],
                        name="Electricity_balance_" + str(t))
        model.addConstr(p_exp[t] == p_sell["s_pv"][t] + p_sell["s_wind"][t] + p_dch["s_bat"][t],
                        name="Power_export_parts_" + str(t))
        model.addConstr(p_imp[t] + p_use["s_pv"][t] + p_use["s_wind"][t] == p_ch["s_bat"][t],
                        name="Power_import_parts_" + str(t))

    # Power trading constraints: split exported power into trading power, previous traded power and power to the grid
    for t in time_steps:
        model.addConstr(p_exp[t] == p_grid_sell[t] + power_trade["seller"][t] + prev_trade["seller"][t],
                        name="Power_export_split_" + str(t))
        # model.addConstr(power_trade["seller"][t] <= opti_bes_res_buyer["res_power_trade"][t],
        #                 name="max_Power_trade_seller")
        # model.addConstr(power_trade["seller"][t] <= quantity_bid_seller[t], name="max_Power_trade_seller")
        model.addConstr(power_trade["seller"][t] >= 0, name="min_Power_trade_seller_1")
        # if quantity_bid_seller[t] <= opti_bes_res_buyer["res_power_trade"][t] and quantity_bid_seller[t] != 0:
        #     model.addConstr(power_trade["seller"][t] >= quantity_bid_seller[t], name="min_Power_trade_seller_2")
        # if first trading:
        #model.addConstr(power_trade["seller"][t] == 0)
        #model.addConstr(prev_trade["seller"][t] == 0)
        # else:
        # Todo: How to implement previous trading
        #model.addConstr(prev_trade["seller"][t] == prev_traded["css"][t], name="Previous_traded_electricity_css_" + str(t))

    # Power trading constraints: split imported power into trading power, previous traded power and power from the grid
    for t in time_steps:
        model.addConstr(p_imp[t] == p_grid_buy[t] + power_trade["buyer"][t] + prev_trade["buyer"][t], name="Power_import_split_" + str(t))
        # model.addConstr(power_trade["buyer"][t] <= quantity_bid_seller[t], name="max_Power_trade_buyer")
        model.addConstr(power_trade["buyer"][t] >= 0, name="min_Power_trade_buyer")
        # if first trading:
        #model.addConstr(power_trade["buyer"][t] == 0)
        #model.addConstr(prev_trade["buyer"][t] == 0)
        # else:
        # model.addConstr(prev_trade["buyer"][t] == prev_traded["css"][t], name="Previous_traded_electricity_css_" + str(t))

    # # Trading quantity during negotiation is limited by the bid quantity
    # model.addConstr(sum(power_trade["buyer"][t] for t in time_steps) <= sum(quantity_bid_buyer.values()),
    #                 name="sum_p_buy")
    # # The sum of power_trade_sell cannot be greater than total trading quantity of the block bid,
    # model.addConstr(sum(power_trade["seller"][t] for t in time_steps) <= sum(quantity_bid_seller.values()),
    #                 name="sum_p_sell")


    #for t in time_steps:
    #    model.addConstr(p_exp[t] <= max(opti_res[n_opt][n][8]["chp"][t] for n in range(options["nb_bes"]) for t in time_steps), f"MaxConstraint_{t}")

    # Set solver parameters
    ratedPower = 750000  # 750 kW
    # Guarantee that just feed-in OR load is possible
    for t in time_steps:
        model.addConstr(1 * ratedPower >= p_imp[t], name="binary_import_" + str(t))  #  + power_trade["buyer"][t]
        model.addConstr(p_imp[t] >= 0, name="p_imp>=0_" + str(t))
        model.addConstr(1 * ratedPower >= p_exp[t], name="binary_export_" + str(t))  # + power_trade["seller"][t]
        model.addConstr(p_exp[t] >= 0, name="p_exp>=0_" + str(t))

    # if is_buying:
    #     for t in time_steps:
    #         model.addConstr(y["css_load"][t] == 1, name="sum_y_css_load")
    # else:
    #     for t in time_steps:
    #         model.addConstr(y["css_load"][t] == 0, name="sum_y_css_load")


    # Set solver parameters (e.g., time limit, MIP gap)
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]

    # Execute the optimization model
    model.optimize()

    # Todo: correct the model, when infeasible or unbounded, can't computeIIS()
    # Write errorfile if optimization problem is infeasible or unbounded
    if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:
        model.computeIIS()
        f = open('errorfile_css.txt', 'w')
        f.write(str(datetime.datetime.now()) + f"Optimization stopped with status {model.status}"
                + '\nThe following constraint(s) cannot be satisfied:\n')
        for c in model.getConstrs():
            if c.IISConstr:
                f.write('%s' % c.constrName)
                f.write('\n')
        f.close()

    # Retrieve results
    res_y = {}
    res_power = {}
    res_soc = {}

    #if model.status == gp.GRB.Status.OPTIMAL:
    for dev in renewables:
        res_power[dev] = {t: power[dev][t].X for t in time_steps}
    for dev in storage:
        res_soc[dev] = {t: soc[dev][t].X for t in time_steps}
    #else:
    #    print("Model is not feasible or optimal. Cannot retrieve results.")

    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {t: p_ch[dev][t].X for t in time_steps}
        res_p_dch[dev] = {t: p_dch[dev][t].X for t in time_steps}

    res_rev = {}

    res_p_use = {}
    res_p_sell = {}
    for dev in renewables:
        res_p_use[dev] = {t: p_use[dev][t].X for t in time_steps}
        res_p_sell[dev] = {t: p_sell[dev][t].X for t in time_steps}

    res_p_exp = {}
    res_p_exp[dev] = {t: p_exp[t].X for t in time_steps}

    res_p_grid_sell = {t: p_grid_sell[t].X for t in time_steps}
    res_p_trade_sell = {t: power_trade["seller"][t].X for t in time_steps}
    res_prev_trade_sell = {t: prev_trade["seller"][t].X for t in time_steps}

    res_p_imp = {t: p_imp[t].X for t in time_steps}
    res_p_grid_buy = {t: p_grid_buy[t].X for t in time_steps}
    res_p_trade_buy = {t: power_trade["buyer"][t].X for t in time_steps}
    res_prev_trade_buy = {t: prev_trade["buyer"][t].X for t in time_steps}

    res_p_trade = {t: power_trade["buyer"][t].X + power_trade["seller"][t].X for t in time_steps}
    res_prev_trade = {t: prev_trade["buyer"][t].X + prev_trade["seller"][t].X for t in time_steps}
    obj = model.objVal
    print("Obj: " + str(model.objVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()

    # Return results
    return {"res_y": res_y, "res_power": res_power, "res_soc": res_soc, "res_p_imp": res_p_imp,
            "res_p_ch": res_p_ch, "res_p_dch": res_p_dch, "res_p_use": res_p_use, "res_p_sell": res_p_sell,
            "obj": obj, "res_rev": res_rev, "objVal": objVal,
            "runtime": runtime, "soc_init_rh": soc_init_rh,
            "res_p_grid_sell": res_p_grid_sell,
            "res_p_trade_sell": res_p_trade_sell, "res_prev_trade_sell": res_prev_trade_sell,
            "res_p_grid_buy": res_p_grid_buy, "res_p_trade_buy": res_p_trade_buy, "res_p_trade": res_p_trade,
            "res_prev_trade": res_prev_trade, "res_prev_trade_buy": res_prev_trade_buy}