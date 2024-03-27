import numpy as np
import copy
import random
random.seed(42)

def compute_block_bids(bes, opti_res, par_rh, mar_agent_prosumer, n_opt, options, nodes,
                       strategies, block_length):
    """
    Compute block bids of 3 time steps for all buildings. The bids are created by each building's mar_agent.

    Returns:
        block_bid (nested dict): [time step t: [bid containing price, quantity, Boolean whether buying/selling, building number]]
        bes (object): inflexible demand is stored in bes for each building
    """

    weights = {}
    block_bid = {}

    # ITERATE THROUGH ALL BUILDINGS
    for n in range(len(opti_res)):
        block_bid["bes_" + str(n)] = {}

        # GET PARAMETERS AT EACH TIMESTEP T FOR BIDDING
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            # t = par_rh["time_steps"][n_opt][0]
            p_imp = opti_res[n][4][t]
            chp_sell = opti_res[n][8]["chp"][t]
            pv_sell = opti_res[n][8]["pv"][t]
            bid_strategy = options["bid_strategy"]
            dem_heat = nodes[n]["heat"][t]
            dem_dhw = nodes[n]["dhw"][t]
            dem_elec = nodes[n]["elec"][t]
            pv_peak = np.max(nodes[n]["pv_power"])
            p_ch_bat = opti_res[n][5]["bat"][t]
            p_dch_bat = opti_res[n][6]["bat"][t]
            soc_bat = opti_res[n][3]["bat"][t]
            soc_tes = opti_res[n][3]["tes"][t]
            heat_hp = opti_res[n][2]["hp35"][t] + opti_res[n][2]["hp55"][t]
            heat_chp = opti_res[n][2]["chp"][t]
            power_hp = max(opti_res[n][1]["hp35"][t], opti_res[n][1]["hp55"][t])
            heat_devs = sum([opti_res[n][2]["hp35"][t], opti_res[n][2]["hp55"][t], opti_res[n][2]["chp"][t],
                             opti_res[n][2]["boiler"][t], dem_dhw * 0.5])

            # ------------- COMPUTE BLOCK BIDS -------------

            # when electricity needs to be bought, compute_hp_bids() of the mar_agent is called
            # if power_hp >= 0.0 and p_imp > 0.0 and pv_sell == 0:
            if power_hp >= 0.0 and p_imp > 0.0 and pv_sell < 1e-3:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = \
                    mar_agent_prosumer[n].compute_hp_bids(p_imp=p_imp, n=n, bid_strategy=bid_strategy, dem_heat=dem_heat,
                                                          dem_dhw=dem_dhw, soc=soc_tes, power_hp=power_hp, options=options,
                                                          strategies=strategies, weights=weights, heat_hp=heat_hp,
                                                          heat_devs=heat_devs, node=nodes[n])

            # when electricity from pv needs to be sold, compute_pv_bids() of the mar_agent is called
            elif pv_sell > 0:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_pv_bids(
                    dem_elec=dem_elec, soc_bat=soc_bat, p_ch_bat=p_ch_bat, p_dch_bat=p_dch_bat,
                    pv_sell=pv_sell, pv_peak=pv_peak, n=n, bid_strategy=options["bid_strategy"],
                    strategies=strategies, weights=weights, options=options)


            # when electricity from chp needs to be sold, compute_chp_bids() of the mar_agent is called
            elif chp_sell > 0:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = \
                    mar_agent_prosumer[n].compute_chp_bids(chp_sell=chp_sell, n=n, bid_strategy=bid_strategy,
                                                           dem_heat=dem_heat, dem_dhw=dem_dhw, soc=soc_tes,
                                                           options=options,strategies=strategies, weights=weights,
                                                           heat_chp=heat_chp, heat_devs=heat_devs, node=nodes[n])

            # when no electricity needs to be bought or sold, compute_empty_bids() of the mar_agent is called
            else:
                block_bid["bes_" + str(n)][t], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_empty_bids(n)

    return block_bid, bes


# CALCULATE CRITERIA FOR SORTING BLOCK BIDS (mean price, mean quantity, or characteristic)
def mean_all(block_bid):
    """Calculates the mean value of the matching criteria of a block bid.
     Returns: mean_price, mean_quantity, mean_energy_forced, mean_energy_delayed, bes_id"""

    # calculate mean price, mean quantity (stored in block_bid)
    total_price = 0
    count = 0
    sum_energy = 0
    bes_id_list = []
    # block_length = len(block_bid)

    for t in block_bid:  # iterate through time steps
        total_price += block_bid[t][0]
        count += 1
        sum_energy += block_bid[t][1]
        bes_id_list.append(block_bid[t][3])

    mean_price = total_price / count if count > 0 else 0
    mean_quantity = sum_energy / count if count > 0 else 0
    bes_id = bes_id_list[0]

    """# calculate mean energy forced and delayed (stored in new_characs)
    total_energy_forced = 0
    total_energy_delayed = 0
    count_energy_forced = 0
    count_energy_delayed = 0

    # calculate flexible energy for every bes_id in new_characs for all time_steps in block_bid:
    for t in list(new_characs[bes_id]["energy_forced"])[:block_length]:
        total_energy_forced += new_characs[bes_id]["energy_forced"][t]
        count_energy_forced += 1
    for t in list(new_characs[bes_id]["energy_delayed"])[:block_length]:
        total_energy_delayed += new_characs[bes_id]["energy_delayed"][t]
        count_energy_delayed += 1

    mean_energy_forced = total_energy_forced / count_energy_forced if count > 0 else 0
    mean_energy_delayed = total_energy_delayed / count_energy_delayed if count > 0 else 0"""

    return bes_id, mean_price, sum_energy, total_price, mean_quantity


