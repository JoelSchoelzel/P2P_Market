#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division

from numpy.ma.extras import average

import python.opti_bes as decentral_opti
import python.opti_bes_negotiation as opti_bes_nego  # MA Lena
import python.opti_css_negotiation as opti_css_nego  # MA Ray
import python.block_bids as block_bids  # MA Lena
import python.market_agents as market_agents
import python.characteristics as characs  # MA Lena
import python.market as market  # MA Lena
import python.calc_results as calc_results
import python.opti_css as opti_css  # MA Ray


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

        mar_agent_css = None
        if options["central_supply_system"]:
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
            "q_tables": {},
            "CSS_profiles": {}
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

            t = par_rh["time_steps"][n_opt][0]
            # matched_bids = {0: {t: {1: [0]}}, 1: {t: {1: [0]}}}
            # prev_traded = {t: 0}
            trading_price = {t: 0.5 * (options["p_min"] + options["p_max"])}

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
                        # init_val[n_opt + 1]["css"] = init_val_sharing_operation(opti_res[n_opt], par_rh, n_opt)
                    else:
                        pass
                if options["central_supply_system"]:
                    init_val[n_opt]["css"] = {}
                    print("Starting optimization: n_opt: " + str(n_opt) + ", central supply system:")
                    res_soc_prev = mar_agent_css.bat_capacity * 0.1
                    opti_res_css[n_opt] = (
                        sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt,
                                          trading_price, block_length, opti_res, options, res_soc_prev))
            else:  # for all next optimization steps n_opt > 0
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
                            # init_val[n_opt + 1]["css"] = init_val_sharing_operation(opti_res[n_opt], par_rh, n_opt)
                        else:
                            init_val[n_opt + 1] = 0
                    else:
                        pass
                if options["central_supply_system"]:
                    # gather information about matched bids and previous trading round
                    print("Starting optimization: n_opt: " + str(n_opt) + ", central supply system:")
                    t = par_rh["time_steps"][n_opt][0]
                    res_soc_prev = opti_res_css[n_opt - 1]["res_soc"]["s_bat"][t - 1]
                    # if len(mar_dict["matched_bids_info"][n_opt]) > 0: #todo: what if more than one round for CSS? consider r?
                    #     for match in range(len(mar_dict["matched_bids_info"][n_opt][0])):
                    #         matched_bids = mar_dict["matched_bids_info"][n_opt][0][match] # todo: this is always empty? need the last match instead
                    #         prev_traded = mar_dict["negotiation_results"][n_opt][0][match]["trading_quantity"]
                    #         trading_price = mar_dict["negotiation_results"][n_opt][0][match]["trading_price"]  # todo: need correct trading price from negotiation results
                    opti_res_css[n_opt] = (
                        sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt, trading_price,
                                          block_length, opti_res, options, res_soc_prev))
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

            # # Update q-tables of BES and CSS agents from previous optimization
            # if n_opt > 0:
            #     if options["bid_strategy"] == "q_learning":
            #         for n in range(options["nb_bes"]):
            #             mar_agent_bes[n]["q_table"] = \
            #                 mar_agent_bes[n].calc_reward_and_update_q_table3(options, nodes, n, par_rh, n_opt,
            #                                                                 block_length, opti_res, mar_dict)
            #             mar_dict["q_tables"][n] = mar_agent_bes[n]["q_table"]
            #
            #         # update q-tables of CSS agent after each negotiation round
            #         if options["central_supply_system"]:
            #             mar_agent_css.q_table = \
            #                 mar_agent_css.calc_reward_and_update_q_table3(options, opti_res_css, par_rh, n_opt,
            #                                                              block_length, mar_dict)
            #             mar_dict["q_tables"]["css"] = mar_agent_css.q_table

            # ----------------- P2P TRADING NEGOTIATION WITH BLOCK BIDS -----------------
            if options["negotiation"]:
                # compute the block bids for each building
                mar_dict["block_bids"][n_opt] = \
                    block_bids.compute_block_bids(opti_res=opti_res[n_opt], par_rh=par_rh,
                                                  mar_agent_bes=mar_agent_bes, n_opt=n_opt, options=options,
                                                  block_length=block_length, mar_dict=mar_dict,
                                                  devs_pre_opti=devs_pre_opti, nodes=nodes)
                # create block bids for CSS
                if options["central_supply_system"]:
                    mar_dict["block_bids"][n_opt] = \
                        block_bids.compute_block_bids_css(par_rh, n_opt, options, block_length, opti_res_css,
                                                          mar_dict["block_bids"][n_opt], mar_agent_css)

                # ------------------- SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS ------------------- #
                mar_dict["buy_list"][n_opt], mar_dict["sell_list"][n_opt] = \
                    block_bids.seperate_block_bids(block_bid=mar_dict["block_bids"][n_opt],
                                                   characs=characteristics[n_opt])

                # sort bids by criteria (mean price/quantity or flexibility characteristic)
                mar_dict["sorted_bids"][n_opt] = \
                    block_bids.sort_block_bids(options, buy_list=mar_dict["buy_list"][n_opt],
                                               sell_list=mar_dict["sell_list"][n_opt],
                                               sorted_bids=mar_dict["sorted_bids"][n_opt],
                                               r=None, par_rh=par_rh, n_opt=n_opt, block_length=block_length)

                # match the block bids to each other according to crit (here, for first matching round only)
                if options["price_based_matching"]:
                    mar_dict["matched_bids_info"][n_opt][0] = market.matching_price_check(sorted_bids=mar_dict["sorted_bids"][n_opt][0])
                else:
                    mar_dict["matched_bids_info"][n_opt][0] = market.matching(sorted_bids=mar_dict["sorted_bids"][n_opt][0])

                # run negotiation optimization (with constraints adapted to matched peer), next mathing rounds, and save results
                if options["central_supply_system"]:
                    (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids"][n_opt],
                     mar_dict["matched_bids_info"][n_opt]), opti_res[n_opt], opti_res_css[n_opt] \
                        = market.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                             init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                             matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                             sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                             opti_res=opti_res[n_opt], opti_res_css=opti_res_css[n_opt],
                                             mar_agent_css=mar_agent_css)
                else:
                    (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids"][n_opt],
                     mar_dict["matched_bids_info"][n_opt]), opti_res[n_opt], opti_res_css[n_opt] \
                        = market.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                              init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                              matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                              sorted_bids=mar_dict["sorted_bids"][n_opt], block_length=block_length,
                                              opti_res=opti_res[n_opt], opti_res_css=opti_res_css[n_opt])

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

                # update q-tables of BES and CSS agents after each negotiation round
                if options["bid_strategy"] == "q_learning":
                    for n in range(options["nb_bes"]):
                        mar_agent_bes[n]["q_table"] = \
                            mar_agent_bes[n].calc_reward_and_update_q_table_indiv(options, nodes, n, par_rh, n_opt,
                                                                             block_length, opti_res, mar_dict)
                        mar_dict["q_tables"][n] = mar_agent_bes[n]["q_table"]

                    # update q-tables of CSS agent after each negotiation round
                    if options["central_supply_system"]:
                        # mar_agent_css.q_table = \
                        #     mar_agent_css.calc_reward_and_update_q_table_indiv(options, opti_res_css, par_rh, n_opt,
                        #                                                  block_length, mar_dict)
                        mar_agent_css.q_table = \
                            mar_agent_css.calc_reward_and_update_q_table_LEM(options, opti_res_css, par_rh, n_opt,
                                                                          block_length, mar_dict, opti_res)
                        mar_dict["q_tables"]["css"] = mar_agent_css.q_table

                # create initial SoC values for next optimization step
                if not options["central_supply_system"]:
                    init_val[n_opt + 1] \
                        = opti_bes_nego.initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                             block_bid_time_steps=par_rh["time_steps"][n_opt][0:block_length],
                                                             length_block_bid=block_length)
                elif options["central_supply_system"]:
                    init_val[n_opt + 1] \
                        = opti_css_nego.initial_values_block(nb_buildings=options["nb_bes"], opti_res=opti_res[n_opt],
                                                             block_bid_time_steps=par_rh["time_steps"][n_opt][0:block_length],
                                                             length_block_bid=block_length, opti_res_css=opti_res_css,
                                                             n_opt=n_opt)
                    # create dict to store initial values of CSS
                    #init_val[n_opt + 1]["css"] = {"soc": {"s_bat": {}}}
                    #init_val[n_opt + 1]["css"]["soc"]["s_bat"] = opti_res_css[n_opt]["res_soc"]["s_bat"]

                # save q-tables after each negotiation round
                #if options["bid_strategy"] == "q_learning":
                #    for n in range(options["nb_bes"]):
                #        mar_agent_bes[n]["q_table"].to_csv("q_table_bes_" + str(n) + ".csv")
                #    mar_agent_css["q_table"].to_csv("q_table_css.csv")

        # Save wind and PV profiles in mar_dict
        if options["CSS_Wind"]:
            mar_dict["CSS_profiles"]["wind_power"] = mar_agent_css.wind_power
        if options["CSS_PV"]:
            mar_dict["CSS_profiles"]["pv_power"] = mar_agent_css.pv_power

        # ------------------ CALCULATE RESULTS ------------------
        results = calc_results.calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, opti_res_check=opti_res_check,
                                                grid_transaction=mar_dict["transactions_with_grid"],
                                                params=params, options=options, opti_res_css=opti_res_css,
                                                mar_agent_bes=mar_agent_bes, mar_agent_css=mar_agent_css)
        # res_time, res_val = 1,2

        return mar_dict, characteristics, init_val, results, opti_res, opti_res_check, opti_res_css


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


def sharing_operation(mar_agent_css, params, par_rh, init_val, n_opt,
                      trading_price, block_length, opti_res, options, res_soc_prev):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_res_css = opti_css.compute(mar_agent_css, params, par_rh, init_val, n_opt,
                                    trading_price, block_length, opti_res, options, res_soc_prev)

    return opti_res_css

def init_val_sharing_operation(opti_res, nodes, par_rh, n_opt):
    init_val = opti_css.compute_initial_values(opti_res, nodes, par_rh, n_opt)

    return init_val