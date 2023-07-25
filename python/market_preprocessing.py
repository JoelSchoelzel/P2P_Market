import numpy as np


def dict_for_market_data(pars_rh):
    """Creates a dictionary to store information about market activities."""

    mar_dict = {
        "transactions": {},
        "bid": {},
        "sorted_bids": {}
        }

    return mar_dict


def bes(pars_rh, numb_bes):
    """Creates a dictionary to store information about the inflexible demands and traded amounts of the building."""

    new_bes = {}
    for n in range(numb_bes):
        new_bes[n] = {"adj_op": np.zeros(pars_rh["n_opt"]),
                      "tra_dem": np.zeros(pars_rh["n_opt"]),
                      "tra_dem_unflex": np.zeros(pars_rh["n_opt"]),
                      "tra_gen": np.zeros(pars_rh["n_opt"]),
                      "plus_gen": np.zeros(pars_rh["n_opt"]),
                      "grid_dem": np.zeros(pars_rh["n_opt"]),
                      "grid_gen": np.zeros(pars_rh["n_opt"]),
                      "hp_dem":  np.zeros(pars_rh["n_opt"]),
                      "unflex":  np.zeros(pars_rh["n_opt"])
                      }
    return new_bes


def compute_bids(bes, opti_res, pars_rh, mar_agent_prosumer, n_opt, options, nodes, init_val):
    """
    Compute bids for all buildings. The bids are created by each building's mar_agent.

    Returns:
        bid (dict): bid containing price, quantity, Boolean whether buying/selling, building number.
        bes (object): inflexible demand is stored in bes for each building
    """

    bid = {}

    # iterate through all buildings
    for n in range(len(opti_res)):
        # get parameters for bidding
        t = pars_rh["time_steps"][n_opt][0]
        p_imp = opti_res[n][4][t]
        chp_sell = opti_res[n][8]["chp"][t]
        bid_strategy = options["bid_strategy"]

        dem_heat = nodes[n]["heat"][n_opt]
        dem_dhw = nodes[n]["dhw"][n_opt]
        if n_opt == 0:
            soc = opti_res[n][3]["tes"][t]
        else:
            soc = init_val[n_opt]["building_" + str(n)]["soc"]["tes"]

        power_hp = max(opti_res[n][1]["hp35"][t], opti_res[n][1]["hp55"][t])

        # compute bids and inflexible demands

        # when electricity needs to be bought, compute_hp_bids() of the mar_agent is called
        if p_imp > 0.0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = \
                mar_agent_prosumer[n].compute_hp_bids(p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options)

        # when electricity needs to be sold, compute_chp_bids() of the mar_agent is called
        elif chp_sell > 0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = \
                mar_agent_prosumer[n].compute_chp_bids(chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options)

        # when no electricity needs to be bought or sold, compute_empty_bids() of the mar_agent is called
        else:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_empty_bids(n)

    return bid, bes


def sort_bids(bid, options, characs, n_opt):
    """
    All bids are sorted by the criteria specified in options["crit_prio"].

    Returns:
        bids (dict): Bids separated by buying/selling and sorted by criteria.
    """

    buy_list = {}  # dictionary for all buying bids
    sell_list = {}  # dictionary for all selling bids

    # sort by buy or sell
    for n in range(len(bid)):

        # don't consider bids with zero quantity
        if float(bid["bes_" + str(n)][1]) != 0.0:

            # add buying bids to buy_list
            if bid["bes_" + str(n)][2] == "True":
                i = len(buy_list)
                buy_list[i] = {
                    "price": bid["bes_" + str(n)][0],
                    "quantity": bid["bes_" + str(n)][1],
                    "building": bid["bes_" + str(n)][3]
                }

            # add selling bids to sell_list
            if bid["bes_" + str(n)][2] == "False":
                i = len(sell_list)
                sell_list[i] = {
                    "price": bid["bes_" + str(n)][0],
                    "quantity": bid["bes_" + str(n)][1],
                    "building": bid["bes_" + str(n)][3]
                }

    # sort buy_list and sell_list by price if price has been specified as criteria in options
    if options["crit_prio"] == "price":
        # highest paying and lowest asking first if descending has been set True in options
        if options["descending"]:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"])
        # otherwise lowest paying and highest asking first
        else:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"], reverse=True)

    # else if a crit from characteristics (KPIs describing flexibility) is specified:
    else:
        # add the delayed flexibility of the chosen characteristic as crit for all buying bids
        for i in range(len(buy_list)):
            buy_list[i]["crit"] = characs[buy_list[i]["building"]][options["crit_prio"]+"_delayed"][n_opt]
        # add the forced flexibility of the chosen characteristic as crit for all selling bids
        for i in range(len(sell_list)):
            sell_list[i]["crit"] = characs[sell_list[i]["building"]][options["crit_prio"]+"_forced"][n_opt]

        # sort the bids by crit, the highest first if "descending" is True in options, otherwise lowest first
        if options["descending"]:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"], reverse=True)
        else:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"])

    # store buy_list and sell_list in one dictionary to return
    # index 1 at end of list to fix changes made to structure while sorting
    bids = {
        "buy": {i: sorted_buy_list[i][1] for i in range(len(sorted_buy_list))},
        "sell": {i: sorted_sell_list[i][1] for i in range(len(sorted_sell_list))}
    }

    return bids


