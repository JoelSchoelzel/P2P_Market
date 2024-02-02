import numpy as np


def dict_for_market_data(par_rh):
    """Creates a dictionary to store information about market activities."""

    mar_dict = {
        "transactions": {},
        "bid": {},
        "block_bid": {},
        "sorted_bids": {},
        "propensities": {n_opt: {} for n_opt in range(par_rh["n_opt"])}
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


def compute_bids(bes, opti_res, par_rh, mar_agent_prosumer, n_opt, options, nodes, init_val, propensities, strategies):
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
        # get parameters for bidding
        # t = par_rh["time_steps"][n_opt][0]
        p_imp = opti_res[n][4][t]
        chp_sell = opti_res[n][8]["chp"][t]
        pv_sell = opti_res[n][8]["pv"][t]  # Index passt!
        bid_strategy = options["bid_strategy"]
        dem_heat = nodes[n]["heat"][t]
        x = []
        for i in range(7):
            x.append(sum(nodes[n]["heat"][i * 24:i * 24 + 24]) + 0.5 * sum(nodes[n]["dhw"][i * 24:i * 24 + 24]))
        soc_set_max = max(x)
        dem_dhw = nodes[n]["dhw"][t]
        heat_hp = opti_res[n][2]["hp35"][t]+opti_res[n][2]["hp55"][t]
        heat_chp = opti_res[n][2]["chp"][t]
        dem_elec = nodes[n]["elec"][t]
        power_pv = nodes[n]["pv_power"][t]
        pv_peak = np.max(nodes[n]["pv_power"][t])
        p_ch_bat = opti_res[n][5]["bat"][t]
        p_dch_bat = opti_res[n][6]["bat"][t]
        soc_bat = opti_res[n][3]["bat"][t]

        heat_devs = sum([opti_res[n][2]["hp35"][t], opti_res[n][2]["hp55"][t], opti_res[n][2]["chp"][t],
                         opti_res[n][2]["boiler"][t], dem_dhw*0.5])

        if n_opt == 0:
            soc = opti_res[n][3]["tes"][t]
        else:
            soc = init_val[n_opt]["building_" + str(n)]["soc"]["tes"]

        power_hp = max(opti_res[n][1]["hp35"][t], opti_res[n][1]["hp55"][t])

        # COMPUTE BIDS AND INFLEXIBLE DEMANDS
        # when electricity needs to be bought, compute_hp_bids() of the mar_agent is called
        if power_hp >= 0.0 and p_imp > 0.0 and pv_sell == 0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = \
                mar_agent_prosumer[n].compute_hp_bids(p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp,
                                                      options, strategies, weights, heat_hp, heat_devs, soc_set_max)

        # when electricity from pv needs to be sold, compute_pv_bids() of the mar_agent is called
        elif pv_sell > 0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_pv_bids(
                dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat,
                pv_sell, pv_peak, t, n, options["bid_strategy"],
                strategies, weights, options)
            # bes[n]["hp_dem"][n_opt] = 0

        # when electricity from chp needs to be sold, compute_chp_bids() of the mar_agent is called
        elif chp_sell > 0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = \
                mar_agent_prosumer[n].compute_chp_bids(chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options,
                                                       strategies, weights, heat_chp, heat_devs, soc_set_max)

        # when no electricity needs to be bought or sold, compute_empty_bids() of the mar_agent is called
        else:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_empty_bids(n)

    return bid, bes

def compute_weights(nb_bes, propensities, par_rh, n_opt): # computes
    # calculates the weights of the bid prices depending on propensities
    weights = {}
    for n in range(nb_bes):

        weights["bes_" + str(n) + "_buy"] = []
        for s in range(len(propensities["bes_" + str(n) + "_buy"])):
            if propensities["bes_" + str(n) + "_buy"][s] > 0:
                weights["bes_" + str(n) + "_buy"].append(
                    propensities["bes_" + str(n) + "_buy"][s] / sum(propensities["bes_" + str(n) + "_buy"]))
            else:
                weights["bes_" + str(n) + "_buy"].append(0)

        weights["bes_" + str(n) + "_sell"] = []
        for s in range(len(propensities["bes_" + str(n) + "_sell"])):
            if propensities["bes_" + str(n) + "_sell"][s] > 0:
                weights["bes_" + str(n) + "_sell"].append(
                    propensities["bes_" + str(n) + "_sell"][s] / sum(propensities["bes_" + str(n) + "_sell"]))
            else:
                weights["bes_" + str(n) + "_sell"].append(0)

    return weights


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


def initial_prop(par_rh, options, pars_li): # creates initial propensities for the first market round
    # list of possible bid prices
    strategies = [round(num, 2) for num in np.arange(options["p_min"], (options["p_max"] + pars_li["step"]),
                                                     pars_li["step"])]
    # inital props:
    prop = {}
    for n in range(options["nb_bes"]):
        prop["bes_" + str(n) + "_buy"] = []
        prop["bes_" + str(n) + "_sell"] = []
        for l in range(len(strategies)):
            prop["bes_" + str(n) + "_buy"].append(pars_li["init_prop"]["buy"])
            prop["bes_" + str(n) + "_sell"].append(pars_li["init_prop"]["sell"])

        # this can be used when props are loaded at the beginning to use last values
        #if pars_li["init_prop"]["buy"] == 0.01:
        #    prop["bes_" + str(n) + "_buy"] = []
        #    prop["bes_" + str(n) + "_sell"] = []
        #    for l in range(len(strategies)):
        #        prop["bes_" + str(n) + "_buy"].append(pars_li["init_prop"]["buy"])
        #        prop["bes_" + str(n) + "_sell"].append(pars_li["init_prop"]["sell"])
        #else:
        #    prop["bes_" + str(n) + "_buy"] = pars_li["init_prop"][744][744]["bes_" + str(n) + "_buy"]
        #    prop["bes_" + str(n) + "_sell"] = pars_li["init_prop"][744][744]["bes_" + str(n) + "_sell"]

    return prop, strategies


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


def update_prop(mar_dict, par_rh, n_opt, bes, options, pars_li, trade_res, strategies): #
    # update the props depending on trading results for the next step

    #clearing_price = trade_res["average_trade_price"]
    # get last bid price of each building
    price = {n: 0 for n in range(options["nb_bes"])}
    sorted_bids = mar_dict["sorted_bids"][n_opt]
    for trading_round in range(len(sorted_bids)):
        for bid in range(len(sorted_bids[trading_round]["buy"])):
            building = sorted_bids[trading_round]["buy"][bid]["building"]
            price[building] = sorted_bids[trading_round]["buy"][bid]["price"]
        for bid in range(len(sorted_bids[trading_round]["sell"])):
            building = sorted_bids[trading_round]["sell"][bid]["building"]
            price[building] = sorted_bids[trading_round]["sell"][bid]["price"]
    for n in range(len(price)):
        price[n] = np.round(price[n], 2)

    #bid = mar_dict["bid"][n_opt]
    bid = mar_dict["bid"]
    #dem_total = mar_dict["dem_total"]
    #sup_total = mar_dict["sup_total"]
    dem_total = trade_res["dem_total"]
    sup_total = trade_res["sup_total"]
    old_prop = mar_dict["propensities"][n_opt]
    # new propensities for the next market round
    new_prop = {}

    t = par_rh["time_steps"][n_opt][0]
    # if no supply or demand at all (trading not possible), the propensities do not change
    if dem_total[t] == 0 or sup_total[t] == 0:
        new_prop = old_prop

    else:
        for n in range(options["nb_bes"]):
            new_prop["bes_" + str(n) + "_buy"] = []
            new_prop["bes_" + str(n) + "_sell"] = []
            # if the bid was empty, the propensities do not change
            if bid[n_opt]["bes_" + str(n)][1] == 0:
                new_prop["bes_" + str(n) + "_buy"] = old_prop["bes_" + str(n) + "_buy"]
                new_prop["bes_" + str(n) + "_sell"] = old_prop["bes_" + str(n) + "_sell"]
            # if buying, only update prop buy
            elif bid[n_opt]["bes_" + str(n)][2] == "True":
                new_prop["bes_" + str(n) + "_sell"] = old_prop["bes_" + str(n) + "_sell"]
                for l in range(len(strategies)):
                    if price[n] == strategies[l]:

                        #r = bes[n]["tra_dem"][n_opt,t-par_rh["hour_start"][n_opt]] * (options["p_max"] - clearing_price[n_opt])
                        r = trade_res["el_from_distr"][n] * (options["p_max"] - price[n])

                        if ((1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_buy"][l]) + ((1 - pars_li["exp"]) *r) >=0:
                            new_prop["bes_" + str(n) + "_buy"].append(((1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_buy"][l]) + ((1 - pars_li["exp"]) *r))
                        else:
                            new_prop["bes_" + str(n) + "_buy"].append(0)

                    else:
                        new_prop["bes_" + str(n) + "_buy"].append((1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_buy"][l] + \
                                                        old_prop["bes_" + str(n) + "_buy"][l] * (
                                                                  pars_li["exp"] / (len(strategies) - 1)))
            # if selling, only update prop sell
            else:
                new_prop["bes_" + str(n) + "_buy"] = old_prop["bes_" + str(n) + "_buy"]
                for l in range(len(strategies)):
                    if price[n] == strategies[l]:

                        #r = (bes[n]["tra_gen"][n_opt, t - par_rh["hour_start"][n_opt]]) * (clearing_price[n_opt] - options["p_min"])
                        r = trade_res["el_to_distr"][n] * (price[n] - options["p_min"])

                        if (1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_sell"][l] + (1 - pars_li["exp"]) * r >=0:
                            new_prop["bes_" + str(n) + "_sell"].append((1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_sell"][l] \
                                                            + (1 - pars_li["exp"]) * r)
                        else: new_prop["bes_" + str(n) + "_sell"].append(0)
                    else:
                        new_prop["bes_" + str(n) +"_sell"].append((1 - pars_li["rec"]) * old_prop["bes_" + str(n) + "_sell"][l] \
                                                           + old_prop["bes_" + str(n) +"_sell"][l] \
                                                             * (pars_li["exp"] / (len(strategies) - 1)))

    return new_prop


def compute_block_bids(bes, opti_res, par_rh, mar_agent_prosumer, n_opt, options, nodes, init_val, propensities, strategies):
    """
    Compute block bids of 3 time steps for all buildings. The bids are created by each building's mar_agent.

    Returns:
        bid (nested dict): [time step t: [bid containing price, quantity, Boolean whether buying/selling, building number]]
        bes (object): inflexible demand is stored in bes for each building
    """

    # calculate weights if learning is chosen
    if options["bid_strategy"] == "learning":
        weights = compute_weights(options["nb_bes"], propensities, par_rh, n_opt)
    else:
        weights = {}

    block_bid = {}

    # ITERATE THROUGH ALL BUILDINGS
    for n in range(len(opti_res)):
        block_bid["bes_" + str(n)] = {}

        # GET PARAMETERS AT EACH TIMESTEP T FOR BIDDING
        for t in par_rh["time_steps"][n_opt][0:3]:
            # t = par_rh["time_steps"][n_opt][0]
            p_imp = opti_res[n][4][t]
            chp_sell = opti_res[n][8]["chp"][t]
            pv_sell = opti_res[n][8]["pv"][t]
            bid_strategy = options["bid_strategy"]
            dem_heat = nodes[n]["heat"][t]
            dem_dhw = nodes[n]["dhw"][t]
            dem_elec = nodes[n]["elec"][t]
            pv_peak = np.max(nodes[n]["pv_power"][t])
            p_ch_bat = opti_res[n][5]["bat"][t]
            p_dch_bat = opti_res[n][6]["bat"][t]
            soc_bat = opti_res[n][3]["bat"][t]
            heat_hp = opti_res[n][2]["hp35"][t] + opti_res[n][2]["hp55"][t]
            heat_chp = opti_res[n][2]["chp"][t]
            power_pv = nodes[n]["pv_power"][t]
            power_hp = max(opti_res[n][1]["hp35"][t], opti_res[n][1]["hp55"][t])
            heat_devs = sum([opti_res[n][2]["hp35"][t], opti_res[n][2]["hp55"][t], opti_res[n][2]["chp"][t],
                             opti_res[n][2]["boiler"][t], dem_dhw * 0.5])

            if n_opt == 0:
                soc = opti_res[n][3]["tes"][t]
            else:
                soc = init_val[n_opt]["building_" + str(n)]["soc"]["tes"]

            x = []
            for i in range(7):
                x.append(sum(nodes[n]["heat"][i * 24:i * 24 + 24]) + 0.5 * sum(nodes[n]["dhw"][i * 24:i * 24 + 24]))
            soc_set_max = max(x)


            # COMPUTE BIDS AND INFLEXIBLE DEMANDS

            # when electricity needs to be bought, compute_hp_bids() of the mar_agent is called
            if power_hp >= 0.0 and p_imp > 0.0 and pv_sell == 0:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = \
                    mar_agent_prosumer[n].compute_hp_bids(p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp,
                                                      options, strategies, weights, heat_hp, heat_devs, soc_set_max)


            # when electricity from pv needs to be sold, compute_pv_bids() of the mar_agent is called
            elif pv_sell > 0:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_pv_bids(
                    dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat,
                    pv_sell, pv_peak, t, n, options["bid_strategy"],
                    strategies, weights, options)
                # bes[n]["hp_dem"][n_opt] = 0

            # when electricity from chp needs to be sold, compute_chp_bids() of the mar_agent is called
            elif chp_sell > 0:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = \
                    mar_agent_prosumer[n].compute_chp_bids(chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options,
                                                       strategies, weights, heat_chp, heat_devs, soc_set_max)

            # when no electricity needs to be bought or sold, compute_empty_bids() of the mar_agent is called
            else:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_empty_bids(n)

    return block_bid, bes

def sort_block_bids(block_bid, options, characs, n_opt):
    """
    All bids are sorted by the criteria specified in options["crit_prio"].

    Returns:
        block_bids (dict): Bids separated by buying/selling and sorted by criteria.
    """

    buy_list = {}  # dictionary for all buying bids
    sell_list = {}  # dictionary for all selling bids

    # sort by buy or sell
    for n in range(len(block_bid)):

        # don't consider bids with zero quantity
        if float(block_bid["bes_" + str(n)][1]) != 0.0:

            # add buying bids to buy_list
            if block_bid["bes_" + str(n)][2] == "True":
                i = len(buy_list)
                buy_list[i] = {
                    "price": block_bid["bes_" + str(n)][0],
                    "quantity": block_bid["bes_" + str(n)][1],
                    "building": block_bid["bes_" + str(n)][3]
                }

            # add selling block_bids to sell_list
            if block_bid["bes_" + str(n)][2] == "False":
                i = len(sell_list)
                sell_list[i] = {
                    "price": block_bid["bes_" + str(n)][0][t],
                    "quantity": block_bid["bes_" + str(n)][1][t],
                    "building": block_bid["bes_" + str(n)][3][t]
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
        # add the delayed flexibility of the chosen characteristic as crit for all buying block_bids
        for i in range(len(buy_list)):
            buy_list[i]["crit"] = characs[buy_list[i]["building"]][options["crit_prio"]+"_delayed"][n_opt]
        # add the forced flexibility of the chosen characteristic as crit for all selling block_bids
        for i in range(len(sell_list)):
            sell_list[i]["crit"] = characs[sell_list[i]["building"]][options["crit_prio"]+"_forced"][n_opt]

        # sort the block_bids by crit, the highest first if "descending" is True in options, otherwise lowest first
        if options["descending"]:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"], reverse=True)
        else:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"])

    # store buy_list and sell_list in one dictionary to return
    # index 1 at end of list to fix changes made to structure while sorting
    block_bids = {
        "buy": {i: sorted_buy_list[i][1] for i in range(len(sorted_buy_list))},
        "sell": {i: sorted_sell_list[i][1] for i in range(len(sorted_sell_list))}
    }

    return block_bids