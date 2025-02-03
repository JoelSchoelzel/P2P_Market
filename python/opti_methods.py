#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import python.opti_bes as decentral_opti
import python.opti_bes_negotiation as opti_bes_nego # MA Lena
import python.block_bids as block_bids # MA Lena
import python.market_agents as market_agents
import python.characteristics as characs # MA Lena
import python.market as market # MA Lena
import python.calc_results as calc_results
import python.opti_css as sharing_opti


def rolling_horizon_opti(options, nodes, par_rh, building_params, params, block_length, districtData, devs_pre_opti):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the first bes optimization of each optimization step
    opti_res_check = {}
    opti_res_css = {}

    if options["optimization"] == "P2P":

        # range of prices for bids
        options["p_max"] = params["eco"]["pr", "el"]  # price for electricity bought from grid
        options["p_min"] = params["eco"]["sell_pv"]  # price for electricity from PV sold to grid

        # compute market agents for prosumers (number of building energy system)
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(market_agents.mar_agent_bes(options, n))

        # todo Ray: compute market agents for central supply system
        mar_agent_css = market_agents.mar_agent_css(options, districtData)

        # Creates a dictionary to store information about market activities.
        mar_dict = {
            "block_bids": {},
            "sell_list": {},
            "buy_list": {},
            "sorted_bids": {},
            # todo: put "matched_bids_info" and "matched_bids_info_nego" in one --> start here with r=0 and in negotiation with r=1
            "matched_bids_info": {},
            # "matched_bids_info_nego": {},
            "negotiation_results": {},
            "transactions_with_grid": {},
            "q_tables": {}
        }

        # create trade_res to store results
        trade_res = {}
        last_time_step = {}

        # create characteristics to store flexibility characteristics (Stinner et. al 2016) of each building
        characteristics = {}

        # START OPTIMIZATION (Start optimizations for the first time step of the block bids)
        for n_opt in range(0, par_rh["n_opt"] - int(36/block_length)-1):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            trade_res[n_opt] = {}
            mar_dict["sorted_bids"][n_opt] = {}
            mar_dict["matched_bids_info"][n_opt] = {}
            opti_res_css[n_opt] = {}
            if options["central_supply_system"]:
                matched_bids = {}
                prev_traded = {}
                trading_price = {}
                res_soc_prev = mar_agent_css.bat_capacity * 0.1
                for t in par_rh["time_steps"][n_opt][0:block_length]:
                    matched_bids = {0: {t: {1: [0]}}, 1: {t: {1: [0]}}}
                    prev_traded = {t: 0}
                    trading_price = {t: options["p_min"]}

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
                        init_val[n_opt + 1]["css"] = init_val_sharing_operation(opti_res[n_opt], par_rh, n_opt)
                    else: pass
                # todo Ray: add sharing operation here, adjust init_val for sharing operation?
                init_val[n_opt]["css"] = {}
                #opti_res_css[n_opt] = sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded, trading_price, block_length, opti_res, options)
                if options["central_supply_system"]:
                    print("Starting optimization: n_opt: " + str(n_opt) + ", central supply system:")
                    matched_bids = {}
                    prev_traded = {}
                    trading_price = {}
                    res_soc_prev = mar_agent_css.bat_capacity * 0.1
                    for t in par_rh["time_steps"][n_opt][0:block_length]:
                        matched_bids = {0: {t: {1: [0]}}, 1: {t: {1: [0]}}}
                        prev_traded = {t: 0}
                        trading_price = {t: options["p_min"]}
                    opti_res_css[n_opt] = (
                        sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded,
                                          trading_price, block_length, opti_res, options, res_soc_prev))
            else: # for all next optimization steps n_opt > 0
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(node=nodes[n], params=params, pars_rh=par_rh,
                                                             building_params=building_params,
                                                             init_val=init_val[n_opt]["building_" + str(n)],
                                                             n_opt=n_opt, options=options)

                    # todo Ray: add sharing operation here, adjust init_val for sharing operation?
                    if options["negotiation"] == "False":
                        if n_opt < par_rh["n_opt"] - 1:
                            init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                                 par_rh, n_opt)
                            init_val[n_opt + 1]["css"] = init_val_sharing_operation(opti_res[n_opt], par_rh, n_opt)
                        else:
                            init_val[n_opt + 1] = 0
                    else: pass
                # todo Ray: add sharing operation here, adjust init_val for sharing operation?
                if options["central_supply_system"]:
                    # gather information about matched bids and previous trading round
                    print("Starting optimization: n_opt: " + str(n_opt) + ", central supply system:")
                    matched_bids = {}
                    prev_traded = {}
                    trading_price = {}
                    res_soc_prev = mar_agent_css.bat_capacity * 0.1
                    for t in par_rh["time_steps"][n_opt][0:block_length]:
                        res_soc_prev = opti_res_css[n_opt - 1]["res_soc"]["s_bat"][t - 1]
                        matched_bids = {t: 0}
                        prev_traded = {t: 0}
                        trading_price = {t: 0}
                    if len(mar_dict["matched_bids_info"][n_opt]) > 0: #todo: what if more than one round for CSS? consider r?
                        for match in range(len(mar_dict["matched_bids_info"][n_opt][0])):
                            for t in par_rh["time_steps"][n_opt][0:block_length]:
                                matched_bids = mar_dict["matched_bids_info"][n_opt][0][match]
                                prev_traded = mar_dict["negotiation_results"][n_opt][0][match]["trading_quantity"]
                                trading_price = mar_dict["negotiation_results"][n_opt][0][match][
                                    "trading_price"]  # todo: need correct trading price from negotiation results
                    opti_res_css[n_opt] = (
                        sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded,
                                          trading_price, block_length, opti_res, options, res_soc_prev))
            #opti_res_check[n_opt] = copy.deepcopy(opti_res[n_opt])
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) +
                  "% of optimizations processed.")

            # calculate new flexibility characteristics for length of block bids using the SOC from optimization results
            if options["central_supply_system"]:
                characteristics[n_opt] = characs.calc_characs(nodes=nodes, options=options, par_rh=par_rh,
                                                              block_length=block_length, opti_res=opti_res,
                                                              start_step=n_opt, opti_res_css=opti_res_css,
                                                              mar_agent_css=mar_agent_css)
            else:
                characteristics[n_opt] = characs.calc_characs(nodes=nodes, options=options, par_rh=par_rh,
                                                              block_length=block_length, opti_res=opti_res,
                                                              start_step=n_opt)

            # ----------------- P2P TRADING NEGOTIATION WITH BLOCK BIDS -----------------
            if options["negotiation"]:
                # compute the block bids for each building
                mar_dict["block_bids"][n_opt] = \
                    block_bids.compute_block_bids(opti_res=opti_res[n_opt], par_rh=par_rh,
                                                  mar_agent_bes=mar_agent_bes, n_opt=n_opt, options=options,
                                                  block_length=block_length, mar_dict=mar_dict,
                                                  devs_pre_opti=devs_pre_opti, nodes=nodes)
                # todo: create block bids for CSS and trade with prosumers
                mar_dict["block_bids"][n_opt] = (
                    block_bids.compute_block_bids_css(par_rh, n_opt, options, block_length, opti_res_css,
                                                      mar_dict["block_bids"][n_opt], mar_agent_css))

                # ------------------- SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS ------------------- #
                mar_dict["buy_list"][n_opt], mar_dict["sell_list"][n_opt] = \
                    block_bids.seperate_block_bids(block_bid=mar_dict["block_bids"][n_opt],
                                                   characs=characteristics[n_opt])

                # sort bids by criteria (mean price/quantity or flexibility characteristic)
                mar_dict["sorted_bids"][n_opt] = \
                    block_bids.sort_block_bids(options, buy_list=mar_dict["buy_list"][n_opt],
                                               sell_list=mar_dict["sell_list"][n_opt],
                                               sorted_bids=mar_dict["sorted_bids"][n_opt],
                                               r=False, par_rh=par_rh, n_opt=n_opt, block_length=block_length)

                # match the block bids to each other according to crit
                mar_dict["matched_bids_info"][n_opt][0] = market.matching(sorted_bids=mar_dict["sorted_bids"][n_opt][0])

                # run negotiation optimization (with constraints adapted to matched peer) and save results
                if options["central_supply_system"]:
                    (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids"][n_opt],
                     mar_dict["matched_bids_info"][n_opt]), opti_res[n_opt] \
                        = market.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                             init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                             matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                             sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                             opti_res=opti_res[n_opt], opti_res_css=opti_res_css[n_opt],
                                             mar_agent_css=mar_agent_css)
                else:
                    (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids"][n_opt],
                     mar_dict["matched_bids_info"][n_opt]), opti_res[n_opt] \
                        = market.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                              init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                              matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                              sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                              opti_res=opti_res[n_opt], opti_res_css=opti_res_css[n_opt])

                # ------------------- TRADE WITH CSS ------------------- #
                # todo: Ray: Insert css opti here, use bids and offers from previous step as input for opti_css
                # todo Ray: trade with css
                #if options["central_supply_system"]:
                    # gather information about matched bids and previous trading round
                    #matched_bids = {}
                    #prev_traded = {}
                    #trading_price = {}
                    #res_soc_prev = mar_agent_css.bat_capacity * 0.1
                    #for t in par_rh["time_steps"][n_opt][0:block_length]:
                    #    matched_bids = {0: {t: {1: [0]}}, 1: {t: {1: [0]}}}
                    #    prev_traded = {t: 0}
                    #    trading_price = {t: options["p_min"]}
                    #if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    #    for match in range(len(mar_dict["matched_bids_info"][n_opt][0])):
                    #        matched_bids = mar_dict["matched_bids_info"][n_opt][0][match]
                    #        prev_traded = mar_dict["negotiation_results"][n_opt][0][match]["trading_quantity"]
                    #        trading_price = mar_dict["negotiation_results"][n_opt][0][match][
                    #                "trading_price"]  # todo: need correct trading price from negotiation results
                    #if n_opt > 0:
                    #    for t in par_rh["time_steps"][n_opt][0:block_length]:
                    #        res_soc_prev = opti_res_css[n_opt - 1]["res_soc"]["s_bat"][t - 1]

                    #opti_res_css[n_opt] = (
                    #    sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded,
                    #                      trading_price, block_length, opti_res, options, res_soc_prev))

                    # create dict to store initial values of CSS
                    #init_val[n_opt]["css"] = {"soc": {"s_bat": {}}}
                    #init_val[n_opt]["css"]["soc"]["s_bat"] = opti_res_css[n_opt]["res_soc"]["s_bat"]

                    # todo: create block bids for CSS and trade with prosumers
                    #mar_dict["block_bids"][n_opt] = (
                    #    block_bids.compute_block_bids_css(par_rh, n_opt, options, block_length, opti_res_css,
                    #                                      mar_dict["block_bids"][n_opt], mar_agent_css))

                    # todo: negotiation between prosumers and CSS
                    #mar_dict["negotiation_results_with_css"] = {n_opt: {}}
                    # mar_dict["negotiation_results_with_css"][n_opt] = (
                    #     market.negotiation_with_css())

                # ------------------- TRADE WITH GRID ------------------- #
                if options["central_supply_system"]:
                    mar_dict["transactions_with_grid"][n_opt] = \
                        market.trade_with_grid(params=params, par_rh=par_rh, n_opt=n_opt,
                                               block_length=block_length, opti_res=opti_res[n_opt],
                                               options=options, opti_res_css=opti_res_css[n_opt])
                else:
                    mar_dict["transactions_with_grid"][n_opt] = \
                        market.trade_with_grid(params=params, par_rh=par_rh, n_opt=n_opt,
                                                block_length=block_length, opti_res=opti_res[n_opt], options=options)

                # todo ray: update q-tables of BES agents here, see below
                # update q-tables of BES and CSS agents after each negotiation round
                if options["bid_strategy"] == "q_learning":
                    for n in range(options["nb_bes"]):
                        mar_agent_bes[n]["q_table"] = (
                            mar_agent_bes[n].calc_reward_and_update_q_table(options, nodes, n, par_rh, n_opt,
                                                                            block_length, opti_res, mar_dict))
                        mar_dict["q_tables"][n] = mar_agent_bes[n]["q_table"]
                    # update q-tables of BES agents after each negotiation round
                    # for n in range(options["nb_bes"]):
                    #     reward1 = reward2 = reward3 = reward4 = 0
                    #     new_buy_quant = 0
                    #     new_sell_quant = 0
                    #     eta_tes = nodes[n]["devs"]["tes"]["eta_tes"]
                    #     for t in par_rh["time_steps"][n_opt][0:block_length]:
                    #         current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                    #         ch_tes = opti_res[n_opt][n][5]["tes"][t]
                    #         dch_tes = opti_res[n_opt][n][6]["tes"][t]
                    #     new_soc = max(0, current_soc * eta_tes + (ch_tes - dch_tes) / opti_res[n_opt][n][12]["tes"])
                    #     for t in par_rh["time_steps"][n_opt][0:block_length]:
                    #         # get the inputs for reward calculation
                    #         buying = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][2]
                    #
                    #         # get remaining demand and remaining supply
                    #         if buying == "True":  # when buying
                    #             # look for the matched bid and find the matched buying quantity
                    #             remaining_demand = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                    #             if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    #                 match_nr = None
                    #                 for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                    #                     if mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == n:
                    #                         match_nr = match
                    #                         break
                    #                         # todo: check if this is correct
                    #                 if match_nr is not None:
                    #                     remaining_demand = mar_dict["negotiation_results"][n_opt][0][match_nr][
                    #                         "remaining_demand"][t]
                    #             new_buy_quant = remaining_demand
                    #         elif buying == "False":  # when selling
                    #             remaining_supply = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                    #             # look for the matched bid and find the matched buying quantity
                    #             if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    #                 match_nr = None
                    #                 # todo: check if this is correct
                    #                 for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                    #                     if mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == n:
                    #                         match_nr = match
                    #                         break
                    #                         # todo: check if this is correct
                    #                 if match_nr is not None:
                    #                     remaining_supply = mar_dict["negotiation_results"][n_opt][0][match_nr][
                    #                         "remaining_supply"][t]
                    #             new_sell_quant = remaining_supply
                    #
                    #         # calculate new SoC
                    #         if opti_res[n_opt][n][12]["bat"] == 0:  # if battery doesn't exist
                    #             current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                    #             eta_tes = nodes[n]["devs"]["tes"]["eta_tes"]
                    #             ch_tes = opti_res[n_opt][n][5]["tes"][t]
                    #             dch_tes = opti_res[n_opt][n][6]["tes"][t]
                    #             new_soc = max(0, current_soc * eta_tes + (ch_tes - dch_tes) / opti_res[n_opt][n][12][
                    #                 "tes"])
                    #             # todo: how to correctly calculate new soc for TES?
                    #         else:  # if battery exist
                    #             current_soc = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]
                    #             eta_bat = nodes[n]["devs"]["bat"]["eta_bat"]
                    #             ch_bat = opti_res[n_opt][n][5]["bat"][t]
                    #             dch_bat = opti_res[n_opt][n][6]["bat"][t]
                    #             k_loss = nodes[n]["devs"]["bat"]["k_loss"]
                    #             new_soc = (1 - k_loss) * current_soc + eta_bat * (ch_bat - dch_bat) / opti_res[n_opt][n][12]["bat"]
                    #             #if buying == "True":
                    #             #    new_soc = current_soc - eta_bat * (match_buying_quantity + pv_gen - elec_demand)
                    #             #elif buying == "False":
                    #             #    new_soc = current_soc + eta_bat * ( - match_selling_quantity + pv_gen - elec_demand)
                    #             #else:
                    #             #    new_soc = current_soc
                    #
                    #         # state q_match and p_match default (when no match found)
                    #         q_match = 0
                    #         if buying == "True":
                    #             p_match = options["p_max"] - 0.001
                    #         elif buying == "False":
                    #             p_match = options["p_min"] + 0.001
                    #         else:
                    #             p_match = 0
                    #         # if any negotiation results exist, get the trading price and quantity
                    #         if len(mar_dict["negotiation_results"][n_opt][0]) > 0:
                    #             match_nr = None
                    #             for match in mar_dict["negotiation_results"][n_opt][0]: # find match number
                    #                 if (mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == n or
                    #                         mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == n):
                    #                     match_nr = match # Store the match number/key
                    #                     break # Exit the loop as the desired match is found
                    #
                    #             if match_nr is not None: # Access trading_price for the respective match
                    #                 p_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_price"][t]
                    #                 q_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_quantity"][t]
                    #
                    #         q_dem = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                    #
                    #         if len(mar_dict["sell_list"][n_opt]) > 0:
                    #             p_min_sell = min(mar_dict["sell_list"][n_opt][n]["mean_price"]
                    #                              for n in range(len(mar_dict["sell_list"][n_opt])))
                    #         else:
                    #             p_min_sell = options["p_max"] - 0.001
                    #         if len(mar_dict["buy_list"][n_opt]) > 0:
                    #             p_max_buy = max(mar_dict["buy_list"][n_opt][n]["mean_price"]
                    #                             for n in range(len(mar_dict["buy_list"][n_opt])))
                    #         else:
                    #             p_max_buy = options["p_min"] + 0.001
                    #         if opti_res[n_opt][n][12]["bat"] != 0:
                    #             soc_state = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]
                    #         else:
                    #             soc_state = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                    #
                    #         # calculate reward
                    #         reward1 = mar_agent_bes[n].calc_reward_q_learning_v1(buying, p_match, q_match, q_dem)
                    #         reward2 = mar_agent_bes[n].calc_reward_q_learning_v2(buying, p_min_sell, p_max_buy, p_match,
                    #                                                              soc_state)
                    #         reward3 = mar_agent_bes[n].calc_reward_q_learning_v3(buying, p_match, q_match, q_dem,
                    #                                                              soc_state)
                    #         reward4 = mar_agent_bes[n].calc_reward_q_learning_v4(buying, p_match, q_match, q_dem,
                    #                                                              soc_state)
                    #         #reward1 += reward1  # sum up rewards for t in n_opt
                    #         #reward2 += reward2
                    #
                    #     # update q-table
                    #     mar_agent_bes[n]["q_table"] = (
                    #         mar_agent_bes[n].
                    #         update_q_table_q_learning(action=mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][0],
                    #                                   reward=reward4,
                    #                                   new_buy_quant=new_buy_quant, new_sell_quant=new_sell_quant,
                    #                                   new_soc=new_soc))
                    #
                    #     mar_dict["q_tables"][n] = mar_agent_bes[n]["q_table"]

                    # update q-tables of CSS agent after each negotiation round
                    if options["central_supply_system"]:
                        mar_agent_css.q_table = (
                            mar_agent_css.calc_reward_and_update_q_table(options, opti_res_css, par_rh, n_opt,
                                                                         block_length, mar_dict))
                        mar_dict["q_tables"]["css"] = mar_agent_css.q_table
                    # # update q-tables of CSS agent after each negotiation round
                        # p_match = 0.5 * (options["p_max"] + options["p_min"])
                        # q_match = 0
                        # p_min_sell = options["p_max"] - 0.001
                        # p_max_buy = options["p_min"] + 0.001
                        # t = par_rh["time_steps"][n_opt][0]
                        # soc_state = opti_res_css[n_opt]["res_soc"]["s_bat"][t] / mar_agent_css.bat_capacity  # SoC %
                        # buying = mar_dict["block_bids"][n_opt]["css"][t][2]
                        # q_dem = mar_dict["block_bids"][n_opt]["css"][t][1]
                        #
                        # for t in par_rh["time_steps"][n_opt][0:block_length]:
                        #     # get the inputs for reward calculation
                        #     # buying = mar_dict["block_bids"][n_opt]["css"][t][2]
                        #     # q_dem = mar_dict["block_bids"][n_opt]["css"][t][1]
                        #     if len(mar_dict["buy_list"][n_opt]) > 0:  # if any buying bid exists
                        #         # get the minimum price of all buying bids
                        #         p_min_sell = min(mar_dict["buy_list"][n_opt][bid]["mean_price"]
                        #                          for bid in range(len(mar_dict["buy_list"][n_opt])))
                        #     if len(mar_dict["sell_list"][n_opt]) > 0:  # if any selling offer exists
                        #         p_max_buy = max(mar_dict["sell_list"][n_opt][bid]["mean_price"]
                        #                         for bid in range(len(mar_dict["sell_list"][n_opt])))
                        #
                        #     # find the matched bid and find the matched buying/selling quantity
                        #     # if any negotiation results exist, get the trading price and quantity
                        #     if len(mar_dict["negotiation_results"][n_opt][0]) > 0:
                        #         match_nr = None
                        #         for match in range(len(mar_dict["negotiation_results"][n_opt][0])):  # find match number
                        #             if (mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == options["nb_bes"] or
                        #                     mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == options["nb_bes"]):
                        #                 match_nr = match # Store the match number/key
                        #                 break # Exit the loop as the desired match is found
                        #
                        #         if match_nr is not None: # Access trading_price for the respective match
                        #             p_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_price"][t]
                        #             q_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_quantity"][t]
                        #
                        # # calc reward for CSS agent
                        # reward_CSS1 = mar_agent_css.calc_reward_q_learning_v1(buying, p_match, q_match, q_dem)
                        # reward_CSS2 = mar_agent_css.calc_reward_q_learning_v2(buying, p_min_sell, p_max_buy, p_match,
                        #                                                       soc_state)
                        #
                        # # Calculate new buying/selling quantity & SoC
                        # new_buy_quant = 0
                        # new_sell_quant = 0
                        # new_soc = 0
                        # for t in par_rh["time_steps"][n_opt][0:block_length]:
                        #     # get remaining demand and remaining supply
                        #     if buying == "True":  # when buying
                        #         # look for the matched bid and find the matched buying quantity
                        #         remaining_demand = mar_dict["block_bids"][n_opt]["css"][t][1]
                        #         if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                        #             match_nr = None
                        #             for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        #                 if (mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] ==
                        #                         options["nb_bes"]):
                        #                     match_nr = match
                        #                     break
                        #             if match_nr is not None: # if match is found
                        #                 remaining_demand = mar_dict["negotiation_results"][n_opt][0][match_nr][
                        #                     "remaining_demand"][t]
                        #         new_buy_quant = remaining_demand
                        #     elif buying == "False":  # when selling
                        #         remaining_supply = mar_dict["block_bids"][n_opt]["css"][t][1]
                        #         # look for the matched bid and find the matched buying quantity
                        #         if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                        #             match_nr = None
                        #             # todo: check if this is correct
                        #             for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        #                 if (mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] ==
                        #                         options["nb_bes"]):
                        #                     match_nr = match
                        #                     break
                        #                     # todo: check if this is correct
                        #             if match_nr is not None:
                        #                 remaining_supply = mar_dict["negotiation_results"][n_opt][0][match_nr][
                        #                     "remaining_supply"][t]
                        #         new_sell_quant = remaining_supply
                        #
                        #     # calculate new SoC
                        #     current_soc = soc_state
                        #     eta_bat = mar_agent_css.bat_eta
                        #     ch_bat = opti_res_css[n_opt]["res_p_ch"]["s_bat"][t]
                        #     dch_bat = opti_res_css[n_opt]["res_p_dch"]["s_bat"][t]
                        #     k_loss = mar_agent_css.k_loss
                        #     new_soc = (1 - k_loss) * current_soc + eta_bat * (ch_bat - dch_bat) / mar_agent_css.bat_capacity
                        #
                        # # update q-table
                        # mar_agent_css.q_table = (
                        #     mar_agent_css.update_q_table_q_learning(action=mar_dict["block_bids"][n_opt]["css"][t][0],
                        #                                             reward=reward_CSS2, new_buy_quant=new_buy_quant,
                        #                                             new_sell_quant=new_sell_quant, new_soc=new_soc))

                # create initial SoC values for next optimization step
                init_val[n_opt + 1] \
                    = opti_bes_nego.initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                         block_bid_time_steps=par_rh["time_steps"][n_opt][0:block_length],
                                                         length_block_bid=block_length, opti_res_css=opti_res_css,
                                                         n_opt=n_opt)
                if options["central_supply_system"]:
                    # create dict to store initial values of CSS
                    init_val[n_opt + 1]["css"] = {"soc": {"s_bat": {}}}
                    init_val[n_opt + 1]["css"]["soc"]["s_bat"] = opti_res_css[n_opt]["res_soc"]["s_bat"]

                # save q-tables after each negotiation round
                #if options["bid_strategy"] == "q_learning":
                #    for n in range(options["nb_bes"]):
                #        mar_agent_bes[n]["q_table"].to_csv("q_table_bes_" + str(n) + ".csv")
                #    mar_agent_css["q_table"].to_csv("q_table_css.csv")

        # ------------------ CALCULATE RESULTS ------------------
        results = calc_results.calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, opti_res_check=opti_res_check,
                                                grid_transaction=mar_dict["transactions_with_grid"],
                                                params=params, options=options, opti_res_css=opti_res_css)
        #res_time, res_val = 1,2

        return mar_dict, characteristics, init_val, results, opti_res, opti_res_check


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


# todo: Ray: implement function for sharing operation with central supply system
def sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt,
                      matched_bids, prev_traded, trading_price, block_length, opti_res, options, res_soc_prev):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_css = sharing_opti.compute(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded,
                                    trading_price, block_length, opti_res, options, res_soc_prev)

    return opti_css

def init_val_sharing_operation(opti_res, nodes, par_rh, n_opt):
    init_val = sharing_opti.compute_initial_values(opti_res, nodes, par_rh, n_opt)

    return init_val