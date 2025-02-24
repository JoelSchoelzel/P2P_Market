import numpy as np
import copy
import random
from python import characteristics
from python.market_agents import mar_agent_css


def compute_block_bids(opti_res, par_rh, mar_agent_bes, n_opt, options, block_length, mar_dict, devs_pre_opti, nodes):
    """
    Compute block bids with length of control horizon for all buildings.
    The bids are created by each building's mar_agent.

    Returns:
        block_bid (nested dict): [time step t: [bid containing price, quantity, Boolean whether buying/selling, building number]]
        bes (object): inflexible demand is stored in bes for each building
    """

    block_bid = {}
    # ITERATE THROUGH ALL BUILDINGS
    for n in range(len(opti_res)):
        block_bid["bes_" + str(n)] = {}

        # GET PARAMETERS AT EACH TIMESTEP T FOR BIDDING
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            buying_quantity = opti_res[n][4]["p_imp"][t]  # p_imp
            selling_quantity = opti_res[n][8]["chp"][t] + opti_res[n][8]["pv"][t]  # chp_sell + pv_sell
            soc_state = opti_res[n][3]["bat"][t]/opti_res[n][12]["bat"] if opti_res[n][12]["bat"] != 0 \
                else opti_res[n][3]["tes"][t]/opti_res[n][12]["tes"]  # soc of bat or tes
            buying_capacity = (nodes[n]["elec"].max() +
                               max(devs_pre_opti[n]["hp55"]["cap"]/nodes[n]["devs"]["COP_sh55"].min(),
                                   devs_pre_opti[n]["hp35"]["cap"]/nodes[n]["devs"]["COP_sh35"].min()))
            selling_capacity = (nodes[n]["pv_power"].max() +
                                nodes[n]["devs"]["chp"]["cap"] * nodes[n]["devs"]["chp"]["eta_el"]
                                / nodes[n]["devs"]["chp"]["eta_th"])

            # compute bids with ZERO-INTELLIGENCE
            if options["bid_strategy"] == "zero":
                block_bid["bes_" + str(n)][t] = mar_agent_bes[n].zero_bids(buying_quantity, selling_quantity)
            # compute bids with erev-roth learning strategy
            elif options["bid_strategy"] == "erev_roth_learning":
                block_bid["bes_" + str(n)][t] = mar_agent_bes[n].erev_roth_learning_bids(buying_quantity, selling_quantity)
            elif options["bid_strategy"] == "q_learning":
                # Initialize Q-table for n_opt == 0, or get Q-table from previous rounds
                if n_opt == 0:
                    mar_agent_bes[n].initialize_q_table_q_learning(t)

                # Get state for q_learning
                mar_agent_bes[n].get_state_q_learning(buying_quantity, buying_capacity, selling_quantity,
                                                      selling_capacity, soc_state, t)

                # Calculate the block bid with q_learning
                block_bid["bes_" + str(n)][t] = mar_agent_bes[n].q_learning_bids(buying_quantity, selling_quantity,
                                                                                 n_opt, block_length, t)
                # Q-table updates happen in 'opti_methods.py' after each negotiation rounds

        if options["bid_strategy"] == "zero" or options["bid_strategy"] == "erev_roth_learning":
            block_bid["bes_" + str(n)] = mar_agent_bes[n].one_price(block_bid["bes_" + str(n)], par_rh, n_opt,
                                                                    block_length)
        elif options["bid_strategy"] == "q_learning":
            block_bid["bes_" + str(n)] = mar_agent_bes[n].one_price_weighted(block_bid["bes_" + str(n)], par_rh, n_opt,
                                                                             block_length, options)

    return block_bid


