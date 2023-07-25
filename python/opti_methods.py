#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import numpy as np
import python.opti_bes as decentral_opti
import python.opti_city as central_opti
import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import python.auction as auction
import python.characteristics as characs


def rolling_horizon_opti(options, nodes, par_rh, building_params, params):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the bes optimization

    if options["optimization"] == "P2P":

        # range of prices for bids
        p_max = params["eco"]["pr", "el"]  # price for electricity bought from gird
        p_min = params["eco"]["sell_chp"]  # price for electricity from CHP sold to grid

        # compute market agents for prosumers
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh, nodes[n]))

        # needed market dicts
        mar_dict = mar_pre.dict_for_market_data(par_rh)

        # create bes for each building
        bes = mar_pre.bes(par_rh, options["nb_bes"])

        # create trade_res to store results
        trade_res = {}

        # calculate characteristics
        characteristics = characs.calc_characs(nodes, options, par_rh)

        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            trade_res[n_opt] = {}

            if n_opt == 0:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    init_val[n_opt]["building_" + str(n)] = {}
                    opti_res[n_opt][n] = decentral_operation(nodes[n], params, par_rh, building_params,
                                                             init_val[n_opt]["building_" + str(n)], n_opt, options)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                             par_rh, n_opt)
            else:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(nodes[n], params, par_rh, building_params,
                                                             init_val[n_opt]["building_" + str(n)], n_opt, options)
                    if n_opt < par_rh["n_opt"] - 1:
                        init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                                 par_rh, n_opt)
                    else:
                        init_val[n_opt + 1] = 0
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) +
                  "% of optimizations processed.")

            # compute bids
            mar_dict["bid"][n_opt], bes = mar_pre.compute_bids(bes, opti_res[n_opt], par_rh, mar_agent_bes, n_opt,
                                                               options, nodes, init_val)
            # separate bids in buying and selling, sort by price
            mar_dict["sorted_bids"][n_opt] = mar_pre.sort_bids(mar_dict["bid"][n_opt], options, characteristics, n_opt)

            # run the auction with multiple trading rounds if "multi_round" is True in options
            if options["multi_round"]:
                mar_dict["transactions"][n_opt], mar_dict["sorted_bids"][n_opt] = auction.multi_round(
                    mar_dict["sorted_bids"][n_opt])
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

        # change structure of results to be sorted by res instead of building
        # from opti_res[n_opt][building][result category] to new_opti_res[n_opt][result category][building]
        opti_res_new = {}
        for n_opt in range(par_rh["n_opt"]):
            opti_res_new[n_opt] = {}
            for i in range(18):
                opti_res_new[n_opt][i] = {}
                for n in range(options["nb_bes"]):
                    opti_res_new[n_opt][i][n] = {}
                    opti_res_new[n_opt][i][n] = opti_res[n_opt][n][i]

        return opti_res_new, mar_dict, trade_res, characteristics

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
           
    opti_res = decentral_opti.compute(node, params, pars_rh, building_params, init_val, n_opt, options)

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
