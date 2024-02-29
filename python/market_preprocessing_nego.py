import numpy as np

def compute_block_bids(bes, opti_res, par_rh, mar_agent_prosumer, n_opt, options, nodes, init_val, propensities,
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
        for t in par_rh["time_steps"][n_opt][0:block_length]:  # for t, t+1, t+2
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
            #if n_opt == 0:
            soc = opti_res[n][3]["tes"][t]
            #else:
                #soc = init_val[n_opt]["building_" + str(n)]["soc"]["tes"]

            x = []
            for i in range(7):
                x.append(sum(nodes[n]["heat"][i * 24:i * 24 + 24]) + 0.5 * sum(nodes[n]["dhw"][i * 24:i * 24 + 24]))
            soc_set_max = max(x)

            # COMPUTE BLOCK BIDS AND INFLEXIBLE DEMANDS

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


# CALCULATE CRITERIA FOR SORTING BLOCK BIDS (mean price, mean quantity, or characteristic)
def mean_all(block_bid, new_characs):
    """Calculates the mean value of the matching criteria of a block bid.
     Returns: mean_price, mean_quantity, mean_energy_forced, mean_energy_delayed, bes_id"""

    # calculate mean price, mean quantity (stored in block_bid)
    total_price = 0
    count = 0
    sum_energy = 0
    bes_id_list = []
    block_length = len(block_bid)

    for t in block_bid:  # iterate through time steps
        total_price += block_bid[t][0] * block_bid[t][1]
        count += 1
        sum_energy += block_bid[t][1]
        bes_id_list.append(block_bid[t][3])

    mean_price = total_price / sum_energy if sum_energy > 0 else 0
    mean_quantity = sum_energy / count if count > 0 else 0
    bes_id = bes_id_list[0]

    # calculate mean energy forced and delayed (stored in new_characs)
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
    mean_energy_delayed = total_energy_delayed / count_energy_delayed if count > 0 else 0

    return bes_id, mean_price, sum_energy, total_price, mean_quantity, mean_energy_forced, mean_energy_delayed


def sort_block_bids(block_bid, options, new_characs, n_opt, par_rh, opti_res):
    """All block bids are sorted by the criteria specified in options["crit_prio"].

    Returns:
        block_bids (nested dict): {buy/sell: position i: time steps t0-t2: [p, q, n]} """

    buy_list = []  # list for all buying bids
    sell_list = []  # list for all selling bids
    sorted_buy_list = []  # list for all sorted buying bids
    sorted_sell_list = []  # list for all sorted selling bids

    # SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS
    for n in range(len(block_bid)):  # iterate through buildings
        block_bid_info = {}
        bes_id, mean_price, sum_energy, total_price, mean_quantity, mean_energy_forced, mean_energy_delayed = mean_all(
            block_bid["bes_" + str(n)], new_characs)
        # bes_id=[f[3] for f in block_bid["bes_" + str(n)].values()]
        block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                          "total_price": total_price,
                          "mean_quantity": mean_quantity, "mean_energy_forced": mean_energy_forced,
                          "mean_energy_delayed": mean_energy_delayed}  # "bes_id": bes_id[0]
        block_bid["bes_" + str(n)].update(block_bid_info)

        # Add str whether buying or not to bool_list
        # Add the value at position 2 (str for buying (either True, False or None)) in the lists inside block_bid to bool_list
        bool_list = []
        for t in block_bid["bes_" + str(n)]:
            if isinstance(block_bid["bes_" + str(n)][t], list):
                bool_list.append(block_bid["bes_" + str(n)][t][2])

        # if entry in bool_list is "True", add block_bid to buy_list and set mean_energy to mean_energy_delayed
        if "True" in bool_list:
            buy_list.append(block_bid["bes_" + str(n)])
        # if any entry in bool_list is "False", add block_bid to sell_list and set mean_energy to mean_energy_forced
        elif "False" in bool_list:
            sell_list.append(block_bid["bes_" + str(n)])
        # if all entries in bool_list are "None", continue
        else:
            continue

    # SORT BLOCK BIDS BY CRITERIA DEFINED IN OPTIONS

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
    elif options["crit_prio"] == "mean_energy":
        # highest energy flexibility of seller (lowest flexibility of buyer) first if descending has been set True in options
        if options["descending"]:
            # most flexible buyer is the one, that can buy more than given buy quantity (soc of tes is low -> energy_forced high)
            sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_forced"])
            # most flexible seller is the one, that can sell more than given in sell quantity (soc of tes is high -> energy_delayed high)
            sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"], reverse=True)
        # otherwise lowest energy flexibility first
        else:
            sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_forced"])
            sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"])

    # STORE SORTED BUY AND SELL LISTS IN ONE DICTIONARY TO RETURN
    block_bids = {"buy_blocks": sorted_buy_list,
                  "sell_blocks": sorted_sell_list}

    return block_bids