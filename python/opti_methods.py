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
import python.stackelberg as stack

def rolling_horizon_opti(options, nodes, par_rh, building_params, params):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the bes optimization

    if options["optimization"] == "decentral":
        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            if n_opt == 0:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" +str(n) + ".")
                    init_val[n_opt]["building_" + str(n)] = {}
                    opti_res[n_opt][n] = decentral_operation(nodes[n],params, par_rh,
                                                              building_params,
                                                              init_val[n_opt]["building_" + str(n)], n_opt, options)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                         par_rh, n_opt)
            else:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(nodes[n], params, par_rh,
                                                              building_params,
                                                              init_val[n_opt]["building_" + str(n)], n_opt, options)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n], par_rh, n_opt)
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) + "% of optimizations processed.")
        return opti_res

    elif options["optimization"] == "central":
        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            if n_opt == 0:
                print("Starting optimization: n_opt: " + str(n_opt) + ".")
                init_val[n_opt] = {}
                opti_res[n_opt] = central_operation(nodes,params, par_rh, building_params,
                                                      init_val[n_opt], n_opt, options)
                init_val[n_opt + 1] = init_val_central_operation(opti_res[n_opt], nodes, par_rh, n_opt)
            else:
                print("Starting optimization: n_opt: " + str(n_opt) + ".")
                opti_res[n_opt] = central_operation(nodes, params, par_rh, building_params,
                                                      init_val[n_opt], n_opt, options)
                init_val[n_opt + 1] = init_val_central_operation(opti_res[n_opt], nodes, par_rh, n_opt)
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) + "% of optimizations processed.")
        return opti_res

    elif options["optimization"] == "central_typeWeeks":
        # Start optimizations

        index = list(range(options["number_typeWeeks"]))
        for k in index:
            print(index)
            init_val[k] = {}
            opti_res[k] = {}
            for n_opt in range(par_rh["n_opt"]):

                opti_res[k][n_opt] = {}
                init_val[k][0] = {}
                init_val[k][n_opt+1] = {}
                if n_opt == 0:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    init_val[k][n_opt] = {}
                    opti_res[k][n_opt], IISconstr = central_operation(nodes[k],params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)
                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                else:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    opti_res[k][n_opt], IISconstr = central_operation(nodes[k], params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)

                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                print("Finished optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ". " + str((par_rh["n_opt"]*k + n_opt+1) / (par_rh["n_opt"]* options["number_typeWeeks"]) * 100) + "% of optimizations processed.")
        return opti_res, index

    elif options["optimization"] == "decentral_typeWeeks":
        # Start optimizations

        index = list(range(options["number_typeWeeks"]))
        for k in index:
            print(index)
            init_val[k] = {}
            opti_res[k] = {}
            for n_opt in range(par_rh["n_opt"]):

                opti_res[k][n_opt] = {}
                init_val[k][0] = {}
                init_val[k][n_opt+1] = {}
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

        #change struture of results to be sorted by res instead of building
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

        return opti_res_new, index

    elif options["optimization"] == "P2P":

        bid_strategy = "zero"

        # range of prices
        p_max = params["eco"]["pr", "el"]
        p_min = params["eco"]["sell_chp"]

        # compute market agents for prosumer
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh))

        # needed market dicts
        mar_dict = mar_pre.dict_for_market_data(par_rh)

        # create trade_res to store results
        trade_res = {}

        #calculate characteristics
        print("Calculate characteristics...")
        characteristics = characs.calc_characs(nodes, options, par_rh)
        print("Finished calculating characteristics!")



        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            trade_res[n_opt] = {}

            if n_opt == 0:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" +str(n) + ".")
                    init_val[n_opt]["building_" + str(n)] = {}
                    opti_res[n_opt][n] = decentral_operation(nodes[n],params, par_rh,
                                                              building_params,
                                                              init_val[n_opt]["building_" + str(n)], n_opt, options)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                         par_rh, n_opt)
            else:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(nodes[n], params, par_rh, building_params,
                                                             init_val[n_opt]["building_" + str(n)], n_opt, options)
                    if n_opt < par_rh["n_opt"] - 1:
                        init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n], par_rh, n_opt)
                    else:
                        init_val[n_opt + 1] = 0
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) + "% of optimizations processed.")

            ### Stackelberg game
            if options["stackelberg"] == "True":

                # compute bids for the Stackelberg game
                mar_dict["bid"][n_opt] = mar_pre.compute_bids(opti_res[n_opt], par_rh, mar_agent_bes, n_opt, options)

                # separate bids in buying and selling and store under "sorted_bids"
                mar_dict["sorted_bids"][n_opt] = mar_pre.sort_participants(mar_dict["bid"][n_opt])

                buy_list_sorted, sell_list_sorted = mar_dict["sorted_bids"][n_opt]

                # run Stackelberg game
                mar_dict["stackelberg_res"][n_opt] = stack.stackelberg_game(buy_list=buy_list_sorted, sell_list=sell_list_sorted,
                                                                            nodes=nodes, params=params, par_rh=par_rh,
                                                                            building_param=building_params, init_val=init_val,
                                                                            n_opt=n_opt, options=options)

            ### Auction
            elif options["stackelberg"] == "False":
                # compute bids
                mar_dict["bid"][n_opt] = mar_pre.compute_bids(opti_res[n_opt], par_rh, mar_agent_bes, n_opt, options)
                # separate bids in buying and selling, sort by price
                mar_dict["sorted_bids"][n_opt] = {}
                mar_dict["sorted_bids"][n_opt] = mar_pre.sort_bids(mar_dict["bid"][n_opt], options, characteristics, n_opt)

                # run the auction
                mar_dict["transactions"][n_opt], mar_dict["sorted_bids"][n_opt] = auction.multi_round(
                   mar_dict["sorted_bids"][n_opt])

                # create categories in trade_res and set to 0
                for cat in ("revenue", "cost", "el_to_distr", "el_from_distr", "el_to_grid", "el_from_grid"):
                    trade_res[n_opt][cat] = {}
                    for nb in range(options["nb_bes"]):
                        trade_res[n_opt][cat][nb] = 0
                trade_res[n_opt]["average_trade_price"] = 0
                trade_res[n_opt]["total_cost_trades"] = 0

                # calculate cost and revenue of transactions
                trade_res[n_opt] = mar_pre.cost_and_rev(mar_dict["transactions"][n_opt], trade_res[n_opt])

                # clear book by buying and selling from and to grid
                trade_res[n_opt], mar_dict["sorted_bids"][n_opt] = mar_pre.clear_book(trade_res[n_opt], mar_dict["sorted_bids"][n_opt][len(mar_dict["sorted_bids"][n_opt])-1], params)

            # change structure of results to be sorted by res instead of building
            # opti_res_new = {}
            # for n_opt in range(par_rh["n_opt"]):
            #     opti_res_new[n_opt] = {}
            #     for i in range(18):
            #         opti_res_new[n_opt][i] = {}
            #         for n in range(options["nb_bes"]):
            #             opti_res_new[n_opt][i][n] = {}
            #             opti_res_new[n_opt][i][n] = opti_res[n_opt][n][i]

        return mar_dict, characteristics
        # return opti_res_new, mar_dict, trade_res, characteristics

    elif options["optimization"] == "P2P_typeWeeks":

        bid_strategy = "zero"

        #range of prices
        p_max = params["eco"]["pr", "el"]
        p_min = params["eco"]["sell_chp"]

        #compute market agents for prosumer
        mar_agent_bes = []
        for n in range(options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh))

        #needed market dicts
        mar_dict = {}

        #create trade_res to store results
        trade_res = {}

        # Start optimizations

        index = list(range(options["number_typeWeeks"]))
        for k in index:

            #create market dicts
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

                #compute bids
                mar_dict[k]["bid"][n_opt] = mar_pre.compute_bids( opti_res[k][n_opt], par_rh, mar_agent_bes, n_opt, options)
                #seperate bids in buying and selling, sort by price
                mar_dict[k]["sorted_bids"][n_opt] = {}
                mar_dict[k]["sorted_bids"][n_opt] = mar_pre.sort_bids(mar_dict[k]["bid"][n_opt])

                #run the auction
                mar_dict[k]["transactions"][n_opt], mar_dict[k]["sorted_bids"][n_opt] = auction.single_round(mar_dict[k]["sorted_bids"][n_opt])

                #create categories in trade_res and set to 0
                for cat in ("revenue", "cost", "el_to_distr", "el_from_distr", "el_to_grid", "el_from_grid"):
                    trade_res[k][n_opt][cat] = {}
                    for nb in range(options["nb_bes"]):
                        trade_res[k][n_opt][cat][nb] = 0
                trade_res[k][n_opt]["average_trade_price"] = 0
                trade_res[k][n_opt]["total_cost_trades"] = 0


                #calculate cost and revenue of transactions
                trade_res[k][n_opt] = mar_pre.cost_and_rev(mar_dict[k]["transactions"][n_opt], trade_res[k][n_opt])

                #clear book by buying and selling from and to grid
                trade_res[k][n_opt], mar_dict[k]["sorted_bids"][n_opt] = mar_pre.clear_book(trade_res[k][n_opt], mar_dict[k]["sorted_bids"][n_opt], params)



        #change struture of results to be sorted by res instead of building
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