def sort_block_bids(block_bid, options, new_characs, n_opt, par_rh):
    """All block bids are sorted by the criteria specified in options["crit_prio"].
    Returns:
        block_bids (nested dict): {buy/sell: position i: time steps t0-t2: [p, q, n]} """

    buy_list = []  # list for all buying bids
    sell_list = []  # list for all selling bids
    sorted_buy_list = []  # list for all sorted buying bids
    sorted_sell_list = []  # list for all sorted selling bids

    # ------------------- SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS -------------------
    for n in range(len(block_bid)):  # iterate through buildings
        # Add str whether buying or not to bool_list
        bool_list = []
        for t in block_bid["bes_" + str(n)]:
            if isinstance(block_bid["bes_" + str(n)][t], list):
                bool_list.append(block_bid["bes_" + str(n)][t][2])

        # Check if str is True or None and not False and append block bid to buy_list
        if ("True" in bool_list or "None" in bool_list) and "False" not in bool_list:
            buy_list.append(block_bid["bes_" + str(n)])
            i = len(buy_list) - 1
            # append block_bid_info to buy_list
            bes_id, mean_price, sum_energy, total_price, mean_quantity \
                = mean_all(block_bid=block_bid["bes_" + str(n)])
            # add flexible energy forced & delayed to buy_list (only first timestep, since it is calculated for 36h)
            first_t = par_rh["time_steps"][n_opt][0]
            flex_energy_forced = new_characs[bes_id]["energy_forced"][first_t]
            flex_energy_delayed = new_characs[bes_id]["energy_delayed"][first_t]
            buy_block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                              "total_price": total_price, "mean_quantity": mean_quantity,
                              "flex_energy_forced": flex_energy_forced, "flex_energy_delayed": flex_energy_delayed}
            buy_list[i].update(buy_block_bid_info)

        # Check if at least one value is False & append block bid to sell_list
        elif "False" in bool_list:
            # Make a deepcopy to avoid modifying the original sublist in block_bid
            sublist_copy = copy.deepcopy(block_bid["bes_" + str(n)])
            sell_list.append(sublist_copy)
            i = len(sell_list) - 1
            ignored_demand = {}
            # Set quantity and price to 0 at time steps where the string is True (seller wants to buy)
            # sell list only contains the quantities & prices to be sold
            for t in sublist_copy:
                if isinstance(sublist_copy[t], list) and sublist_copy[t][2] == "True":
                    sell_list[i][t][0] = 0  # set price to 0
                    sell_list[i][t][1] = 0  # set quantity to 0
                    sell_list[i][t][2] = str("False")  # set str to False
                # ignored demand at each time step t is difference between quantity in sellers block bid and in
                # sell list and will be traded with grid at end of negotiation rounds
                ignored_demand[t] = block_bid["bes_"+str(n)][t][1] - sell_list[i][t][1]

            # append block_bid_info to sell_list
            bes_id, mean_price, sum_energy, total_price, mean_quantity \
                = mean_all(block_bid=sell_list[i])
            # add flexible energy forced & delayed to sell_list (only first timestep, since it is calculated for 36h)
            first_t = par_rh["time_steps"][n_opt][0]
            flex_energy_forced = new_characs[bes_id]["energy_forced"][first_t]
            flex_energy_delayed = new_characs[bes_id]["energy_delayed"][first_t]
            sell_block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                   "total_price": total_price, "mean_quantity": mean_quantity,
                                   "flex_energy_forced": flex_energy_forced, "flex_energy_delayed": flex_energy_delayed,
                                   "ignored_demand": ignored_demand}
            sell_list[i].update(sell_block_bid_info)

    # ------------------- SORT BLOCK BIDS BY CRITERIA DEFINED IN OPTIONS -------------------

    # sort buy_list and sell_list by mean price of block_bids if mean price has been specified as criteria in options
    if options["crit_prio"] == "mean_price":
        # highest paying and lowest asking first if descending has been set True in options
        if options["descending"]:
            sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_price"], reverse=True)
            sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_price"], reverse=True)
        # otherwise lowest mean price first
        else:
            sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_price"])
            sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_price"])

    # sort buy_list and sell_list by mean quantity if mean quantity has been specified as criteria in options
    elif options["crit_prio"] == "mean_quantity":
        # highest quantity first if descending has been set True in options
        if options["descending"]:
            sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_quantity"], reverse=True)
            sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_quantity"], reverse=True)
        # otherwise lowest quantity first
        else:
            sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_quantity"])
            sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_quantity"])

    # sort buy_list and sell_list by flexible mean energy if mean energy has been specified as criteria in options
    elif options["crit_prio"] == "flex_energy":
        # highest energy flexibility of seller (lowest flexibility of buyer) first if descending has been set True in options
        if options["descending"]:
            # most flexible buyer is the one, that can buy more than given buy quantity (soc of tes is low -> energy_forced high)
            sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_forced"]) # _forced
            # most flexible seller is the one, that can sell more than given in sell quantity (soc of tes is high -> energy_delayed high)
            sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"], reverse=True) # _delayed
        # otherwise lowest energy flexibility first
        else:
            sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_forced"])
            sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"])

    elif options["crit_prio"] == "random":
        sorted_buy_list = buy_list
        if not sorted_buy_list:
            random.shuffle(sorted_buy_list)

        sorted_sell_list = sell_list
        if not sorted_sell_list:
            random.shuffle(sorted_sell_list)

    # STORE SORTED BUY AND SELL LISTS IN ONE DICTIONARY TO RETURN
    sorted_block_bids = {"buy_blocks": sorted_buy_list,
                         "sell_blocks": sorted_sell_list}

    return sorted_block_bids, sell_list, buy_list