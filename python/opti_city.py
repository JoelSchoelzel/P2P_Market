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


def compute(nodes, params, par_rh, building_param, init_val, n_opt, options):


    # Define subsets
    heater = ("boiler", "chp", "eh", "hp35", "hp55", "bz", "bz_sf")
    storage = ("bat", "tes", "ev")
    solar = ("pv",)  # , "stc"
    device = ("boiler", "chp", "eh", "hp35", "hp55", "bat", "tes", "pv", "bz", "bz_sf")


    # Create list of time steps and list of durations per optimization horizon
    time_steps = par_rh["time_steps"][n_opt]
    dt = par_rh["duration"][n_opt]

    # Durations of time steps # for aggregated RH
    # duration = par_rh["duration"][n_opt]

    # get relevant input data (elec, dhw, heat) for prediction horizon
    discretization_input_data = options["discretization_input_data"]

    # get elec, heat etc. for optimization n_opt
    demands = {}
    for n in nodes:
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
            param01 = int(dt[param00]/discretization_input_data)
            param02 = int(par_rh["org_time_steps"][n_opt][i]/discretization_input_data)
            if param01 < 1:
                raise ValueError("Interpolation of input data necessary")
            elif options["number_typeWeeks"] == 0:
                elec[param00] = np.mean([nodes[n]["elec"][param02], nodes[n]["elec"][param02 + param01 - 1]])
                heat[param00] = np.mean([nodes[n]["heat"][param02], nodes[n]["heat"][param02 + param01 - 1]])
                dhw[param00] = np.mean([nodes[n]["dhw"][param02], nodes[n]["dhw"][param02 + param01 - 1]])
                COP35[param00] = np.mean([nodes[n]["devs"]["COP_sh35"][param02], nodes[n]["devs"]["COP_sh35"][param02 + param01 - 1]])
                COP55[param00] = np.mean([nodes[n]["devs"]["COP_sh55"][param02], nodes[n]["devs"]["COP_sh55"][param02 + param01 - 1]])
                PV_GEN[param00] = np.mean([nodes[n]["pv_power"][param02], nodes[n]["pv_power"][param02 + param01 - 1]])
                EV_AVAIL[param00] = np.mean([nodes[n]["ev_avail"][param02], nodes[n]["ev_avail"][param02 + param01 - 1]])
                EV_DEM_LEAVE[param00] = np.mean([nodes[n]["ev_dem_leave"][param02], nodes[n]["ev_dem_leave"][param02 + param01 - 1]])
            else:
                elec[param00] = np.mean([nodes[n]["elec_appended"][param02], nodes[n]["elec_appended"][param02 + param01 - 1]])
                heat[param00] = np.mean([nodes[n]["heat_appended"][param02], nodes[n]["heat_appended"][param02 + param01 - 1]])
                dhw[param00] = np.mean([nodes[n]["dhw_appended"][param02], nodes[n]["dhw_appended"][param02 + param01 - 1]])
                COP35[param00] = np.mean([nodes[n]["devs"]["COP_sh35_appended"][param02], nodes[n]["devs"]["COP_sh35_appended"][param02 + param01 - 1]])
                COP55[param00] = np.mean([nodes[n]["devs"]["COP_sh55_appended"][param02], nodes[n]["devs"]["COP_sh55_appended"][param02 + param01 - 1]])
                PV_GEN[param00] = np.mean([nodes[n]["pv_power_appended"][param02], nodes[n]["pv_power_appended"][param02 + param01 - 1]])
                EV_AVAIL[param00] = np.mean([nodes[n]["ev_avail_appended"][param02], nodes[n]["ev_avail_appended"][param02 + param01 - 1]])
                EV_DEM_LEAVE[param00] = np.mean([nodes[n]["ev_dem_leave_appended"][param02], nodes[n]["ev_dem_leave_appended"][param02 + param01 - 1]])

            demands[n] = {
            "elec": elec,
            "heat": heat,
            "dhw": dhw,
            "COP35": COP35,
            "COP55": COP55,
            "PV_GEN": PV_GEN,
            "EV_AVAIL": EV_AVAIL,
            "EV_DEM_LEAVE": EV_DEM_LEAVE,
            }

    #for n in nodes:
     #   count = 0
      #  for k in indices:
       #     j = par_rh["hour_start"][n_opt] + count
        #    demands[n] = {
         #       "elec"[j]: nodes[n]["elec"][k],
          #      "heat"[j]: nodes[n]["heat"][k],
           #     "dhw"[j]: nodes[n]["dhw"][k],
           # }
           # count += 1


    model = gp.Model("Operation computation")

    # Initialization: only if initial values have been generated in previous prediction horizon
    soc_init_rh = {}
    if bool(init_val) == True:
        # initial SOCs
        # Buildings
        for n in nodes:
            soc_init_rh[n] = {}
            for dev in storage:
                soc_init_rh[n][dev] = init_val["soc"][n][dev]

    if par_rh["month"] == 0:
        par_rh["month"] = par_rh["month"] + 1

    # Define variables
    # Costs and Revenues
    c_dem = {dev: model.addVar(vtype="C", name="c_dem_" + dev)
             for dev in ("gas", "grid")}

    # revenue = {"grid": model.addVar(vtype="C", name="revenue_" + "grid")}

    revenue = {"grid_pv": model.addVar(vtype="C", name="revenue_" + "grid_pv"),
               "grid_chp": model.addVar(vtype="C", name="revenue_" + "grid_chp")}


    # SOC, charging, discharging, power and heat
    soc = {}
    p_ch = {}
    p_dch = {}
    power = {}
    heat = {}
    dhw = {}
    for n in nodes:
        soc[n] = {}
        p_ch[n] = {}
        p_dch[n] = {}
        for dev in storage:  # All storage devices
            soc[n][dev] = {}
            p_ch[n][dev] = {}
            p_dch[n][dev] = {}
            for t in time_steps:  # All time steps of all days
                soc[n][dev][t] = model.addVar(vtype="C", name="SOC_" + dev + "_" + str(t))
                p_ch[n][dev][t] = model.addVar(vtype="C", name="P_ch_" + dev + "_" + str(t))
                p_dch[n][dev][t] = model.addVar(vtype="C", name="P_dch_" + dev + "_" + str(t))


    for n in nodes:
        power[n] = {}
        heat[n] = {}
        for dev in ["hp35", "hp55", "chp", "boiler", "bz", "bz_sf"]:

            power[n][dev] = {}
            heat[n][dev] = {}
            for t in time_steps:
                power[n][dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))
                heat[n][dev][t] = model.addVar(vtype="C", lb=0, name="Q_" + dev + "_" + str(t))

    for n in nodes:
        dhw[n] = {}
        for dev in ["eh"]: # todo: EH nur für WW?
            dhw[n][dev] = {}
            power[n][dev] = {}
            for t in time_steps:
                dhw[n][dev][t] = model.addVar(vtype="C", name="Q_" + dev + "_" + str(t))
                power[n][dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    for n in nodes:
        for dev in ["pv"]:
            power[n][dev] = {}
            for t in time_steps:
                power[n][dev][t] = model.addVar(vtype="C", lb=0, name="P_" + dev + "_" + str(t))

    # mapping storage sizes
    soc_nom = {}
    for n in nodes:
        soc_nom[n] = {}
        for dev in storage:
            soc_nom[n][dev] = nodes[n]["devs"][dev]["cap"]

    # Storage initial SOC's
    soc_init = {}
    for n in nodes:
        soc_init[n] = {}
        soc_init[n]["tes"] = soc_nom[n]["tes"] * 0.5  # kWh   Initial SOC TES
        soc_init[n]["bat"] = soc_nom[n]["bat"] * 0.5  # kWh   Initial SOC Battery
        soc_init[n]["ev"] = soc_nom[n]["ev"] * 0.75

    # storage devices: soc_end = soc_init
    boolSOC = True
    if boolSOC:
        if par_rh["end_time_org"] in par_rh["org_time_steps"][n_opt]:
            index_end = par_rh["org_time_steps"][n_opt].index(par_rh["end_time_org"])
            time_step_end = par_rh["time_steps"][n_opt][index_end]

            for n in nodes:
                for dev in storage:
                    model.addConstr(soc[n][dev][time_step_end] == soc_init[n][dev],
                                    name = "soc_end == soc_init for " + str(dev) + " in BES: " +str(n) + " for n_opt: " + str(n_opt))


    # Electricity imports, sold and self-used electricity
    p_imp = {}
    p_use = {}
    p_sell = {}
    y_imp = {}
    for n in nodes:
        p_imp[n] = {}
        y_imp[n] = {}
        p_use[n] = {}
        p_sell[n] = {}
        for t in time_steps:
            p_imp[n][t] = model.addVar(vtype="C", name="P_imp_" + str(t))
            y_imp[n][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_imp_exp_" + str(t))
        for dev in ("chp", "pv", "bz", "bz_sf"):

            p_use[n][dev] = {}
            p_sell[n][dev] = {}
            for t in time_steps:
                p_use[n][dev][t] = model.addVar(vtype="C", name="P_use_" + dev + "_" + str(t))
                p_sell[n][dev][t] = model.addVar(vtype="C", name="P_sell_" + dev + "_" + str(t))

    # Gas imports to devices
    gas = {}
    for n in nodes:
        gas[n] = {}
        for dev in ["chp", "boiler", "bz", "bz_sf"]:

            gas[n][dev] = {}
            for t in time_steps:
                gas[n][dev][t] = model.addVar(vtype="C", name="gas" + dev + "_" + str(t))

    # mapping PV areas
   # area = {}
   # for n in nodes:
   #     area[n] = {}
   #     for dev in solar:
   #         area[n][dev] = building_param.iloc[n]["modules"] * nodes[n]["devs"]["pv"]["area_real"] # todo

    # Activation decision variables
    # binary variable for each house to avoid simultaneous feed-in and purchase of electric energy
    y = {}
    for n in nodes:
        y[n] = {}
        for dev in ["bat", "ev", "house_load"]:
            y[n][dev] = {}
            for t in time_steps:
                y[n][dev][t] = model.addVar(vtype="B", lb=0.0, ub=1.0, name="y_" + dev + "_" + str(t))

    # %% NETWORK VARIABLES

    # Network variables
    #power_net = {}
    #power_net["Inj"] = {}
    #power_net["Load"] = {}
    #for node in net_data["gridnodes"]:
        # Electricity demand
    #    power_net["Inj"][node] = {}
    #    power_net["Load"][node] = {}
    #    for t in time_steps:
    #        power_net["Inj"][node][t] = model.addVar(vtype="C",name="powerInj_" + str(n) + "_t" + str(t))
    #        power_net["Load"][node][t] = model.addVar(vtype="C",name="powerLoad_" + str(n) + "_t" + str(t))

    # set line bounds due to technical limits
    #powerLine = model.addVars(net_data["nodeLines"],time_steps,vtype="C",lb=-10000,name="powerLine_")

    # set trafo bounds due to technichal limits
    #powerTrafoLoad = model.addVars(time_steps,vtype="C",lb=0,ub=net_data["trafo_max"],name="powerTrafo_" + str(t))
    #powerTrafoInj = model.addVars(time_steps,vtype="C",lb=0,ub=net_data["trafo_max"],name="injTrafo_" + str(t))

    # activation variable for trafo load
    yTrafo = model.addVars(time_steps,vtype="B",name="yTrafo_" + str(t))

    # %% BALANCING UNIT VARIABLES

    # Residual network demand
    residual = {}
    residual["demand"] = {}  # Residual network electricity demand
    residual["feed_pv"] = {}  # Residual feed in pv
    residual["feed_chp"] = {}  # Residual feed in chp, bz, bz_sf
    power["from_grid"] = {}
    power["to_grid"] = {}
    gas_dom = {}
    for t in time_steps:
        residual["demand"][t] = model.addVar(vtype="C",name="residual_demand_t" + str(t))
        residual["feed_pv"][t] = model.addVar(vtype="C",name="residual_feed_pv_t" + str(t))
        residual["feed_chp"][t] = model.addVar(vtype="C",name="residual_feed_chp_t" + str(t))
        power["from_grid"][t] = model.addVar(vtype="C",name="district_demand_t" + str(t))
        power["to_grid"][t] = model.addVar(vtype="C",name="district_feed_t" + str(t))
        gas_dom[t] = model.addVar(vtype="C",name="gas_demand_t" + str(t))

    # Electrical power to/from devices
    for device in ["el_from_grid","el_to_grid","gas_from_grid"]:
        power[device] = {}
        for t in time_steps:
            power[device][t] = model.addVar(vtype="C",lb=0,name="power_" + device + "_t" + str(t))

    # total energy amounts taken from grid
    from_grid_total_el = model.addVar(vtype="C",name="from_grid_total_el")
    # total power to grid
    to_grid_total_el = model.addVar(vtype="C",name="to_grid_total_el")
    # total gas amounts taken from grid
    from_grid_total_gas = model.addVar(vtype="C",name="from_grid_total_gas")

    # Total gross CO2 emissions
    co2_total = model.addVar(vtype="c",lb=-gp.GRB.INFINITY,name="total_CO2")

    # Update
    model.update()

    # Objective
    # TODO:
    model.setObjective(c_dem["grid"] + c_dem["gas"]
                       - revenue["grid_pv"] - revenue["grid_chp"], gp.GRB.MINIMIZE)

    ####### Define constraints

    ##### Economic constraints

    # Demand related costs (gas)
    model.addConstr(c_dem["gas"] == params["eco"]["gas"] * sum(dt[t] * gas_dom[t] for t in time_steps),
                        name="Demand_costs_gas")
    # Demand related costs (electricity)
    model.addConstr(c_dem["grid"] == params["eco"]["pr", "el"] * sum(dt[t] * residual["demand"][t] for t in time_steps),
                    name="Demand_costs_el_grid")
    # Revenues for selling electricity to the grid / neighborhood
    model.addConstr(revenue["grid_pv"] == params["eco"]["sell_pv"] * sum(dt[t] * residual["feed_pv"][t] for t in time_steps),
                    name="Feed_in_rev_pv")
    model.addConstr(revenue["grid_chp"] == params["eco"]["sell_chp"] * sum(dt[t] * residual["feed_chp"][t] for t in time_steps),
                    name="Feed_in_rev_chp")

    ###### Technical constraints

    # Determine nominal heat at every timestep
    for n in nodes:
        for t in time_steps:
            for dev in ["hp35", "hp55", "chp", "boiler", "eh", "bz", "bz_sf"]:
            #for dev in ["hp35", "hp55", "chp", "boiler", "eh"]:

                if dev == "eh":
                    model.addConstr(power[n][dev][t] <= nodes[n]["devs"][dev]["cap"])
                else:
                    model.addConstr(heat[n][dev][t] <= nodes[n]["devs"][dev]["cap"],
                                    name="Max_heat_operation_" + dev)

    ### Devices operation
    # Heat output between mod_lvl*Q_nom and Q_nom (P_nom for heat pumps)
    # Power and Energy directly result from Heat output
    for n in nodes:
        for t in time_steps:
            # Heatpumps
            dev = "hp35"
            model.addConstr(heat[n][dev][t] == power[n][dev][t] * demands[n]["COP35"][t],
                            name="Power_equation_" + dev + "_" + str(t))
            # TODO: Check need of mod_lvl
            model.addConstr(heat[n][dev][t] >= power[n][dev][t] * demands[n]["COP35"][t] * nodes[n]["devs"][dev]["mod_lvl"],
                            name="Min_pow_operation_" + dev + "_" + str(t))

            dev = "hp55"
            model.addConstr(heat[n][dev][t] == power[n][dev][t] * demands[n]["COP55"][t],
                            name="Power_equation_" + dev + "_" + str(t))
            # TODO: Check need of mod_lvl
            model.addConstr(heat[n][dev][t] >= power[n][dev][t] * demands[n]["COP55"][t] * nodes[n]["devs"][dev]["mod_lvl"],
                            name="Min_pow_operation_" + dev + "_" + str(t))

            # CHP
            dev = "chp"
            model.addConstr(heat[n]["chp"][t] == nodes[n]["devs"]["chp"]["eta_th"] * gas[n]["chp"][t],
                            name="heat_operation_chp_" + str(t))

            model.addConstr(power[n]["chp"][t] == nodes[n]["devs"]["chp"]["eta_el"] * gas[n]["chp"][t],
                            name="Power_equation_" + dev + "_" + str(t))
            # TODO: Check need of mod_lvl
            # model.addConstr(power["chp"][t] == node["devs"]["chp"]["eta_el"] * gas["chp"][t] * node["devs"]["chp"]["mod_lvl"],
            #                name="Min_power_equation_chp_" + str(t))

            # BOILER
            dev = "boiler"
            model.addConstr(heat[n]["boiler"][t] == nodes[n]["devs"]["boiler"]["eta_th"] * gas[n]["boiler"][t],
                            name="Power_equation_" + dev + "_" + str(t))

            # Fuel Cell
            for dev in ["bz", "bz_sf"]:
                model.addConstr(heat[n][dev][t] == nodes[n]["devs"][dev]["eta_th"] * gas[n][dev][t],
                                name="Power_equation_" + dev + "_" + str(t))
                model.addConstr(power[n][dev][t] == nodes[n]["devs"][dev]["eta_el"] * gas[n][dev][t],
                                name="Power_equation_" + dev + "_" + str(t))

            # additional boundary conditions for min/max heat/power operation of Sunfire BZ
            if nodes[n]["devs"]["bz_sf"]["cap"] > 0:
                model.addConstr(heat[n]["bz_sf"][t] >= nodes[n]["devs"]["bz_sf"]["min_heat"],
                                name="min_heat_" + dev + "_t" + str(t) + "_bes" + str(n))
                model.addConstr(power[n]["bz_sf"][t] >= nodes[n]["devs"]["bz_sf"]["min_power"],
                                name="min_power_" + dev + "_" + str(t))
                model.addConstr(power[n]["bz_sf"][t] <= nodes[n]["devs"]["bz_sf"]["max_power"],
                                name="max_power_" + dev + "_" + str(t))

    # Solar components
    for n in nodes:
        for dev in solar:
            for t in time_steps:
                model.addConstr(power[n][dev][t] == demands[n]["PV_GEN"][t],
                                name="Solar_electrical_" + dev + "_" + str(t))

    # power of the electric heater
    for n in nodes:
        for t in time_steps:
            # covers 50% of the dhw power # todo
            model.addConstr(dhw[n]["eh"][t] == 0.5 * demands[n]["dhw"][t], name="El_heater_act_" + str(t))

    # %% BUILDING STORAGES # %% DOMESTIC FLEXIBILITIES

    ### TES CONSTRAINTS CONSTRAINTS
    dev = "tes"
    for n in nodes:
        eta_tes = nodes[n]["devs"][dev]["eta_tes"]
        eta_ch = nodes[n]["devs"][dev]["eta_ch"]
        eta_dch = nodes[n]["devs"][dev]["eta_dch"]

        for t in time_steps:
        # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
            if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init_rh[n][dev]
            elif t == par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init[n][dev]
            else:
                soc_prev = soc[n][dev][t - 1]

            # Maximal charging
            model.addConstr(p_ch[n][dev][t] == eta_ch * (heat[n]["chp"][t] + heat[n]["hp35"][t] + heat[n]["bz"][t] + heat[n]["bz_sf"][t]
                                                         + heat[n]["hp55"][t] + heat[n]["boiler"][t]),
                                                         name="Heat_charging_" + str(t))
            #model.addConstr(p_ch[n][dev][t] == eta_ch * (heat[n]["chp"][t] + heat[n]["hp35"][t]
            #                                         + heat[n]["hp55"][t] + heat[n]["boiler"][t]),
            #            name="Heat_charging_" + str(t))
            # Maximal discharging
            model.addConstr(p_dch[n][dev][t] == (1 / eta_dch) * (demands[n]["heat"][t] + 0.5 * demands[n]["dhw"][t]),
                            name="Heat_discharging_" + str(t)) # todo: 0.5*DHW ??

            # Minimal and maximal soc
            model.addConstr(soc[n]["tes"][t] <= soc_nom[n]["tes"], name="max_cap_tes_" + str(t))
            model.addConstr(soc[n]["tes"][t] >= nodes[n]["devs"]["tes"]["min_soc"] * soc_nom[n]["tes"],
                            name="min_cap_" + str(t))

            # SOC coupled over all times steps (Energy amount balance, kWh)
            model.addConstr(soc[n][dev][t] == soc_prev * eta_tes + dt[t] * (p_ch[n][dev][t] - p_dch[n][dev][t]),
                            name="Storage_bal_" + dev + "_" + str(t))

        # TODO: soc at the end is the same like at the beginning
        # if t == last_time_step:
        #    model.addConstr(soc[device][t] == soc_init[device],
        #                    name="End_TES_Storage_" + str(t))


    ## BAT CONSTRAINTS CONSTRAINTS
    dev = "bat"
    for n in nodes:
        k_loss = nodes[n]["devs"][dev]["k_loss"]
        for t in time_steps:
            # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
            if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init_rh[n][dev]
            elif t == par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init[n][dev]
            else:
                soc_prev = soc[n][dev][t - 1]

            # Maximal charging
            model.addConstr(p_ch[n]["bat"][t] <= y[n]["bat"][t] * nodes[n]["devs"]["bat"]["cap"] * nodes[n]["devs"]["bat"]["max_ch"],
                            name="max_ch_bat_" + str(t))
            # Maximal discharging
            model.addConstr(p_dch[n]["bat"][t] <= (1 - y[n]["bat"][t]) * nodes[n]["devs"]["bat"]["cap"] * nodes[n]["devs"]["bat"]["max_dch"],
                            name="max_dch_bat_" + str(t))

            # Minimal and maximal soc
            model.addConstr(soc[n]["bat"][t] <= nodes[n]["devs"]["bat"]["max_soc"] * nodes[n]["devs"]["bat"]["cap"],
                            name="max_soc_bat_" + str(t))
            model.addConstr(soc[n]["bat"][t] >= nodes[n]["devs"]["bat"]["min_soc"] * nodes[n]["devs"]["bat"]["cap"],
                            name="max_soc_bat_" + str(t))

            # SOC coupled over all times steps (Energy amount balance, kWh)
            model.addConstr(soc[n][dev][t] == (1 - k_loss) * soc_prev +
                            dt[t]* (nodes[n]["devs"][dev]["eta_bat"] * p_ch[n][dev][t] - 1 / nodes[n]["devs"][dev]["eta_bat"] *
                              p_dch[n][dev][t]),
                            name="Storage_balance_" + dev + "_" + str(t))

    ### EV CONSTRAINTS CONSTRAINTS
    dev = "ev"
    for n in nodes:
        for t in time_steps:
            # Initial SOC is the SOC at the beginning of the first time step, thus it equals the SOC at the end of the previous time step
            if t == par_rh["hour_start"][n_opt] and t > par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init_rh[n][dev]
            elif t == par_rh["month_start"][par_rh["month"]]:
                soc_prev = soc_init[n][dev]
            else:
                soc_prev = soc[n][dev][t - 1]

            # TODO:
            # if t == last_time_step:
            #    model.addConstr(soc_dom[device][n][t] == soc_init[device][n])

            # Maximal charging
            model.addConstr(p_ch[n][dev][t] <= (1 - y[n][dev][t]) * nodes[n]["devs"][dev]["max_ch_ev"],
                            name="Binary2_ev" + "_" + str(t))
            model.addConstr(p_ch[n][dev][t] <= demands[n]["EV_AVAIL"][t] * nodes[n]["devs"][dev]["max_ch_ev"])
            # Maximal discharging
            model.addConstr(p_dch[n][dev][t] <= y[n][dev][t] * nodes[n]["devs"][dev]["max_dch_ev"],
                            name="Binary1_ev" + "_" + str(t))
            model.addConstr(p_dch[n][dev][t] <= demands[n]["EV_AVAIL"][t] * nodes[n]["devs"][dev]["max_dch_ev"])
            # Minimal and maximal soc
            model.addConstr(soc[n][dev][t] >= nodes[n]["devs"][dev]["min_soc"] * nodes[n]["devs"][dev]["cap"])
            model.addConstr(soc[n][dev][t] <= nodes[n]["devs"][dev]["max_soc"] * nodes[n]["devs"][dev]["cap"])
            # SOC coupled over all times steps (Energy amount balance, kWh)
            model.addConstr(soc[n][dev][t] == soc_prev + p_ch[n][dev][t] * nodes[n]["devs"][dev]["eta_ch_ev"] * dt[t]
                                                       - p_dch[n][dev][t] / nodes[n]["devs"][dev]["eta_dch_ev"] * dt[t]
                                                       - demands[n]["EV_DEM_LEAVE"][t])

    # Electricity balance (house)
    for n in nodes:
        for t in time_steps:
            model.addConstr(demands[n]["elec"][t]
                            + p_ch[n]["bat"][t] - p_dch[n]["bat"][t]
                            + p_ch[n]["ev"][t] - p_dch[n]["ev"][t]
                            + power[n]["hp35"][t] + power[n]["hp55"][t] + power[n]["eh"][t]
                            - p_use[n]["chp"][t] - p_use[n]["pv"][t] - p_use[n]["bz"][t] - p_use[n]["bz_sf"][t]
                            == p_imp[n][t],
                            name="Electricity_balance_" + str(t))

    # Guarantee that just feed-in OR load is possible
    p_rated = {} # rated power of the house connection (elec)
    p_rated["MFH"] = 69282 # Kleinwandlermessung bis 100A
    p_rated["SFH/TH"] = 30484 # Direktmessung bis 44A

    for n in nodes:
        if nodes[n]["type"] == "MFH":
            ratedPower = p_rated["MFH"]
        else:
            ratedPower = p_rated["SFH/TH"]

        for t in time_steps:
            # TODO: net params
            model.addConstr(y[n]["house_load"][t] * ratedPower >= p_imp[n][t])  # Big M Methode --> Methodik
            model.addConstr(p_imp[n][t] >= 0)
            model.addConstr((1 - y[n]["house_load"][t]) * ratedPower >= p_sell[n]["pv"][t] + p_sell[n]["chp"][t] + p_sell[n]["bz"][t] + p_sell[n]["bz_sf"][t])

    # Split CHP and PV generation into self-consumed and sold powers
    for n in nodes:
        for dev in ("chp", "pv", "bz", "bz_sf"):
        #for dev in ("chp", "pv"):

            for t in time_steps:
                model.addConstr(p_sell[n][dev][t] + p_use[n][dev][t] == power[n][dev][t],
                                name="power=sell+use_" + dev + "_" + str(t))

    ### energy balance neighborhood

    # Residual loads
    for t in time_steps:
        # Residual network electricity demand (Power balance, MW)
        model.addConstr(residual["demand"][t] == sum(p_imp[n][t] for n in nodes))
        model.addConstr(residual["feed_pv"][t] == sum(p_sell[n]["pv"][t] for n in nodes))
        model.addConstr(residual["feed_chp"][t] == sum(p_sell[n]["chp"][t] + p_sell[n]["bz"][t] + p_sell[n]["bz_sf"][t] for n in nodes))
        model.addConstr(gas_dom[t] == sum(gas[n]["chp"][t] + gas[n]["boiler"][t] + gas[n]["bz"][t] + gas[n]["bz_sf"][t] for n in nodes),
                            name="Demand_gas_total")


    # %% ENERGY BALANCES: NETWORK AND ENERGY HUB
    ratedPowerTrafo = 400000 # 400 kVA
    for t in time_steps:
        # For all modes and scenarios:
        # Electricity balance neighborhood(Power balance, MW)
        model.addConstr(residual["feed_pv"][t] + residual["feed_chp"][t] + power["from_grid"][t] == residual["demand"][t] + power["to_grid"][t])

        model.addConstr(power["to_grid"][t] <= (residual["feed_pv"][t] + residual["feed_chp"][t]))
        model.addConstr(power["from_grid"][t] <= yTrafo[t] * ratedPowerTrafo,     name="Binary1_" + str(n) + "_" + str(t))
        model.addConstr(power["to_grid"][t] <= (1 - yTrafo[t]) * ratedPowerTrafo, name="Binary2_" + str(n) + "_" + str(t))

        # Gas balance (power)
        model.addConstr(power["gas_from_grid"][t] == sum(gas[n]["chp"][t] + gas[n]["boiler"][t] + gas[n]["bz"][t] + gas[n]["bz_sf"][t] for n in nodes))


    # Total gas amounts taken from grid (Energy amounts, MWh)
    model.addConstr(from_grid_total_gas ==  sum(dt[t] * power["gas_from_grid"][t] for t in time_steps))
    # Total electricity amounts taken from grid (Energy amounts, MWh)
    model.addConstr(from_grid_total_el ==  sum(dt[t] * power["from_grid"][t] for t in time_steps))
    # Total electricity feed-in (Energy amounts, MWh)
    model.addConstr(to_grid_total_el == sum(dt[t] * power["to_grid"][t] for t in time_steps))

    # Set solver parameters
    model.Params.TimeLimit = params["gp"]["time_limit"]
    model.Params.MIPGap = params["gp"]["mip_gap"]
    model.Params.MIPFocus = params["gp"]["numeric_focus"]
    IISconstr = []

    try:

        # Execute calculation
        model.optimize()
        #        model.write("model.ilp")

        # Write errorfile if optimization problem is infeasible or unbounded
        if model.status == gp.GRB.Status.INFEASIBLE or model.status == gp.GRB.Status.INF_OR_UNBD:

            model.computeIIS()
            f = open('errorfile_hp.txt', 'w')
            f.write('\nThe following constraint(s) cannot be satisfied:\n')
            for c in model.getConstrs():
                if c.IISConstr:
                    f.write('%s' % c.constrName)
                    f.write('\n')
                    IISconstr.append(c.constrName)
            f.close()

        # Retrieve results
        res_y = {}
        res_power = {}
        res_heat = {}
        res_soc = {}
        res_p_ch = {}
        res_p_dch = {}
        res_p_imp = {}
        res_gas = {}
        res_c_dem = {}
        res_soc_nom = {}
        res_p_use = {}
        res_p_sell = {}
        res_rev = {}
        for n in nodes:
            res_y[n] = {}
            res_power[n] = {}
            res_heat[n] = {}
            res_soc[n] = {}
            res_p_ch[n] = {}
            res_p_dch[n] = {}
            res_p_imp[n] = {}
            res_gas[n] = {}
            res_c_dem[n] = {}
            res_soc_nom[n] = {}
            res_p_use[n] = {}
            res_p_sell[n] = {}
            res_rev[n] = {}

            for dev in ["bat", "ev", "house_load"]:
                res_y[n][dev] = {(t): y[n][dev][t].X for t in time_steps}
            for dev in ["hp35", "hp55", "chp", "boiler", "bz", "bz_sf"]:
                res_power[n][dev] = {(t): power[n][dev][t].X for t in time_steps}
                res_heat[n][dev] = {(t): heat[n][dev][t].X for t in time_steps}
            for dev in ["pv"]:
                res_power[n][dev] = {(t): power[n][dev][t].X for t in time_steps}
            for dev in storage:
                res_soc[n][dev] = {(t): soc[n][dev][t].X for t in time_steps}
            for dev in storage:
                res_p_ch[n][dev] = {(t): p_ch[n][dev][t].X for t in time_steps}
                res_p_dch[n][dev] = {(t): p_dch[n][dev][t].X for t in time_steps}
            for dev in ["boiler", "chp", "bz", "bz_sf"]:
                res_gas[n][dev] = {(t): gas[n][dev][t].X for t in time_steps}
            for dev in ["boiler", "chp", "bz", "bz_sf"]:
                res_c_dem[n][dev] = {(t): params["eco"]["gas"] * gas[n][dev][t].X for t in time_steps}
            res_c_dem[n]["grid"] = {(t): p_imp[n][t].X * params["eco"]["pr", "el"] for t in time_steps}
            for dev in ["pv"]:
                res_rev[n][dev] = {(t): p_sell[n][dev][t].X * params["eco"]["sell_pv"] for t in time_steps}
            for dev in ["chp", "bz", "bz_sf"]:
                res_rev[n][dev] = {(t): p_sell[n][dev][t].X * params["eco"]["sell_chp"] for t in time_steps}
            res_soc_nom[n] = {dev: soc_nom[n][dev] for dev in storage}
            for dev in ("chp", "pv", "bz", "bz_sf"):
                res_p_use[n][dev] = {(t): p_use[n][dev][t].X for t in time_steps}
                res_p_sell[n][dev] = {(t): p_sell[n][dev][t].X for t in time_steps}
            res_p_imp[n] = {(t): p_imp[n][t].X for t in time_steps}

        res_p_to_grid = {(t): power["to_grid"][t].X for t in time_steps}
        res_p_from_grid = {(t): power["from_grid"][t].X for t in time_steps}
        res_gas_from_grid = {(t): power["gas_from_grid"][t].X for t in time_steps}
        res_p_feed_pv = {(t): residual["feed_pv"][t].X for t in time_steps}
        res_p_feed_chp = {(t): residual["feed_chp"][t].X for t in time_steps}
        res_p_demand = {(t): residual["demand"][t].X for t in time_steps}

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
        return (res_y, res_power, res_heat, res_soc,
                res_p_imp, res_p_ch, res_p_dch, res_p_use, res_p_sell,
                obj, res_c_dem, res_rev, res_soc_nom, nodes,
                objVal, runtime, soc_init_rh, dt, demands, res_p_from_grid,
                res_p_to_grid, res_gas_from_grid, res_p_feed_pv, res_p_demand, res_gas, res_p_feed_chp, 'feasible'), IISconstr

    except:
        print("Error: Presumably, more heat is provided than is needed due to the fuel cell.")

        return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'infeasible'), IISconstr

def compute_initial_values(opti_res, nodes, par_rh, n_opt):
    init_val = {}
    init_val["soc"] = {}
    # initial SOCs
    for n in nodes:
        init_val["soc"][n] = {}
        for dev in ["tes", "bat", "ev"]:
            init_val["soc"][n][dev] = opti_res[3][n][dev][par_rh["hour_start"][n_opt] + par_rh["n_hours"] - par_rh["n_hours_ov"]]

    return init_val