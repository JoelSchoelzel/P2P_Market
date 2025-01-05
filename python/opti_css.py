#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subproblem optimization model for hierarchical central supply system (CSS) optimization.

"""
from __future__ import division
import gurobipy as gp
import datetime


def compute(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded, trading_price, block_length,
            opti_res, options):
    # todo: input anpassen für css! Infos zu den Gebäuden werden nicht mehr benötigt
    # params:  dict, economic parameters, such as costs of electricity or gas, and technical parameters for optimization
    # par_rh: dict, contains information about the prediction horizon (time-related parameters).
    # init_val: dict, contains the initial values for the storage devices, such as the initial SOC
    # n_opt: int, number of the optimization horizon

    # Define subsets
    storage = ("s_bat") # Shared battery storage
    renewables = ("s_pv", "s_wind")    # Solar park, wind turbine.
    devices = ("s_bat", "s_pv", "s_wind" )

    # Extract parameters
    dt = par_rh["duration"][n_opt]
    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    # last time step for soc_end
    first_time_step = time_steps[0]
    last_time_step = time_steps[-1]
    time_steps_block_bid = [time_steps[0], time_steps[1], time_steps[2], time_steps[3]]

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
    # Revenues
    revenue = {}
    for rev in ["fix_tarif", "trading"]:
        revenue[rev] = {}
        for t in time_steps:
            revenue[rev][t] = model.addVar(vtype="C", name="revenue_" + rev + "_" + str(t))

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

    # Electricity export
    p_exp = {} # Total electricity exported
    p_grid_sell = {} # Electricity sold to the grid
    # Dicts for the variables of traded power and trading price
    power_trade = {} # Power traded
    prev_trade = {} # Previous power traded
    for t in time_steps:
        p_exp[t] = model.addVar(vtype="C", name="total_power_exported" + str(t))
        p_grid_sell[t] = model.addVar(vtype="C", name="p_grid_sell" + str(t))
        power_trade[t] = model.addVar(vtype="C", name="Power_trade_" + str(t))
        prev_trade[t] = model.addVar(vtype="C", name="Previous_power_trade_" + str(t))

    # Import bid power quantity and bid price of matched trading partners
    quantity_bid_seller = {}
    quantity_bid_buyer = {}
    # quantity and price of the buyer and seller is only set for block length
    for t in time_steps:
        quantity_bid_buyer[t] = matched_bids[0][t][1]
        quantity_bid_seller[t] = matched_bids[1][t][1]

    # Activation decision variables
    # binary variable for each css block to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for dev in ["s_bat"]:
        y[dev] = {}
        for t in time_steps:
            y[dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # Update model
    model.update()

    # todo: Aufladen und Entladen der Batterie
    # Objective function
    model.setObjective( - revenue["grid"] - revenue["trading"], gp.GRB.MINIMIZE)

    # Define constraints
    # Economic constraints
    # Revenues for selling electricity to the grid
    model.addConstr(revenue["fix_tarif"] == sum(p_grid_sell[t] * params["eco"]["sell_pv"] for t in time_steps),
                        name="Feed_in_rev_" + dev)
    # Revenues of trading within community
    model.addConstr(revenue["trading"] == sum(power_trade[t] * trading_price[t] for t in time_steps),
                        name="Power_trade_revenue")


    # Devices operation
    for t in time_steps:
    # Solar park and wind turbine
        dev = "s_pv"
        model.addConstr(power[dev][t] == mar_agent_css.pv_power[t],
                        name="Solar_electrical_" + dev + "_" + str(t))

        dev = "s_wind"
        model.addConstr(power[dev][t] == mar_agent_css.wind_power[t],
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
    k_loss = mar_agent_css.k_loss  # Battery degradation loss factor
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
        model.addConstr(p_ch["s_bat"][t] <= y["s_bat"][t] * mar_agent_css.bat_cap * mar_agent_css.bat_ch_max,
                        name="max_ch_s_bat_" + str(t))
        # Maximal discharging
        model.addConstr(p_dch["s_bat"][t] <= (1 - y["s_bat"][t]) * mar_agent_css.bat_cap * mar_agent_css.bat_dch_max,
                        name="max_dch_s_bat_" + str(t))

        # Battery SOC constraints: Minimal and maximal soc
        model.addConstr(soc["s_bat"][t] <= mar_agent_css.bat_soc_max * mar_agent_css.bat_cap,
                        name="max_soc_s_bat_" + str(t))
        model.addConstr(soc["s_bat"][t] >= mar_agent_css.bat_soc_min * mar_agent_css.bat_cap,
                        name="max_soc_s_bat_" + str(t))

        #SoC degradation over time
        model.addConstr(soc[dev][t] == (1 - k_loss) * soc_prev +
                        dt[t] * (mar_agent_css.eta_bat * p_ch[dev][t] - 1 / mar_agent_css.eta_bat * p_dch[dev][t]),
                        name="Storage_balance_" + dev + "_" + str(t))

    # Electricity balance for the central supply system
    for t in time_steps:
        model.addConstr(p_exp[t] + p_ch["s_bat"][t] == p_dch["s_bat"][t] + power["s_wind"][t] + power["s_pv"][t],
                        name="Electricity_balance_" + str(t))
            
    # Power trading constraints: split exported power into trading power, previous traded power and power to the grid
    for t in time_steps:
        model.addConstr(p_exp[t] == p_grid_sell[t] + power_trade[t] + prev_trade[t])
        # if first trading:
        model.addConstr(power_trade[t] == 0)
        model.addConstr(prev_trade[t] == 0)
        # else:
        model.addConstr(prev_trade[t] == prev_traded["css"][t], name="Previous_traded_electricity_css_" + str(t))

    # The sum of power_trade cannot be greater than total trading quantity of the block bid
    model.addConstr(sum(power_trade[t] for t in time_steps) <= sum(quantity_bid_seller.values()),
                    name="sum_p_sell")
    for t in time_steps:
        model.addConstr(p_exp[t] <= max(opti_res[n_opt][n][8]["chp"][t] for n in options["nb_bes"] for t in time_steps), f"MaxConstraint_{t}")

    # Set solver parameters (e.g., time limit, MIP gap)
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]

    # Execute the optimization model
    model.optimize()

    # Write errorfile if optimization problem is infeasible or unbounded
    if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:
        model.computeIIS()
        f = open('errorfile_css.txt', 'w')
        f.write(str(datetime.datetime.now()) + '\nThe following constraint(s) cannot be satisfied:\n')
        for c in model.getConstrs():
            if c.IISConstr:
                f.write('%s' % c.constrName)
                f.write('\n')
        f.close()

    # Retrieve results
    res_y = {}
    res_power = {}
    res_soc = {}

    for dev in renewables:
        res_power[dev] = {t: power[dev][t].X for t in time_steps}
    for dev in storage:
        res_soc[dev] = {t: soc[dev][t].X for t in time_steps}

    res_p_ch = {}
    res_p_dch = {}
    for dev in storage:
        res_p_ch[dev] = {t: p_ch[dev][t].X for t in time_steps}
        res_p_dch[dev] = {t: p_dch[dev][t].X for t in time_steps}

    res_rev = {}

    res_p_exp = {}
    res_p_exp[dev] = {t: p_exp[t].X for t in time_steps}

    res_p_grid_sell = {(t): p_grid_sell[t].X for t in time_steps}
    res_p_trade = {(t): power_trade[t].X for t in time_steps}
    res_prev_trade = {(t): prev_trade[t].X for t in time_steps}

    obj = model.objVal
    print("Obj: " + str(model.objVal))
    objVal = obj

    runtime = model.getAttr("Runtime")
    datetime.datetime.now()

    # Return results
    return {"res_y": res_y, "res_power": res_power, "res_soc": res_soc,
            "res_p_ch": res_p_ch, "res_p_dch": res_p_dch,
            "obj": obj, "res_rev": res_rev, "objVal": objVal,
            "runtime": runtime, "soc_init_rh": soc_init_rh,
            "res_p_grid_sell": res_p_grid_sell,
            "res_p_trade": res_p_trade, "res_prev_trade": res_prev_trade}