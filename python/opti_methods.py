#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import numpy as np
import python.opti_bes as decentral_opti
import python.opti_bes_negotiation as opti_bes_nego
import python.opti_city as central_opti
import python.market_preprocessing as mar_pre
import python.market_preprocessing_nego as mar_pre_nego
import python.bidding_strategies as bd
import python.auction as auction
import python.characteristics as characs
import python.parse_inputs as parse_inputs
import python.matching_negotiation as mat_neg
from python import matching_negotiation


def rolling_horizon_opti(options, nodes, par_rh, building_params, params, block_length):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the first bes optimization of each optimization step

    if options["optimization"] == "P2P":

        # range of prices for bids
        options["p_max"] = params["eco"]["pr", "el"]  # price for electricity bought from grid
        options["p_min"] = params["eco"]["sell_chp"]  # price for electricity from CHP sold to grid

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




        # START OPTIMIZATION (Start optimizations for the first time step of the block bids)
        for n_opt in range(0, par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            trade_res[n_opt] = {}

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


            # calculate new flexibility characteristics for 3 steps using the SOC from optimization results
            characteristics[n_opt] = characs.calc_characs(nodes=nodes, options=options, par_rh=par_rh,
                                                          block_length=block_length, opti_res=opti_res,
                                                          start_step=n_opt)

            # P2P TRADING NEGOTIATION WITH BLOCK BIDS
            if options["negotiation"] == True:

                # compute the block bids for each building
                mar_dict["block_bid"][n_opt], bes = \
                    mar_pre_nego.compute_block_bids(bes=bes, opti_res=opti_res[n_opt], par_rh=par_rh,
                                                    mar_agent_prosumer=mar_agent_bes, n_opt=n_opt, options=options,
                                                    nodes=nodes, strategies=strategies, block_length=block_length)

                # separate bids in buying & selling, sort by crit (mean price/quantity or flexibility characteristic)
                mar_dict["sorted_bids"][n_opt] = \
                    mar_pre_nego.sort_block_bids(block_bid=mar_dict["block_bid"][n_opt], options=options,
                                                 new_characs=characteristics[n_opt],
                                                 n_opt=n_opt, par_rh=par_rh, opti_res=opti_res[n_opt])

                # match the block bids to each other according to crit
                mar_dict["matched_bids_info"][n_opt] \
                    = mat_neg.matching(block_bids=mar_dict["sorted_bids"][n_opt], n_opt=n_opt) #, mar_dict["unmatched_bids"][n_opt]

                # run negotiation optimization (with constraints adapted to matched peer) and save results
                mar_dict["negotiation_results"][n_opt], mar_dict["total_market_info"][n_opt], last_time_step[n_opt]\
                    = mat_neg.negotiation(nodes=nodes, params=params, par_rh=par_rh,
                                          init_val=init_val[n_opt], n_opt=n_opt, options=options,
                                          matched_bids_info=mar_dict["matched_bids_info"][n_opt],
                                          block_bids=mar_dict["block_bid"][n_opt], block_length=block_length)

                # create initial SoC values for next optimization step
                init_val[n_opt + 1] \
                    = opti_bes_nego.compute_initial_values_block(nb_buildings=options["nb_bes"],
                                                                 opti_res=opti_res[n_opt],
                                                                 nego_transactions=mar_dict["negotiation_results"][n_opt],
                                                                 last_time_step=last_time_step[n_opt])





            # P2P TRADING WITH AUCTION AND SINGLE BIDS
            elif options["negotiation"] == False:
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

                # if there's next step:
                if n_opt < par_rh["n_opt"] - 1:
                    # update propensities
                    if options["bid_strategy"] == "learning":
                        mar_dict["propensities"][n_opt + 1] = mar_pre.update_prop(mar_dict, par_rh, n_opt, bes, options,
                                                                                  pars_li, trade_res[n_opt], strategies)

                # change structure of results to be sorted by res instead of building
                # from opti_res[n_opt][building][result category] to new_opti_res[n_opt][result category][building]
                opti_res_new = {}
                for n_opt in range(par_rh["n_opt"]):
                    opti_res_new[n_opt] = {}
                    for i in range(18): # 18 is the number of result categories in opti_bes
                        # if number of result categories changes, this needs to be changed as well!!!
                        opti_res_new[n_opt][i] = {}
                        for n in range(options["nb_bes"]):
                            opti_res_new[n_opt][i][n] = {}
                            opti_res_new[n_opt][i][n] = opti_res[n_opt][n][i]

        # return opti_res_new, mar_dict, trade_res, characteristics  #opti_res,
        return mar_dict, characteristics, init_val

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
