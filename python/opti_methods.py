#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import python.opti_bes as decentral_opti
import python.opti_bes_negotiation as opti_bes_nego # MA Lena
import python.opti_city as central_opti
import python.market_preprocessing as mar_pre
import python.market_preprocessing_nego as mar_pre_nego # MA Lena
import python.bidding_strategies as bd
import python.auction as auction
import python.characteristics as characs # MA Lena
import python.parse_inputs as parse_inputs
import python.matching_negotiation as mat_neg # MA Lena
import python.calc_results as calc_results

import fmpy
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result, download_test_file
from fmpy import *

def rolling_horizon_opti(options, nodes, par_rh, building_params, params, block_length):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the first bes optimization of each optimization step
    init_val_opti = {}  # used for SOC comparisons in case of an MPC
    tra_vol = {}        # to hand over the total bought/sold electricity of one time step
    soc_bat_fmu = {}    # SOC of the battery retrieved from the Modelica simulation
    soc_tes_fmu = {}    # SOC of the TES retrieved from the Modelica simulation
    soc_bat_opti = {}   # SOC from init_val, but percentual, not in kWh
    soc_diff_bat = {}       # difference between the simulation and optimization SOC
    soc_diff_tes = {}       # difference between the simulation and optimization SOC

    if options["optimization"] == "P2P":

        # range of prices for bids
        options["p_max"] = params["eco"]["pr", "el"]  # price for electricity bought from grid
        # options["p_min"] = params["eco"]["sell_chp"]  # price for electricity from CHP sold to grid
        options["p_min"] = params["eco"]["sell_pv"]  # price for electricity from PV sold to grid

        # compute market agents for prosumers (number of building energy system)
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(options, par_rh, nodes[n]))

        # needed market dicts
        mar_dict = mar_pre.dict_for_market_data(par_rh)

        # create bes for each building
        bes = mar_pre.bes(par_rh, options["nb_bes"])

        # create trade_res to store results
        trade_res = {}
        last_time_step = {}
        participating_buyers = {}
        participating_sellers = {}

        # create characteristics to store flexibility characteristics of each building
        characteristics = {}

        # calculate characteristics (Flexibilitätskennzahlen) Stinner et. al 2016
        # characteristics = characs.calc_characs(nodes, options, par_rh)

        # parameters for learning bidding strategy
        pars_li = parse_inputs.learning_bidding()
        # initiate propensities for learning intelligence agent
        if options["bid_strategy"] == "learning":
            mar_dict["propensities"][0], strategies = mar_pre.initial_prop(par_rh, options, pars_li)
        else:
            strategies = {}

                # FMU IMPORT AND INITIALIZATION
        #fmu_filename = 'FMU/Small_District_6houses_Boi.fmu'
        #fmu_filename = 'FMU/Small_District_8houses_HP_Boi.fmu'
        #fmu_filename = 'FMU/Small_District_8houses_HeatDemand_HP_Boi_constantinterpol.fmu'
        fmu_filename = 'FMU/Small_District_8houses_HeatDemand_HP_Boi_DHWCalc.fmu'
        #fmu_filename = 'FMU/Medium_District_13houses_HP_Boi_CHP.fmu'
        #fmu_filename = 'FMU/Small_District_6houses_Boi_DHWCalc.fmu'

        #start_time = 0 
        start_time = 3600 * par_rh["month_start"][par_rh["month"]]
        stop_time = 3600*24 # 1h in Sekunden
        #step_size = 3600  # Auflösung dyn. Sim; Communication Step size
        step_size = 60  # Auflösung dyn. Sim; Communication Step size

        # read the model description
        model_description = read_model_description(fmu_filename)

        # collect the value references (vr) for each variable
        vr = {}
        for variable in model_description.modelVariables:
            vr[variable.name] = variable.valueReference

        vr_traded_elec = []
        vr_soc_bat = []
        vr_soc_tes = []

        vr_grid_gen = []
        vr_grid_load = []
        vr_Tmax_tes = []
        vr_trade_check = []
        vr_heat_dem = []
        vr_hp_elec = []
        vr_elec_dem = []
        rows = []  # list to record the results
        grid_gen = []
        grid_load = []
        t_max = []
        trade_sold = []
        trade_bought = []
        hp_elec = []
        elec_dem = []
        

        # get the value references (vr) for the variables we want to get/set
        for house in range(1, options["nb_bes"]+1): # different index, as house enumeration in Modelica model start with "1"
            vr_traded_elec.append(vr['tra_vol_input' + str(house)])  # defines value reference for variable name
            if nodes[house-1]["devs"]["bat"]["cap"] != 0: #TODO Wahrscheinlich müssen die BAT Häuser zuerst kommen
                vr_soc_bat.append(vr['House'+ str(house) + '.electrical.distribution.batterySimple.SOC']) # defines value reference for variable name
            vr_soc_tes.append(vr['House'+ str(house) + '.hydraulic.distribution.soc_sto']) # defines value reference for variable name
            vr_grid_load.append(vr['House'+ str(house) + '.electricalGrid.PElecLoa']) # defines value reference for variable name
            vr_grid_gen.append(vr['House'+ str(house) + '.electricalGrid.PElecGen']) # defines value reference for variable name
            vr_Tmax_tes.append(vr['House'+ str(house) + '.hydraulic.distribution.stoBuf.TTop']) # defines value reference for variable name
            vr_trade_check.append(vr['House'+ str(house) + '.electrical.generation.tradingBus.tradedElec[1]']) # defines value reference for variable name
            vr_heat_dem.append(vr['House'+ str(house) + '.userProfiles.tabHeatDem.y[1]']) # defines value reference for variable name
            vr_elec_dem.append(vr['House'+ str(house) + '.userProfiles.tabElecDem.y[1]']) # defines value reference for variable name
            if nodes[house-1]["devs"]["hp35"]["cap"] != 0:
                vr_hp_elec.append(vr['House'+ str(house) + '.outputs.hydraulic.gen.PEleHeaPum.value']) # defines value reference for variable name
            else:
                vr_hp_elec.append(0) # defines value reference for variable name


        # extract the FMU
        unzipdir = extract(fmu_filename)

        fmu = FMU2Slave(guid=model_description.guid,
                        unzipDirectory=unzipdir,
                        modelIdentifier=model_description.coSimulation.modelIdentifier,
                        instanceName='instance1')

        # initialize
        fmu.instantiate()
        fmu.setupExperiment(startTime=start_time)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        # START OPTIMIZATION (Start optimizations for the first time step of the block bids)
        for n_opt in range(0, par_rh["n_opt"] - int(36/block_length)-1):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            trade_res[n_opt] = {}
            tra_vol[n_opt] = {}

            if n_opt == 0:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    init_val[n_opt]["building_" + str(n)] = {}
                    opti_res[n_opt][n] = decentral_operation(node=nodes[n], params=params, pars_rh=par_rh,
                                                             building_params=building_params,
                                                             init_val=init_val[n_opt]["building_" + str(n)],
                                                             n_opt=n_opt, options=options)

                    if options["negotiation"] == "False":
                        init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                                 par_rh, n_opt)
                    else: pass
            else:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(node=nodes[n], params=params, pars_rh=par_rh,
                                                             building_params=building_params,
                                                             init_val=init_val[n_opt]["building_" + str(n)],
                                                             n_opt=n_opt, options=options)
                    if options["negotiation"] == "False":
                        if n_opt < par_rh["n_opt"] - 1:
                            init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                                 par_rh, n_opt)
                        else:
                            init_val[n_opt + 1] = 0
                    else: pass
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) +
                  "% of optimizations processed.")

            # calculate new flexibility characteristics for length of block bids using the SOC from optimization results
            characteristics[n_opt] = characs.calc_characs(nodes=nodes, options=options, par_rh=par_rh,
                                                          block_length=block_length, opti_res=opti_res,
                                                          start_step=n_opt)

            # ----------------- P2P TRADING NEGOTIATION WITH BLOCK BIDS -----------------
            if options["negotiation"]:
                # compute the block bids for each building
                mar_dict["block_bids"][n_opt], bes = \
                    mar_pre_nego.compute_block_bids(bes=bes, opti_res=opti_res[n_opt], par_rh=par_rh,
                                                    mar_agent_prosumer=mar_agent_bes, n_opt=n_opt, options=options,
                                                    nodes=nodes, strategies=strategies, block_length=block_length)

                # separate bids in buying & selling, sort by crit (mean price/quantity or flexibility characteristic)
                mar_dict["sorted_bids"][n_opt], mar_dict["sell_list"][n_opt], mar_dict["buy_list"][n_opt] = \
                    mar_pre_nego.sort_block_bids(block_bid=mar_dict["block_bids"][n_opt], options=options,
                                                 characs=characteristics[n_opt], n_opt=n_opt, par_rh=par_rh)

                # match the block bids to each other according to crit
                mar_dict["matched_bids_info"][n_opt] \
                    = mat_neg.matching(sorted_block_bids=mar_dict["sorted_bids"][n_opt])

                # run negotiation optimization (with constraints adapted to matched peer) and save results
                (mar_dict["negotiation_results"][n_opt], participating_buyers[n_opt], participating_sellers[n_opt], mar_dict["sorted_bids_nego"][n_opt], last_time_step[n_opt],
                 mar_dict["matched_bids_info_nego"][n_opt]), opti_res[n_opt] \
                    = mat_neg.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                          init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                          matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                          sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                          opti_res=opti_res[n_opt])

                # trade the remaining power with the grid
                mar_dict["transactions_with_grid"][n_opt] = \
                    mat_neg.trade_with_grid(sorted_bids=mar_dict["sorted_bids"][n_opt], params=params, par_rh=par_rh,
                                            n_opt=n_opt, block_length=block_length, opti_res=opti_res[n_opt])


                time = 0
                if options["mpc"]: 
                    while time < 3600:
                        """
                        # Sum up the bought and sold energy quantities over the number of market rounds for every house using tra_vol
                        # As tra_vol is the direct control variable for the simulation de/increasing the BESMod electrical generation, it has to be negative for sellers
                        for house in range(0, options["nb_bes"]):
                            vol_sum = 0 # intermediate variable, as dicts cannot use the += method
                            tra_vol[n_opt][house] = {}
                            if house in participating_buyers[n_opt]:
                                l = list(mar_dict["transactions"][n_opt][house]["quantity"].values())
                                for i in range(len(l)): # number of rounds, the house participated in (the last round is mostly started without successful negotiations)
                                    vol_sum += l[i][par_rh["month_start"][par_rh["month"]] + n_opt] # sum of the total energy quantitiy of the current house
                                tra_vol[n_opt][house] = vol_sum
                            elif house in participating_sellers[n_opt]:
                                l = list(mar_dict["transactions"][n_opt][house]["quantity"].values())
                                for i in range(len(l)):
                                    vol_sum += l[i][par_rh["month_start"][par_rh["month"]] + n_opt]
                                tra_vol[n_opt][house] = -1 * vol_sum
                            else:
                                tra_vol[n_opt][house] = float(0)
                            #set the control variable for the simulation
                            fmu.setReal([vr_traded_elec[house]], [tra_vol[n_opt][house]]) 
                        """
                        # Sum up the bought and sold energy quantities over the number of market rounds for every house using tra_vol
                        # As tra_vol is the direct control variable for the simulation de/increasing the BESMod electrical generation, it has to be negative for sellers
                        for house in range(0, options["nb_bes"]):
                            tra_vol[n_opt][house] = {}
                            if house in participating_buyers[n_opt]:
                                tra_vol[n_opt][house] = opti_res[n_opt][house][19][par_rh["month_start"][par_rh["month"]] + n_opt]
                            elif house in participating_sellers[n_opt]:
                                tra_vol[n_opt][house] = -1 * opti_res[n_opt][house][19][par_rh["month_start"][par_rh["month"]] + n_opt]
                            else:
                                tra_vol[n_opt][house] = float(0)
                            #set the control variable for the simulation
                            fmu.setReal([vr_traded_elec[house]], [tra_vol[n_opt][house]]) 
                        # simulate one time step
                        fmu.doStep(currentCommunicationPoint=start_time + n_opt * 3600 + time, communicationStepSize=step_size) #TODO checken, ob das richtig ist als "time"-Ersatz
                        
                        # Test for the returned values from the FMU
                        no_house = 4 #in Modelica ist das Haus 5
                        input1, input2, input3, input4, input5, input6, input7 = fmu.getReal([vr_grid_gen[no_house], vr_grid_load[no_house], vr_Tmax_tes[no_house], vr_trade_check[no_house], vr_heat_dem[no_house], vr_hp_elec[no_house], vr_elec_dem[no_house]])
                        rows.append((n_opt, input1, input2, input3, input4, input5, input6, input7))
                        time += step_size

                    length = 96
                    if n_opt == length:
                        total_elec = []
                        for i in range(length * int(3600/step_size)):
                            grid_gen.append(rows[i][1]/1000) # change from Wh to kWh
                            grid_load.append(rows[i][2]/1000) # change from Wh to kWh
                            t_max.append(rows[i][3])
                            if rows[i][4] > 0:
                                trade_sold.append(0)
                                trade_bought.append(rows[i][4]/1000)
                            else:
                                trade_sold.append(rows[i][4]/1000)
                                trade_bought.append(0)
                            hp_elec.append(rows[i][6]/1000)
                            elec_dem.append(rows[i][7]/1000)
                            total_elec.append((rows[i][6]+rows[i][7])/1000)
                            #trade_check.append(rows[i][4]/1000) # change from Wh to kWh
                        plt.plot(grid_gen, label = 'feed-in', color = 'tab:blue')
                        plt.plot(grid_load, label = 'grid load', color = 'tab:orange')
                        plt.plot(trade_bought, label = 'bought electricity', color = 'tab:green')
                        plt.plot(trade_sold, label = 'sold electricity', color = 'tab:gray')
                        plt.legend()
                        plt.xticks(np.arange(0, length + 1, 1))
                        plt.xlabel('time in h')
                        plt.ylabel('electricity in kWh')
                        plt.show()
                        print("HI")

                        plt.clf()
                        plt.plot(trade_bought, label = 'bought electricity', color = 'tab:green')
                        plt.plot(hp_elec, label = 'heat pump electricity', color = 'tab:cyan')
                        plt.plot(elec_dem, label = 'electric load profile', color = 'tab:red')
                        plt.legend()
                        plt.xlabel('time in h')
                        plt.ylabel('electricity in kWh')
                        #plt.xticks(np.arange(0, length + 1, 1))
                        plt.show()
                        print("HI")

                        plt.clf()
                        plt.plot(trade_bought, label = 'bought electricity', color = 'tab:green')
                        plt.plot(total_elec, label = 'hp + elec demand', color = 'tab:red')
                        plt.legend()
                        plt.xlabel('time in h')
                        plt.ylabel('electricity in kWh')
                        #plt.xticks(np.arange(0, length + 1, 1))
                        plt.show()
                        print("HI")
                     

                    # create initial SoC values for next optimization step
                    # in the case of Co-Simulation, the SOC is retrieved from the Modelica simulation
                    # the standard method for the SOC initial_values is still used for a comparison of both values
                    soc_diff_bat[n_opt] = {}
                    soc_diff_tes[n_opt] = {}
                    soc_bat_fmu[n_opt] = {}
                    soc_tes_fmu[n_opt] = {}
                    
                    init_val_opti[n_opt + 1] \
                        = opti_bes_nego.compute_initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                                    last_time_step=last_time_step[n_opt],
                                                                    length_block_bid=block_length)
                    for n in range(options["nb_bes"]):
                        init_val[n_opt + 1]["building_" + str(n)] = {}
                        init_val[n_opt + 1]["building_" + str(n)]["soc"] = {}
                        # not every house owns BAT
                        soc_bat_fmu[n_opt][n] = {}
                        if nodes[n]["devs"]["bat"]["cap"] != 0:
                            soc_bat_fmu[n_opt][n] = fmu.getReal([vr_soc_bat[n]])
                            #if soc_bat_fmu[n_opt][n][0] > 0.95:
                                #soc_bat_fmu[n_opt][n][0] = 0.95
                            init_val[n_opt + 1]["building_" + str(n)]["soc"]["bat"] \
                                = soc_bat_fmu[n_opt][n][0] * opti_res[n_opt][n][12]["bat"] #SOC from simulation is percentual, optimization needs kWh
                        else:
                            init_val[n_opt + 1]["building_" + str(n)]["soc"]["bat"] \
                                = init_val_opti[n_opt + 1]["building_" + str(n)]["soc"]["bat"]
                        #for boiler systems, dont use the Modelica SOC_TES
                        #TODO nochmal klären!
                        if nodes[n]["devs"]["boiler"]["cap"] != 0.0:
                            init_val[n_opt + 1]["building_" + str(n)]["soc"]["tes"] \
                            = init_val_opti[n_opt + 1]["building_" + str(n)]["soc"]["tes"]
                        else:
                            soc_tes_fmu[n_opt][n] = fmu.getReal([vr_soc_tes[n]])
                            init_val[n_opt + 1]["building_" + str(n)]["soc"]["tes"] \
                            = soc_tes_fmu[n_opt][n][0] * opti_res[n_opt][n][12]["tes"] #SOC from simulation is percentual, optimization needs kWh
                        init_val[n_opt + 1]["building_" + str(n)]["soc"]["ev"] = 0 # no EVs examined
                        
                        if n_opt != 0:
                            if nodes[n]["devs"]["bat"]["cap"] != 0:
                                soc_diff_bat[n_opt][n] \
                                    = abs(soc_bat_fmu[n_opt][n] - init_val_opti[n_opt + 1]["building_" + str(n)]["soc"]["bat"]/opti_res[n_opt][n][12]["bat"])
                            if nodes[n]["devs"]["boiler"]["cap"] == 0.0:
                                soc_diff_tes[n_opt][n] \
                                    = abs(soc_tes_fmu[n_opt][n] - init_val_opti[n_opt + 1]["building_" + str(n)]["soc"]["tes"]/opti_res[n_opt][n][12]["tes"])
                else: 
                    # create initial SoC values for next optimization step
                    init_val[n_opt + 1] \
                        = opti_bes_nego.compute_initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                                    last_time_step=last_time_step[n_opt],
                                                                    length_block_bid=block_length)

            # ----------------- P2P TRADING WITH AUCTION AND SINGLE BIDS -----------------
            elif not options["negotiation"]:
                mar_dict["bid"][n_opt], bes = mar_pre.compute_bids(bes, opti_res[n_opt], par_rh, mar_agent_bes, n_opt,
                                                               options, nodes, init_val, mar_dict["propensities"][n_opt], strategies)

                # separate bids in buying and selling, sort by mean price, mean quantity or flexibility characteristic
                mar_dict["sorted_bids"][n_opt] = mar_pre.sort_bids(mar_dict["bid"][n_opt], options, characteristics[n_opt], n_opt)

                # run the auction with multiple trading rounds if "multi_round" is True in options
                if options["multi_round"]:
                   mar_dict["transactions"][n_opt], mar_dict["sorted_bids"][n_opt] = auction.multi_round(
                        mar_dict["sorted_bids"][n_opt], options["trading_rounds"])
                # otherwise run the auction with a single trading round
                else:
                    mar_dict["transactions"][n_opt], mar_dict["sorted_bids"][n_opt] = auction.single_round(
                        mar_dict["sorted_bids"][n_opt])

                # create categories in trade_res and set to 0
                for cat in ("revenue", "cost", "el_to_distr", "el_from_distr", "el_to_grid", "el_from_grid"):
                    trade_res[n_opt][cat] = {}
                    for nb in range(options["nb_bes"]):
                        trade_res[n_opt][cat][nb] = 0
                trade_res[n_opt]["average_trade_price"] = 0
                trade_res[n_opt]["total_cost_trades"] = 0
                trade_res[n_opt]["dem_total"] = 0
                trade_res[n_opt]["sup_total"] = 0

                # calculate traded volume
                trade_res[n_opt] = mar_pre.traded_volume(mar_dict["transactions"][n_opt], trade_res[n_opt])

                # calculate cost and revenue of transactions
                trade_res[n_opt] = mar_pre.cost_and_rev_trans(mar_dict["transactions"][n_opt], trade_res[n_opt])

                # calculate needs and surpluses that need to be fulfilled by grid
                bes = mar_pre.grid_demands(bes, trade_res[n_opt], options, mar_dict["bid"][n_opt], n_opt)

                # calculate volume, cost and revenue of buying/selling to grid
                trade_res[n_opt] = mar_pre.cost_and_rev_grid(bes, trade_res[n_opt], options, n_opt, params["eco"])

                # calculate new initial values, considering unfulfilled demands
                if options["flexible_demands"]:
                    init_val[n_opt + 1] = decentral_opti.initial_values_flex(opti_res[n_opt], par_rh, n_opt, nodes, options,
                                                                             trade_res[n_opt], init_val[n_opt])

                trade_res[n_opt]["dem_total"], trade_res[n_opt]["sup_total"] \
                    = mar_pre.total_sup_and_dem(opti_res[n_opt], par_rh, n_opt, options["nb_bes"])

                ## if there's next step:
                #if n_opt < par_rh["n_opt"] - 1:
                #    # update propensities
                #    if options["bid_strategy"] == "learning":
                #        mar_dict["propensities"][n_opt + 1] = mar_pre.update_prop(mar_dict, par_rh, n_opt, bes, options,
                #                                                                  pars_li, trade_res[n_opt], strategies)


        # ------------------ CALCULATE RESULTS ------------------
        results = calc_results.calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
        #res_time, res_val = 1,2

        return mar_dict, characteristics, init_val, results, opti_res

    elif options["optimization"] == "P2P_typeWeeks":
        # runs optimization for type weeks instead of whole month/year
        # TODO: implement changes made to opti for whole year such as flexible demands and multi round trading

        bid_strategy = "zero"

        # range of prices
        p_max = params["eco"]["pr", "el"]
        p_min = params["eco"]["sell_chp"]

        # compute market agents for prosumer
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh))

        # needed market dicts
        mar_dict = {}

        # create trade_res to store results
        trade_res = {}

        # Start optimizations

        index = list(range(options["number_typeWeeks"]))
        for k in index:

            # create market dicts
            mar_dict[k] = mar_pre.dict_for_market_data(par_rh)

            print(index)
            init_val[k] = {}
            opti_res[k] = {}
            trade_res[k] = {}

            for n_opt in range(par_rh["n_opt"]):

                opti_res[k][n_opt] = {}
                init_val[k][0] = {}
                init_val[k][n_opt+1] = {}
                trade_res[k][n_opt] = {}

                if n_opt == 0:
                    for n in range(options["nb_bes"]):
                        opti_res[k][n_opt][n] = {}
                        print("Starting optimization: type week: " + str(k)+ " n_opt: " + str(n_opt) + " building " + str(n) + ".")
                        init_val[k][n_opt]["building_" + str(n)] = {}
                        opti_res[k][n_opt][n]= decentral_operation(nodes[k][n],params, par_rh, building_params,
                                                              init_val[k][n_opt]["building_" + str(n)], n_opt, options)
                        init_val[k][n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[k][n_opt][n], par_rh, n_opt)
                else:
                    for n in range(options["nb_bes"]):
                        opti_res[k][n_opt][n] = {}
                        print("Starting optimization: type week: " + str(k)+ " n_opt: " + str(n_opt) + " building " + str(n) + ".")
                        opti_res[k][n_opt][n]= decentral_operation(nodes[k][n], params, par_rh, building_params,
                                                            init_val[k][n_opt]["building_" + str(n)], n_opt, options)
                        init_val[k][n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[k][n_opt][n], par_rh, n_opt)
                print("Finished optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ". " + str((par_rh["n_opt"]*k + n_opt+1) / (par_rh["n_opt"]* options["number_typeWeeks"]) * 100) + "% of optimizations processed.")

                # compute bids
                mar_dict[k]["bid"][n_opt] = mar_pre.compute_bids( opti_res[k][n_opt], par_rh, mar_agent_bes, n_opt, options)

                # separate bids in buying and selling and sort them
                mar_dict[k]["sorted_bids"][n_opt] = {}
                mar_dict[k]["sorted_bids"][n_opt] = mar_pre.sort_bids(mar_dict[k]["bid"][n_opt])

                # run the auction
                mar_dict[k]["transactions"][n_opt], mar_dict[k]["sorted_bids"][n_opt] = auction.single_round(mar_dict[k]["sorted_bids"][n_opt])

                # create categories in trade_res and set to 0
                for cat in ("revenue", "cost", "el_to_distr", "el_from_distr", "el_to_grid", "el_from_grid"):
                    trade_res[k][n_opt][cat] = {}
                    for nb in range(options["nb_bes"]):
                        trade_res[k][n_opt][cat][nb] = 0
                trade_res[k][n_opt]["average_trade_price"] = 0
                trade_res[k][n_opt]["total_cost_trades"] = 0

                # calculate cost and revenue of transactions
                trade_res[k][n_opt] = mar_pre.cost_and_rev(mar_dict[k]["transactions"][n_opt], trade_res[k][n_opt])

                # clear book by buying and selling from and to grid
                trade_res[k][n_opt], mar_dict[k]["sorted_bids"][n_opt] = mar_pre.clear_book(trade_res[k][n_opt], mar_dict[k]["sorted_bids"][n_opt], params)

        # change structure of results to be sorted by res instead of building
        opti_res_new = {}
        for k in range(options["number_typeWeeks"]):
            opti_res_new[k] = {}
            for n_opt in range(par_rh["n_opt"]):
                opti_res_new[k][n_opt] = {}
                for i in range(18):
                    opti_res_new[k][n_opt][i] = {}
                    for n in range(options["nb_bes"]):
                        opti_res_new[k][n_opt][i][n] = {}
                        opti_res_new[k][n_opt][i][n] = opti_res[k][n_opt][n][i]

        return opti_res_new, index, mar_dict, trade_res


def infeasible_model_adjust_fuel_cell_configuration(k, nodes, options, index_typeweeks, IISconstr):

    return nodes, index_typeweeks


def decentral_operation(node, params, pars_rh, building_params, init_val, n_opt, options):

    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """
           
    opti_res = decentral_opti.compute(node=node, params=params, par_rh=pars_rh, building_param=building_params,
                                      init_val=init_val, n_opt=n_opt, options=options)

    return opti_res


def init_val_decentral_operation(opti_bes, par_rh, n_opt):

    init_val = decentral_opti.compute_initial_values(opti_bes, par_rh, n_opt)

    return init_val


def central_operation(nodes, params, pars_rh, building_params, init_val, n_opt, options):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_res = central_opti.compute(nodes, params, pars_rh, building_params, init_val, n_opt, options)

    return opti_res


def init_val_central_operation(opti_res, nodes, par_rh, n_opt):
    init_val = central_opti.compute_initial_values(opti_res, nodes, par_rh, n_opt)

    return init_val