def compute_block_bids_css(par_rh, n_opt, options, block_length, opti_res_css, block_bid, mar_agent_css):
    # compute bids for central supply system
    block_bid["css"] = {}
    for t in par_rh["time_steps"][n_opt][0:block_length]:
        buying_quantity_css = opti_res_css[n_opt]["res_p_grid_buy"][t] + opti_res_css[n_opt]["res_p_trade_buy"][t]  # + opti_res_css[n_opt]["res_prev_trade_buy"][t]
        selling_quantity_css = opti_res_css[n_opt]["res_p_grid_sell"][t] + opti_res_css[n_opt]["res_p_trade_sell"][t]  # + opti_res_css[n_opt]["res_prev_trade_sell"][t]
        soc_state = opti_res_css[n_opt]["res_soc"]["s_bat"][t] / mar_agent_css.bat_capacity \
            if mar_agent_css.bat_capacity != 0 else 0

        block_bid["css"][t] = {}
        #block_bid["bes_" + str(options["nb_bes"])][t] = {}
        # compute bids with ZERO-INTELLIGENCE
        if options["bid_strategy"] == "zero":
            block_bid["css"][t] = mar_agent_css.zero_bids_css(buying_quantity_css, selling_quantity_css)
            #block_bid["bes_" + str(options["nb_bes"])][t] = mar_agent_css.zero_bids_css(buying_quantity_css, selling_quantity_css)
        if options["bid_strategy"] == "q_learning":
            # Initialize Q-table for n_opt == 0, or get Q-table from previous rounds
            if n_opt == 0:
                mar_agent_css.initialize_q_table_q_learning(t)

            # Get state for q_learning
            mar_agent_css.get_state_q_learning(buying_quantity_css, selling_quantity_css, soc_state, t)

            # Calculate the block bid with q_learning
            block_bid["css"][t] = mar_agent_css.q_learning_bids(buying_quantity_css, selling_quantity_css, n_opt, block_length, t)
            # Q-table updates happen in 'opti_methods.py' after each negotiation rounds

    if options["bid_strategy"] == "zero" or options["bid_strategy"] == "erev_roth_learning":
        block_bid["css"] = mar_agent_css.one_price(block_bid["css"], par_rh, n_opt, block_length)
    elif options["bid_strategy"] == "q_learning":
        block_bid["css"] = mar_agent_css.one_price_weighted(block_bid["css"], par_rh, n_opt, block_length, options)

    return block_bid


def compute_block_bids_during_negotiation(matched_bids, r, match, remaining_demand, block_bid_time_steps, nodes,
                                          block_length, buyer_id, opti_bes_res_buyer, opti_res, buy_list_next_round,
                                          remaining_supply, seller_id, opti_bes_res_seller, sell_list_next_round, options,
                                          opti_res_css: dict = None, mar_agent_css: object = None):
    new_sum_energy = 0
    # add bids only if there is untraded demand
    if sum(remaining_demand.values()) > 1e-3:
        add_buy_bid = True
    else:
        add_buy_bid = False
    # add unsatisfied buyers and sellers to next trading round with remaining demand/supply
    if add_buy_bid == True:
        block_bid = {}
        # copy_of_buy_bid = copy.deepcopy(matched_bids_info_nego[r][match][0])
        for t in block_bid_time_steps:
            # Subtract the traded power from the original demand to get the new remaining demand
            block_bid[t] = [matched_bids[r][match][0][t][0],  # price
                            max(0, remaining_demand[t]),  # remaining demand
                            'True',  # True --> buying
                            matched_bids[r][match][0][t][3]  # bes_id
                            ]
            new_sum_energy += block_bid[t][1]
        block_bid["bes_id"] = matched_bids[r][match][0][t][3]
        block_bid["quantity"] = new_sum_energy / len(block_bid_time_steps)
        block_bid["sum_energy"] = new_sum_energy
        block_bid["total_price"] = matched_bids[r][match][0][t][0]
        block_bid["mean_price"] = matched_bids[r][match][0][t][0]
        block_bid["ignored_demand"] = matched_bids[r][match][0]["ignored_demand"]
        if buyer_id == options["nb_bes"]:  # if central supply system is in block_bid
            flex_energy = characteristics.calc_characs_single_css(block_length, soc_state=opti_bes_res_buyer["res_soc"],
                                                                  opti_res_css=opti_res_css, mar_agent_css=mar_agent_css)
        else:
            flex_energy = characteristics.calc_characs_single(nodes=nodes, block_length=block_length,
                                                              bes_id=buyer_id, soc_state=opti_bes_res_buyer["res_soc"],
                                                              opti_res=opti_res[buyer_id], buyer=True)

        block_bid["flex_energy"] = flex_energy
        ### add block bid with remaining demand to next round
        buy_list_next_round.append(block_bid)

    new_sum_energy = 0  # reset sum energy for seller, otherwise it will be added up from previous block_bid loop
    # add bids only if there is untraded supply
    if sum(remaining_supply.values()) > 1e-3:
        add_sell_bid = True
    else:
        add_sell_bid = False
    if add_sell_bid == True:
        block_bid = {}
        # copy_of_sell_bid = copy.deepcopy(matched_bids_info_nego[r][match][1])
        for t in block_bid_time_steps:
            # Subtract the traded power from the original supply to get the new remaining supply
            block_bid[t] = [matched_bids[r][match][1][t][0],  # price
                            max(0, remaining_supply[t]),  # remaining supply
                            'False',  # False --> selling
                            matched_bids[r][match][1][t][3]  # bes_id
                            ]
            # copy_of_buy_bid[t][1] = new_remaining_demand[t]
            # new_total_price += copy_of_buy_bid[t][0]
            # count += 1
            new_sum_energy += block_bid[t][1]
        block_bid["bes_id"] = matched_bids[r][match][1][t][3]
        block_bid["quantity"] = new_sum_energy / len(block_bid_time_steps)
        block_bid["sum_energy"] = new_sum_energy
        block_bid["total_price"] = matched_bids[r][match][1][t][0]
        block_bid["mean_price"] = matched_bids[r][match][1][t][0]
        block_bid["ignored_demand"] = matched_bids[r][match][1]["ignored_demand"]
        if seller_id == options["nb_bes"]:  # if central supply system is in block_bid
            flex_energy = characteristics.calc_characs_single_css(block_length, soc_state=opti_bes_res_seller["res_soc"],
                                                                  opti_res_css=opti_res_css, mar_agent_css=mar_agent_css)
        else:
            flex_energy = characteristics.calc_characs_single(nodes=nodes, block_length=block_length,
                                                            bes_id=seller_id, soc_state=opti_bes_res_seller["res_soc"],
                                                            opti_res=opti_res[seller_id], buyer=False)

        block_bid["flex_energy"] = flex_energy
        ### add block bid with remaining supply to next round
        sell_list_next_round.append(block_bid)

    return buy_list_next_round, sell_list_next_round

