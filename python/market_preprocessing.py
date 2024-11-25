import numpy as np


def dict_for_market_data(par_rh):
    """Creates a dictionary to store information about market activities."""

    mar_dict = {
        "transactions": {},
        "bid": {},
        "block_bids": {},
        "sell_list": {},
        "buy_list": {},
        "sorted_bids": {},
        "sorted_bids_nego": {},
        "matched_bids_info": {},
        "matched_bids_info_nego": {},
        "negotiation_results": {},
        "participating_bes": {},
        "transactions_with_grid": {},
        "total_market_info": {},
        "propensities": {n_opt: {} for n_opt in range(par_rh["n_opt"])}
        }

    return mar_dict


def dict_for_bes(pars_rh, numb_bes):
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


def css(pars_rh, numb_css):
    """Creates a dictionary to store information about the central supply systems."""

    central_systems = {}
    for n in range(numb_css):
        central_systems[n] = {
            "css_capacity": np.zeros(pars_rh["n_opt"]),
            "css_el_demand": np.zeros(pars_rh["n_opt"]),
            "css_el_generation": np.zeros(pars_rh["n_opt"]),
            "css_heat_generation": np.zeros(pars_rh["n_opt"]),
            "css_op_cost": np.zeros(pars_rh["n_opt"]),
            "css_revenue": np.zeros(pars_rh["n_opt"])
        }
    return central_systems

def compute_bids(bes, opti_res, par_rh, mar_agent_bes, n_opt, options, nodes, init_val, propensities, strategies):
    # Todo: Integrate bids for central supply systems by css agents

    """
     Compute bids for all buildings. The bids are created by each building's mar_agent.

     Returns:
         bid (dict):  bid containing price, quantity, Boolean whether buying/selling, building number
         bes (object): inflexible demand is stored in bes for each building
     """

    # calculate weights if learning is chosen
    if options["bid_strategy"] == "learning":
        weights = compute_weights(options["nb_bes"], propensities, par_rh, n_opt)
    else:
        weights = {}

    bid = {}
    # iterate through all buildings
    for n in range(len(opti_res)):
        bid["bes_" + str(n)] = {}
        t = par_rh["time_steps"][n_opt][0]
        buying_quantity = opti_res[n][4][t] # p_imp
        selling_quantity = opti_res[n][8]["chp"][t] + opti_res[n][8]["pv"][t] # chp_sell + pv_sell

        # compute bids with ZERO-INTELLIGENCE
        if options["bid_strategy"] == "zero":
            bid["bes_" + str(n)] = mar_agent_bes[n].zero_bids(buying_quantity, selling_quantity, n)
        # compute bids with erev-roth learning strategy
        elif options["bid_strategy"] == "learning":
            bid["bes_" + str(n)] = mar_agent_bes[n].erev_roth_learning_bids(buying_quantity, selling_quantity, n, strategies, weights)

    return bid

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

    # sort buy_list and sell_list by quantity if quantity has been specified as criteria in options
    elif options["crit_prio"] == "quantity":
        # highest quantity first if descending has been set True in options
        if options["descending"]:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["quantity"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["quantity"], reverse=True)
        # otherwise lowest quantity first
        else:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["quantity"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["quantity"])

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
    # Todo: Check if the integration of CSS is needed here
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
    # Todo: Integrate central supply systems
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


def total_sup_and_dem(opti_res, par_rh, n_opt, nb_bes):

    # calculates total generated and demanded electricity

    dem = {}
    sup = {}
    dem_total = {}
    sup_total = {}
    for t in par_rh["time_steps"][n_opt]:
        dem[t] = []
        sup[t] = []
        for n in range(nb_bes):
            dem[t].append(opti_res[n][4][t])
            sup[t].append(opti_res[n][8]["pv"][t] + opti_res[n][8]["chp"][t])
        dem_total[t] = sum(dem[t])
        sup_total[t] = sum(sup[t])

    return dem_total, sup_total