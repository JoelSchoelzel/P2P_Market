#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import python.opti_bes as decentral_opti
import python.opti_bes_negotiation as opti_bes_nego # MA Lena
import python.market_preprocessing as mar_pre
import python.block_bids as block_bids # MA Lena
import python.bidding_strategies as bd
import python.auction as auction
import python.characteristics as characs # MA Lena
import python.parse_inputs as parse_inputs
import python.matching_negotiation as mat_neg # MA Lena
import python.calc_results as calc_results




def rolling_horizon_opti(options, nodes, par_rh, building_params, params, block_length):
    """ Run rolling horizon """
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the first bes optimization of each optimization step
    opti_res_check = {}
    trade_res = {}   # create trade_res to store results
    last_time_step = {}

    # range of prices for bids
    options["p_max"] = params["eco"]["pr", "el"]  # price for electricity bought from grid
    options["p_min"] = params["eco"]["sell_pv"]  # price for electricity from PV sold to grid

    # compute market agents for prosumers (number of building energy system)
    mar_agent_bes = []
    for n in range(options["nb_bes"]):
        mar_agent_bes.append(bd.mar_agent_bes(options, par_rh, nodes[n]))

    # create market dict for market data during trading and negotiation
    mar_dict = mar_pre.dict_for_market_data(par_rh)

    # create dictionary to store information about the inflexible demands and traded amounts of the building.
    bes = mar_pre.bes(par_rh, options["nb_bes"])

    # create characteristics to store flexibility characteristics (Stinner et. al 2016) of each building
    characteristics = {}

    # parameters for learning bidding strategy
    pars_li = parse_inputs.learning_bidding()
    # initiate propensities for learning intelligence agent
    if options["bid_strategy"] == "learning":
        mar_dict["propensities"][0], strategies = mar_pre.initial_prop(par_rh, options, pars_li)
    else:
        strategies = {}

    # START OPTIMIZATION (Start optimizations for the first time step of the block bids)
    for n_opt in range(0, par_rh["n_opt"] - int(36/block_length)-1):
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

        # opti_res_check[n_opt] = copy.deepcopy(opti_res[n_opt])
        print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) +
                "% of optimizations processed.")

        # calculate flexibility characteristics for length of block bids using the SOC from optimization results
        characteristics[n_opt] = characs.calc_characs(nodes=nodes, options=options, par_rh=par_rh,
                                                      block_length=block_length, opti_res=opti_res,
                                                      start_step=n_opt)

        # ----------------- P2P TRADING NEGOTIATION WITH BLOCK BIDS -----------------
        if options["negotiation"]:
            # compute the block bids for each building
            mar_dict["block_bids"][n_opt], bes = \
                block_bids.compute_block_bids(bes=bes, opti_res=opti_res[n_opt], par_rh=par_rh,
                                                    mar_agent_prosumer=mar_agent_bes, n_opt=n_opt, options=options,
                                                    nodes=nodes, strategies=strategies, block_length=block_length)

            # separate bids in buying & selling, sort by crit (mean price/quantity or flexibility characteristic)
            mar_dict["sorted_bids"][n_opt], mar_dict["sell_list"][n_opt], mar_dict["buy_list"][n_opt] = \
                    block_bids.sort_block_bids(block_bid=mar_dict["block_bids"][n_opt], options=options,
                                                 characs=characteristics[n_opt], n_opt=n_opt, par_rh=par_rh)

            # match the block bids to each other according to crit
            mar_dict["matched_bids_info"][n_opt] \
                    = mat_neg.matching(sorted_block_bids=mar_dict["sorted_bids"][n_opt])

            # run negotiation optimization (with constraints adapted to matched peer) and save results
            (mar_dict["negotiation_results"][n_opt], mar_dict["sorted_bids_nego"][n_opt], last_time_step[n_opt],
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
                                            opti_res=opti_res, opti_res_check= opti_res_check,
                                            grid_transaction=mar_dict["transactions_with_grid"],
                                            params = params)

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