# CALCULATE CRITERIA FOR SORTING BLOCK BIDS (mean price, mean quantity, or characteristic)
def mean_all(block_bid):
    """
    Calculates the mean value of the matching criteria of a block bid.
    Return: mean_price, sum_energy, mean_quantity
    """

    # calculate mean price, mean quantity (stored in block_bid)
    # total_price = 0
    count = 0
    sum_energy = 0
    bes_id_list = []
    # block_length = len(block_bid)

    for t in block_bid:  # iterate through time steps
        # total_price += block_bid[t][0]
        count += 1
        sum_energy += block_bid[t][1]
        bes_id_list.append(block_bid[t][3])

    mean_price = block_bid[t][0]
    mean_quantity = sum_energy / count if count > 0 else 0
    bes_id = bes_id_list[0]

    return bes_id, mean_price, sum_energy, mean_quantity

def seperate_block_bids(block_bid, characs):
    # ------------------- SEPARATE BLOCK BIDS INTO BUY AND SELL LISTS ------------------- #
    buy_list = []  # list for all buying bids
    sell_list = []  # list for all selling bids
    for n in range(len(block_bid)):  # iterate through buildings
        # check for css
        if "css" in block_bid:
            if n == len(block_bid) - 1:
                break
        # Add str whether buying or not to bool_list
        bool_list = []
        for t in block_bid["bes_" + str(n)]:
            if isinstance(block_bid["bes_" + str(n)][t], list):
                bool_list.append(block_bid["bes_" + str(n)][t][2])

        # Check if str is True or None and not False
        # and append block bid to buy_list
        #if ("True" in bool_list or "None" in bool_list) and "False" not in bool_list:
        if ("True" in bool_list) and "False" not in bool_list:
            buy_list.append(block_bid["bes_" + str(n)])
            i = len(buy_list) - 1
            # append block_bid_info to buy_list
            bes_id, mean_price, sum_energy, mean_quantity \
                = mean_all(block_bid=block_bid["bes_" + str(n)])
            # add flexible energy forced & delayed to buy_list (only first timestep, since it is calculated for 36h)
            buy_block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                  "quantity": mean_quantity,
                                  "flex_energy": min(characs[bes_id]["energy_bid_avg_forced_heat"]
                                                     + characs[bes_id]["energy_bid_avg_forced_bat"],
                                                     characs[bes_id]["energy_bid_avg_delayed_heat"]
                                                     + characs[bes_id]["energy_bid_avg_delayed_bat"]),
                                  "ignored_demand": False}
            buy_list[i].update(buy_block_bid_info)
            if buy_block_bid_info["quantity"] == 0:
                del buy_list[i]

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
                    sell_list[i][t][0] = 0.09  # set price to 0
                    sell_list[i][t][1] = 0  # set quantity to 0
                    sell_list[i][t][2] = str("False")  # set str to False
                # ignored demand at each time step t is difference between quantity in sellers block bid and in
                # sell list and will be traded with grid at end of negotiation rounds
                ignored_demand[t] = block_bid["bes_"+str(n)][t][1] - sell_list[i][t][1]
            if sum(ignored_demand.values()) > 0:
                bid_info = {"ignored_demand": True}
            else:
                bid_info = {"ignored_demand": False}

            # append block_bid_info to sell_list
            bes_id, mean_price, sum_energy, mean_quantity = mean_all(block_bid=sell_list[i])
            # add flexible energy forced & delayed to sell_list (only first timestep, since it is calculated for 36h)
            sell_block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                   "quantity": mean_quantity,
                                   "flex_energy": min(characs[bes_id]["energy_bid_avg_delayed_heat"]
                                                      + characs[bes_id]["energy_bid_avg_forced_bat"],
                                                      characs[bes_id]["energy_bid_avg_forced_heat"]
                                                      + characs[bes_id]["energy_bid_avg_delayed_bat"]),
                                   "ignored_demand": bid_info["ignored_demand"]}
            sell_list[i].update(sell_block_bid_info)
            if sell_block_bid_info["quantity"] == 0:
                del sell_list[i]

            sublist_copy = copy.deepcopy(block_bid["bes_" + str(n)])
            buy_list.append(sublist_copy)
            i = len(buy_list) - 1
            # Set quantity and price to 0 at time steps where the string is False (seller wants to sell)
            # buy list only contains the quantities & prices to be bought
            for t in sublist_copy:
                buy_list[i][t][2] = str("True")  # set str to True
                buy_list[i][t][1] = ignored_demand[t]

            # append block_bid_info to buy_list
            bes_id, mean_price, sum_energy, mean_quantity = mean_all(block_bid=buy_list[i])
            buy_block_bid_info = {"bes_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                   "quantity": mean_quantity,
                                   "flex_energy": min(characs[bes_id]["energy_bid_avg_delayed_heat"]
                                                      + characs[bes_id]["energy_bid_avg_forced_bat"],
                                                      characs[bes_id]["energy_bid_avg_forced_heat"]
                                                      + characs[bes_id]["energy_bid_avg_delayed_bat"]),
                                   "ignored_demand": bid_info["ignored_demand"]}
            buy_list[i].update(buy_block_bid_info)
            if buy_block_bid_info["quantity"] == 0:
                del buy_list[i]

    if "css" in block_bid:  # if central supply system is in block_bid
        # Add str whether buying or not to bool_list
        bool_list = []
        # iterate through time steps
        for t in block_bid["css"]:
            if isinstance(block_bid["css"][t], list):
                bool_list.append(block_bid["css"][t][2])
        # Check if str is True or None and not False
        # and append block bid to buy_list
        # if ("True" in bool_list or "None" in bool_list) and "False" not in bool_list:
        if ("True" in bool_list) and "False" not in bool_list:
            buy_list.append(block_bid["css"])
            i = len(buy_list) - 1
            # append block_bid_info to buy_list
            bes_id, mean_price, sum_energy, mean_quantity \
                = mean_all(block_bid=block_bid["css"])
            # add flexible energy forced & delayed to buy_list (only first timestep, since it is calculated for 36h)
            buy_block_bid_info = {"css_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                    "quantity": mean_quantity,
                                    "flex_energy": min(characs["css"]["energy_bid_avg_forced_bat"],
                                                       characs["css"]["energy_bid_avg_delayed_bat"]),
                                    "ignored_demand": False}
            buy_list[i].update(buy_block_bid_info)
            if buy_block_bid_info["quantity"] == 0:
                del buy_list[i]

        # Check if at least one value is False & append block bid to sell_list
        elif "False" in bool_list:
            # Make a deepcopy to avoid modifying the original sublist in block_bid
            sublist_copy = copy.deepcopy(block_bid["css"])
            sell_list.append(sublist_copy)
            i = len(sell_list) - 1
            ignored_demand = {}
            # Set quantity and price to 0 at time steps where the string is True (seller wants to buy)
            # sell list only contains the quantities & prices to be sold
            for t in sublist_copy:
                if isinstance(sublist_copy[t], list) and sublist_copy[t][2] == "True":
                    sell_list[i][t][0] = 0.09  # set price to 0
                    sell_list[i][t][1] = 0  # set quantity to 0
                    sell_list[i][t][2] = str("False")  # set str to False
                # ignored demand at each time step t is difference between quantity in sellers block bid and in
                # sell list and will be traded with grid at end of negotiation rounds
                ignored_demand[t] = block_bid["css"][t][1] - sell_list[i][t][1]
            if sum(ignored_demand.values()) > 0:
                bid_info = {"ignored_demand": True}
            else:
                bid_info = {"ignored_demand": False}

            # append block_bid_info to sell_list
            bes_id, mean_price, sum_energy, mean_quantity = mean_all(block_bid=sell_list[i])
            # add flexible energy forced & delayed to sell_list (only first timestep, since it is calculated for 36h)
            sell_block_bid_info = {"css_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                    "quantity": mean_quantity,
                                    "flex_energy": min(characs["css"]["energy_bid_avg_forced_bat"],
                                                      characs["css"]["energy_bid_avg_delayed_bat"]),
                                   "ignored_demand": bid_info["ignored_demand"]}
            sell_list[i].update(sell_block_bid_info)
            if sell_block_bid_info["quantity"] == 0:
                del sell_list[i]

            sublist_copy = copy.deepcopy(block_bid["css"])
            buy_list.append(sublist_copy)
            i = len(buy_list) - 1
            # Set quantity and price to 0 at time steps where the string is False (seller wants to sell)
            # buy list only contains the quantities & prices to be bought
            for t in sublist_copy:
                buy_list[i][t][2] = str("True")  # set str to True
                buy_list[i][t][1] = ignored_demand[t]

            # append block_bid_info to buy_list
            bes_id, mean_price, sum_energy, mean_quantity = mean_all(block_bid=buy_list[i])
            buy_block_bid_info = {"css_id": bes_id, "mean_price": mean_price, "sum_energy": sum_energy,
                                    "quantity": mean_quantity,
                                    "flex_energy": min(characs["css"]["energy_bid_avg_forced_bat"],
                                                     characs["css"]["energy_bid_avg_delayed_bat"]),
                                  "ignored_demand": bid_info["ignored_demand"]}
            buy_list[i].update(buy_block_bid_info)
            if buy_block_bid_info["quantity"] == 0:
                del buy_list[i]

    return buy_list, sell_list

