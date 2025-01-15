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
    opti_css = {}

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
            opti_css[n_opt] = {}

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
                        #init_val[n_opt + 1]["building_" + str(n)] = init_val_sharing_operation(opti_res[n_opt][n],
                        #                                                                         par_rh, n_opt)
                    else: pass
                # todo Ray: add sharing operation here, adjust init_val for sharing operation?
                #init_val[n_opt]["css"] = {}
                #opti_css[n_opt] = sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, block_length, opti_res, options)
            else:
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
                            #init_val[n_opt + 1]["building_" + str(n)] = init_val_sharing_operation(opti_res[n_opt][n],
                            #                                                                         par_rh, n_opt)
                        else:
                            init_val[n_opt + 1] = 0
                    else: pass
                # todo Ray: add sharing operation here, adjust init_val for sharing operation?
                #init_val[n_opt]["css"] = {}
                #opti_css[n_opt] = sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, block_length, opti_res, options)
            #opti_res_check[n_opt] = copy.deepcopy(opti_res[n_opt])
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) +
                  "% of optimizations processed.")

            # calculate new flexibility characteristics for length of block bids using the SOC from optimization results
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

                # ------------------- SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS ------------------- #
                mar_dict["sell_list"][n_opt], mar_dict["buy_list"][n_opt] = \
                    block_bids.seperate_block_bids(block_bid=mar_dict["block_bids"][n_opt],
                                                   characs=characteristics[n_opt])

                # sort bids by criteria (mean price/quantity or flexibility characteristic)
                mar_dict["sorted_bids"][n_opt] = \
                    block_bids.sort_block_bids(options, buy_list=mar_dict["buy_list"][n_opt],
                                               sell_list=mar_dict["sell_list"][n_opt],
                                               sorted_bids=mar_dict["sorted_bids"][n_opt],
                                               r=False)

                # match the block bids to each other according to crit
                mar_dict["matched_bids_info"][n_opt][0] = market.matching(sorted_bids=mar_dict["sorted_bids"][n_opt][0])

                # run negotiation optimization (with constraints adapted to matched peer) and save results
                (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids"][n_opt],
                 mar_dict["matched_bids_info"][n_opt]), opti_res[n_opt] \
                    = market.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                          init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                          matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                          sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                          opti_res=opti_res[n_opt])

                # ------------------- TRADE WITH CSS ------------------- #
                # todo: Ray: Insert css opti here, use bids and offers from previous step as input for opti_css
                # todo Ray: trade with css
                #opti_res_css[n_opt] = opti_css.compute(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids,
                #                                       prev_traded, trading_price, block_length)

                # trade the remaining power with the grid
                mar_dict["transactions_with_grid"][n_opt] = \
                    market.trade_with_grid(params=params, par_rh=par_rh, n_opt=n_opt,
                                            block_length=block_length, opti_res=opti_res[n_opt])

                # todo ray: update q-tables of BES agents here, see below
                # update q-tables of BES agents after each negotiation round
                if options["bid_strategy"] == "q_learning":
                    for n in range(options["nb_bes"]):
                        for t in par_rh["time_steps"][n_opt][0:block_length]:
                            buying = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][2]
                            pv_gen = nodes[n]["pv_power"][t]
                            elec_demand = nodes[n]["elec"][t]
                            if buying == "True":  # when buying
                                for i in range(0, 2): # look for the matched bid and find the matched buying quantity
                                    if [0] in mar_dict["matched_bids_info"][n_opt][0] and mar_dict["matched_bids_info"][n_opt][0][0][i]["bes_id"] == n:
                                        match_buying_quantity = min(mar_dict["matched_bids_info"][n_opt][0][0][i]["quantity"] for i in range(0, 2)) # todo: check if this is correct
                                    else:
                                        match_buying_quantity = 0
                                prev_buying_quantity = opti_res[n_opt][n][4]["p_imp"][t]
                                new_buy_quant = prev_buying_quantity - match_buying_quantity
                                new_sell_quant = 0
                                if opti_res[n_opt][n][12]["bat"] == 0:  # if battery doesn't exist
                                    current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                                    new_soc = current_soc
                                else:  # if battery exist
                                    current_soc = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]
                                    eta_bat = nodes[n]["devs"]["bat"]["eta_bat"]
                                    new_soc = current_soc + eta_bat * (match_buying_quantity + pv_gen - elec_demand)

                            elif buying == "False":  # when selling
                                for i in range(0, 2): # look for the matched bid and find the matched buying quantity
                                    if ([0] in mar_dict["matched_bids_info"][n_opt][0] and
                                            mar_dict["matched_bids_info"][n_opt][0][0][i]["bes_id"] == n):
                                        match_selling_quantity = (
                                            min(mar_dict["matched_bids_info"][n_opt][0][0][i]["quantity"] for i in range(0, 2))) # todo: check if this is correct
                                    else:
                                        match_selling_quantity = 0
                                prev_selling_quantity = opti_res[n_opt][n][8]["chp"][t] + opti_res[n_opt][n][8]["pv"][t]
                                new_buy_quant = 0
                                new_sell_quant = prev_selling_quantity - match_selling_quantity
                                if opti_res[n_opt][n][12]["bat"] == 0:  # if battery doesn't exist
                                    current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                                    new_soc = current_soc
                                else:  # if battery exist
                                    current_soc = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]
                                    eta_bat = nodes[n]["devs"]["bat"]["eta_bat"]
                                    new_soc = current_soc - eta_bat * (match_selling_quantity + pv_gen - elec_demand)
                            if any(result == [0] for result in mar_dict["negotiation_results"][n_opt][0]): # if any negotiation results exist
                                p_match = mar_dict["negotiation_results"][n_opt][0][0]["trading_price"] # todo: need correct trading price from negotiation results
                                q_match = mar_dict["negotiation_results"][n_opt][0][0]["trading_quantity"]
                            else:
                                p_match = 0
                                q_match = 0
                            q_dem = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                            if any(result == [n] for result in mar_dict["buy_list"][n_opt]):
                                p_min_sell = min(mar_dict["buy_list"][n_opt][n]["mean_price"] for n in range(options["nb_bes"]))
                            else: p_min_sell = options["p_min"]
                            if any(result == [n] for result in mar_dict["sell_list"][n_opt]):
                                p_max_buy = max(mar_dict["sell_list"][n_opt][n]["mean_price"] for n in range(options["nb_bes"]))
                            else: p_max_buy = options["p_max"]
                            soc_state = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"] if opti_res[n_opt][n][12]["bat"] != 0 \
                                else opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]

                            # calculate reward
                            reward1 = mar_agent_bes[n].calc_reward_q_learning_v1(buying, p_match, q_match, q_dem)
                            reward2 = mar_agent_bes[n].calc_reward_q_learning_v2(buying, p_min_sell, p_max_buy, p_match,
                                                                                 soc_state)

                            reward1 += reward1 # sum up rewards for t in n_opt
                            reward2 += reward2

                        # update q-table
                        mar_agent_bes[n]["q_table"] = (
                            mar_agent_bes[n].
                            update_q_table_q_learning(action=mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][0],
                                                      reward=reward2,
                                                      new_buy_quant=new_buy_quant, new_sell_quant=new_sell_quant,
                                                      new_soc=new_soc))

                # create initial SoC values for next optimization step
                init_val[n_opt + 1] \
                    = opti_bes_nego.initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                         block_bid_time_steps=par_rh["time_steps"][n_opt][0:block_length],
                                                         length_block_bid=block_length)

        # ------------------ CALCULATE RESULTS ------------------
        results = calc_results.calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, opti_res_check= opti_res_check,
                                                grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
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
                      block_length, opti_res, options):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_css = sharing_opti.compute(mar_agent_css, params, par_rh, init_val, n_opt, block_length, opti_res, options)

    return opti_css

def init_val_sharing_operation(opti_res, nodes, par_rh, n_opt):
    init_val = sharing_opti.compute_initial_values(opti_res, nodes, par_rh, n_opt)

    return init_val