def cost_and_rev_trans(trans, res):
    """
    Calculates the cost and revenue of each trade made within the district as well as the average trade price and the
    total cost.

    Returns:
        Revenue, cost, average trade price and total cost stored in res.
    """

    # calculate revenue and cost by adding quantity*price of each transaction
    for i in range(len(trans)):
        res["revenue"][trans[i]["seller"]] += (trans[i]["quantity"] * trans[i]["price"])
        res["cost"][trans[i]["buyer"]] += (trans[i]["quantity"] * trans[i]["price"])

    # calculate average trade price and total cost of all trades made in this n_opt
    if len(trans) > 0:
        res["average_trade_price"] = sum(res["cost"].values()) / sum(res["el_from_distr"].values())
        res["total_cost_trades"] = sum(res["cost"].values())

    return res


def clear_book(res, bids, params):
    """
    Not used at the moment! Has been replaced by grid_demands() and cost_and_rev_grid().

    Clears all remaining bids by buying from and selling to the grid.
    """

    for i in range(len(bids["buy"])):
        res["cost"][bids["buy"][i]["building"]] += (bids["buy"][i]["quantity"] * params["eco"]["pr", "el"])
        res["el_from_grid"][bids["buy"][i]["building"]] += bids["buy"][i]["quantity"]
        bids["buy"][i]["quantity"] = 0

    for i in range(len(bids["sell"])):
        res["revenue"][bids["sell"][i]["building"]] += (bids["sell"][i]["quantity"] * params["eco"]["sell_chp"])
        res["el_to_grid"][bids["sell"][i]["building"]] += bids["sell"][i]["quantity"]
        bids["sell"][i]["quantity"] = 0

    return res, bids


def traded_volume(transaction, res):
    """Calculates the amount of electricity traded within the district."""

    # add volumes traded within the district
    for i in range(len(transaction)):
        res["el_from_distr"][transaction[i]["buyer"]] += transaction[i]["quantity"]
        res["el_to_distr"][transaction[i]["seller"]] += transaction[i]["quantity"]

    return res


def grid_demands(bes, trade_res, options, bids, n_opt):
    """
    Calculates needs and surpluses that need to be fulfilled by grid. These are inflexible demands that haven't been
    fulfilled by trading.
    """

    # iterate through buildings
    for n in range(options["nb_bes"]):
        # only buying bids
        if bids["bes_" + str(n)][2] == "True":
            # check whether unflexible demand has been fulfilled, otherwise add remaining unflexible demand to grid_dem
            if bes[n]["unflex"][n_opt] > trade_res["el_from_distr"][n]:
                bes[n]["grid_dem"][n_opt] = bes[n]["unflex"][n_opt] - trade_res["el_from_distr"][n]

        # only selling bids
        if bids["bes_" + str(n)][2] == "False":
            # check whether unflexible surplus has been sold, otherwise add remaining unflexible surplus to grid_dem
            if bes[n]["unflex"][n_opt] > trade_res["el_to_distr"][n]:
                bes[n]["grid_gen"][n_opt] = bes[n]["unflex"][n_opt] - trade_res["el_to_distr"][n]
    return bes


def cost_and_rev_grid(bes, trade_res, options, n_opt, eco):
    """Calculates amount and cost or revenue of buying and selling to the grid."""

    # iterate through buildings
    for n in range(options["nb_bes"]):
        # add volume and revenue of elec sold to grid
        if bes[n]["grid_gen"][n_opt] > 0:
            trade_res["el_to_grid"][n] = bes[n]["grid_gen"][n_opt]
            trade_res["revenue"][n] += bes[n]["grid_gen"][n_opt] * eco["sell_chp"]

        # add volume and cost of elec bought from grid
        elif bes[n]["grid_dem"][n_opt] > 0:
            trade_res["el_from_grid"][n] = bes[n]["grid_dem"][n_opt]
            trade_res["cost"][n] += bes[n]["grid_dem"][n_opt] * eco["pr", "el"]

    return trade_res