def sort_block_bids(options, buy_list, sell_list, sorted_bids, r, par_rh, n_opt, block_length):
    """
    All block bids are sorted by the criteria specified in options["crit_prio"].
    Returns:
        block_bids (nested dict): {buy/sell: position i: time steps t0-t2: [p, q, n]}
    """

    # ------------------- SORT BLOCK BIDS BY CRITERIA DEFINED IN OPTIONS -------------------

    # sort buy_list and sell_list by mean price of block_bids if mean price has been specified as criteria in options
    if options["crit_prio"] == "mean_price":
        sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_price"], reverse=True)
        sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_price"], reverse=True)

    # sort buy_list and sell_list by mean quantity if mean quantity has been specified as criteria in options
    elif options["crit_prio"] == "quantity":
        sorted_buy_list = sorted(buy_list, key=lambda x: x["quantity"], reverse=True)
        sorted_sell_list = sorted(sell_list, key=lambda x: x["quantity"], reverse=True)

    elif options["crit_prio"] == "flex_quantity":
        sorted_sell_list = sorted(sell_list, key=lambda x: x["quantity"], reverse=True)
        sorted_buy_list = sorted(buy_list, key=lambda x: x["flex_energy"], reverse=True)

    # sort buy_list and sell_list by flexible mean energy if mean energy has been specified as criteria in options
    elif options["crit_prio"] == "flex_energy":
        # most flexible seller is the one, that can sell less than given in sell quantity (soc of tes is low -> energy_forced high)
        sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"]], reverse=True)  # delayed
        # least flexible buyer is the one, that can not buy less than given buy quantity (soc of tes is low -> energy_delayed low)
        sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"]])

    # sort buy_list and sell_list by trading quantity and mean price if quantity_x_price has been specified as criteria in options
    elif options["crit_prio"] == "quantity_x_price":
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            sorted_buy_list = sorted(buy_list, key=lambda x: x["quantity"]*x[t][0], reverse=True)
            sorted_sell_list = sorted(sell_list, key=lambda x: x["quantity"]*x[t][0], reverse=True)
        #sorted_buy_list = sorted(buy_list, key=lambda x: x["quantity"]*x["mean_price"], reverse=True)
        #sorted_sell_list = sorted(sell_list, key=lambda x: x["quantity"]*x["total_price"], reverse=True)

    elif options["crit_prio"] == "random":
        sorted_buy_list = buy_list
        random.shuffle(sorted_buy_list)

        sorted_sell_list = sell_list
        random.shuffle(sorted_sell_list)

    # STORE SORTED BUY AND SELL LISTS IN ONE DICTIONARY TO RETURN
    if r is None:
        sorted_bids[0] = {"buy_blocks": sorted_buy_list,
                          "sell_blocks": sorted_sell_list}
    else:
        sorted_bids[r+1] = {"buy_blocks": sorted_buy_list,
                            "sell_blocks": sorted_sell_list}

    return sorted_bids