from python import opti_bes_negotiation
from python import characs_single_build
from python import characteristics

import random
import copy
import numpy as np
from python.last_opti import compute_last_opti


def matching(sorted_block_bids):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

    # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st
    # sell bid, 2nd buy bid matches with 2nd sell bid, etc.)
    if len(sorted_block_bids["buy_blocks"]) != 0 and len(sorted_block_bids["sell_blocks"]) != 0:
        matched_bids_info = list(zip(sorted_block_bids["buy_blocks"], sorted_block_bids["sell_blocks"]))

    else:
        matched_bids_info = []
        print("No matched bids for this optimization period.")

    return matched_bids_info

def matching_nego(sorted_block_bids, matched_pairs):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

    # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st
    # sell bid, 2nd buy bid matches with 2nd sell bid, etc.)
    matched_bids_info = {}
    possible_matches = []
    not_possible_matches = []
    if len(sorted_block_bids["buy_blocks"]) != 0 and len(sorted_block_bids["sell_blocks"]) != 0:
        if len(sorted_block_bids["buy_blocks"]) <= len(sorted_block_bids["sell_blocks"]):
            for b in range(len(sorted_block_bids["buy_blocks"])):
                if [sorted_block_bids["buy_blocks"][b]["bes_id"], sorted_block_bids["sell_blocks"][b]["bes_id"]] not in matched_pairs:
                    possible_matches.append([sorted_block_bids["buy_blocks"][b]["bes_id"], sorted_block_bids["sell_blocks"][b]["bes_id"]])
                else:
                    not_possible_matches.append([sorted_block_bids["buy_blocks"][b]["bes_id"], sorted_block_bids["sell_blocks"][b]["bes_id"]])
            x = len(not_possible_matches)
            max= 0
            while x > 1 and max < 5:
                ndarray = np.array(not_possible_matches)
                # Rotate the second column
                second_column = ndarray[:, 1]
                rotated_second_column = np.roll(second_column, 1)
                ndarray[:, 1] = rotated_second_column
                # Convert back to list
                not_possible_matches = ndarray.tolist()
                not_possible_matches_2 = copy.deepcopy(not_possible_matches)
                for b in range(x):
                    if not_possible_matches_2[b] not in matched_pairs:
                        possible_matches.append(not_possible_matches_2[b])
                        try:
                            not_possible_matches.remove(not_possible_matches_2[b])
                        except:
                            pass
                x = len(not_possible_matches)
                max += 1
            for i in range(len(possible_matches)):
                for b in range(len(sorted_block_bids["buy_blocks"])):
                    if sorted_block_bids["buy_blocks"][b]["bes_id"] == possible_matches[i][0]:
                        matched_bids_info[i] = [sorted_block_bids["buy_blocks"][b], []]
                for s in range(len(sorted_block_bids["sell_blocks"])):
                    if sorted_block_bids["sell_blocks"][s]["bes_id"] == possible_matches[i][1]:
                        matched_bids_info[i][1] = sorted_block_bids["sell_blocks"][s]

        elif len(sorted_block_bids["sell_blocks"]) < len(sorted_block_bids["buy_blocks"]):
            for s in range(len(sorted_block_bids["sell_blocks"])):
                if [sorted_block_bids["buy_blocks"][s]["bes_id"], sorted_block_bids["sell_blocks"][s]["bes_id"]] not in matched_pairs:
                    possible_matches.append([sorted_block_bids["buy_blocks"][s]["bes_id"], sorted_block_bids["sell_blocks"][s]["bes_id"]])
                else:
                    not_possible_matches.append([sorted_block_bids["buy_blocks"][s]["bes_id"], sorted_block_bids["sell_blocks"][s]["bes_id"]])
            x = len(not_possible_matches)
            max = 0
            while x > 1 and max < 5:
                ndarray = np.array(not_possible_matches)
                # Rotate the second column
                second_column = ndarray[:, 1]
                rotated_second_column = np.roll(second_column, 1)
                ndarray[:, 1] = rotated_second_column
                # Convert back to list
                not_possible_matches = ndarray.tolist()
                not_possible_matches_2 = copy.deepcopy(not_possible_matches)
                for b in range(x):
                    if not_possible_matches_2[b] not in matched_pairs:
                        possible_matches.append(not_possible_matches_2[b])
                        try:
                            not_possible_matches.remove(not_possible_matches_2[b])
                        except:
                            pass
                x = len(not_possible_matches)
                max += 1

            for i in range(len(possible_matches)):
                for b in range(len(sorted_block_bids["buy_blocks"])):
                    if sorted_block_bids["buy_blocks"][b]["bes_id"] == possible_matches[i][0]:
                        matched_bids_info[i] = [sorted_block_bids["buy_blocks"][b], []]
                for s in range(len(sorted_block_bids["sell_blocks"])):
                    if sorted_block_bids["sell_blocks"][s]["bes_id"] == possible_matches[i][1]:
                        matched_bids_info[i][1] = sorted_block_bids["sell_blocks"][s]

    else:
        matched_bids_info = []
        print("No matched bids for this optimization period.")

    return matched_bids_info

# Function to remove all but the first occurrence of sublists starting with the specified number
def remove_subsequent_sublists(main_list, num, buy):
    first_found = False
    for i in range(len(main_list) - 1, -1, -1):
        if main_list[i][buy] == num:
            if not first_found:
                first_found = True
            else:
                del main_list[i]


def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, sorted_bids, block_length,
                opti_res):
    """Run the optimization problem for the negotiation phase (taking into account
    bid quantities and prices of matched peer).

    Returns:
        nego_transactions (dict): Dictionary containing the results of the negotiation phase for each match.
        total_market_info (dict): Dictionary containing the results of the total market (all matched and unmatched peers).
        last_time_step (int): Last time step of the optimization horizon.

        nego_transactions, participating_buyers, participating_sellers, sorted_bids_nego, last_time_step, matched_bids_info_nego
        """

    # Get the time steps of the block bid
    block_bid_time_steps = par_rh["time_steps"][n_opt][0:block_length]
    last_time_step = block_bid_time_steps[-1]

    # Initialize variables for the negotiation phase
    r = 0  # trading rounds
    max_rounds = options["max_trading_rounds"]  # maximum number of trading rounds
    num_bes = len(opti_res)

    # Dicts to store results
    sorted_bids_nego = {r: sorted_bids}
    matched_bids_info_nego = {r: matched_bids_info}
    nego_transactions = {r: {}}
    prev_trade = {}
    for n in range(num_bes):
        prev_trade[n] = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            prev_trade[n][t] = 0
    matched_pairs = []

    # --------------------- START NEGOTIATION ---------------------

    # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
    while len(sorted_bids_nego[r]["sell_blocks"]) > 0 and len(sorted_bids_nego[r]["buy_blocks"]) > 0 and r < max_rounds:

        # create new variables for the next trading round
        sorted_bids_nego[r + 1] = {"buy_blocks": [], "sell_blocks": []}
        matched_bids_info_nego[r + 1] = []
        nego_transactions[r + 1] = {}
        buy_list_next_round = []
        sell_list_next_round = []
        # buyer and seller of each match run their optimization model
        # until their price_trade difference to average price is less than 0.005
        for match in range(len(matched_bids_info_nego[r])):
            nego_transactions[r][match] = {}
            trade_power = {}
            trading_cost = {}
            saved_costs = {}
            trading_revenue  = {}
            additional_revenue = {}
            remaining_demand = {}
            remaining_supply = {}
            buyer_id = matched_bids_info_nego[r][match][0]["bes_id"]
            seller_id = matched_bids_info_nego[r][match][1]["bes_id"]

            # price adjustment for negotiation
            # todo: delta_prices in abh. der Gebotsmengen und deren Differenzen
            bid_quantity_seller = {}
            ratio = {}
            for t in par_rh["time_steps"][n_opt][0:block_length]:
                bid_quantity_seller[t] = matched_bids_info_nego[r][match][1][t][1]
            for t in par_rh["time_steps"][n_opt][0:block_length]:
                try:
                    ratio[t] = bid_quantity_seller[t] / max(bid_quantity_seller.values())
                except ZeroDivisionError:
                    ratio[t] = 0
            trade_price = {}
            for t in par_rh["time_steps"][n_opt][0:block_length]:
                trade_price[t] = min(matched_bids_info_nego[r][match][1][t][0], matched_bids_info_nego[r][match][0][t][0]) \
                                    + (1 - ratio[t]) * (max(matched_bids_info_nego[r][match][1][t][0],
                                                                          matched_bids_info_nego[r][match][0][t][0])
                                                                      - min(matched_bids_info_nego[r][match][1][t][0],
                                                                            matched_bids_info_nego[r][match][0][t][0]))

            #### run the optimization model for buyer and seller ###
            try:
                opti_bes_res_buyer = {}
                print(buyer_id)
                opti_bes_res_buyer \
                        = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(buyer_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info_nego[r][match],
                                                            prev_traded = prev_trade[buyer_id], r = r,
                                                            is_buying=True, delta_price=trade_price,
                                                            block_length=block_length, opti_res = opti_res[buyer_id],
                                                            opti_bes_res_buyer = opti_bes_res_buyer)
                opti_res[buyer_id] = opti_bes_negotiation.replace_opti_res(opti_res[buyer_id], opti_bes_res_buyer,
                                                                           par_rh, n_opt)

                print(seller_id)
                opti_bes_res_seller \
                        = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(seller_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info_nego[r][match],
                                                            prev_traded=prev_trade[seller_id], r=r,
                                                            is_buying=False, delta_price=trade_price,
                                                            block_length=block_length, opti_res = opti_res[seller_id],
                                                            opti_bes_res_buyer = opti_bes_res_buyer)
                opti_res[seller_id] = opti_bes_negotiation.replace_opti_res(opti_res[seller_id], opti_bes_res_seller,
                                                                            par_rh, n_opt)
                matched_pairs.append([buyer_id, seller_id])

                # ---------- RESULTS OF NEGOTIATION FOR THIS MATCH AND THIS ROUND ---------- #
                for t in block_bid_time_steps:

                        trading_cost[t] = 0
                        saved_costs[t] = 0
                        trading_revenue[t] = 0
                        additional_revenue[t] = 0
                        trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t],
                                                opti_bes_res_seller["res_power_trade"][t])

                        # calculate the saved costs for this match compared to trading with grid
                        saved_costs[t] = trade_power[t]/1000 * (params["eco"]["pr", "el"] - trade_price[t])
                        # calculate the trading costs
                        trading_cost[t] = trade_power[t]/1000 * trade_price[t]
                        # calculate the additional revenue for this match compared to trading with grid
                        # todo: gibt nur ein p_min
                        if opti_res[seller_id][8]["pv"][t] > 1e-4:
                            additional_revenue[t] = trade_power[t]/1000 * abs(trade_price[t] - params["eco"]["sell" + "_" + "pv"])
                        elif opti_res[seller_id][8]["chp"][t] > 1e-4:
                            additional_revenue[t] = trade_power[t]/1000 * abs(trade_price[t] - params["eco"]["sell" + "_" + "chp"])
                        # calculate the trading costs
                        trading_revenue[t] = trade_power[t]/1000 * trade_price[t]

                        # remaining demand
                        # remaining_demand[t] = matched_bids_info_nego[r][match][0][t][1] - trade_power[t]
                        remaining_demand[t] = opti_bes_res_buyer["res_p_grid_buy"][t] + (opti_bes_res_buyer["res_power_trade"][t] - trade_power[t])
                        # remaining supply
                        # remaining_supply[t] = matched_bids_info_nego[r][match][1][t][1] - trade_power[t]
                        remaining_supply[t] = opti_bes_res_seller["res_p_grid_sell"][t] + (opti_bes_res_seller["res_power_trade"][t] - trade_power[t])
                        # store the traded quantity of each trader for the opti of next trading round r
                        prev_trade[buyer_id][t] += trade_power[t] # buyer
                        prev_trade[seller_id][t] += trade_power[t] # seller


                # ---------- BIDS FOR NEXT ROUND ---------- #
                new_sum_energy = 0
                res_soc_buyer = opti_bes_res_buyer["res_soc"]
                res_soc_seller = opti_bes_res_seller["res_soc"]

                # add bids only if there is untraded demand
                if sum(remaining_demand.values()) > 1e-3:
                    add_buy_bid = True
                else:
                    add_buy_bid = False
                # add unsatisfied buyers and sellers to next trading round with remaining demand/supply
                if add_buy_bid == True:
                    block_bid = {}
                    #copy_of_buy_bid = copy.deepcopy(matched_bids_info_nego[r][match][0])
                    for t in block_bid_time_steps:
                        # Subtract the traded power from the original demand to get the new remaining demand
                        block_bid[t] = [matched_bids_info_nego[r][match][0][t][0],     # price
                                        max(0, remaining_demand[t]), # remaining demand
                                            'True',                                    # True --> buying
                                            matched_bids_info_nego[r][match][0][t][3]  # bes_id
                                            ]
                        new_sum_energy += block_bid[t][1]
                    block_bid["bes_id"] = matched_bids_info_nego[r][match][0][t][3]
                    block_bid["quantity"] = new_sum_energy / len(block_bid_time_steps)
                    block_bid["sum_energy"] = new_sum_energy
                    block_bid["total_price"] = matched_bids_info_nego[r][match][0][t][0]
                    flex_energy = characteristics.calc_characs_single(nodes = nodes, block_length = block_length,
                                                                      bes_id = buyer_id, soc_state = res_soc_buyer,
                                                                      opti_res = opti_res[buyer_id], buyer = True)

                    block_bid["flex_energy"] = flex_energy
                    ### add block bid with remaining demand to next round
                    buy_list_next_round.append(block_bid)

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
                        block_bid[t] = [matched_bids_info_nego[r][match][1][t][0],  # price
                                        max(0, remaining_supply[t]),
                                        # remaining demand
                                        'False',  # False --> selling
                                        matched_bids_info_nego[r][match][1][t][3]  # bes_id
                                        ]
                        # copy_of_buy_bid[t][1] = new_remaining_demand[t]
                        # new_total_price += copy_of_buy_bid[t][0]
                        # count += 1
                        new_sum_energy += block_bid[t][1]
                    block_bid["bes_id"] = matched_bids_info_nego[r][match][1][t][3]
                    block_bid["quantity"] = new_sum_energy / len(block_bid_time_steps)
                    block_bid["sum_energy"] = new_sum_energy
                    block_bid["total_price"] = matched_bids_info_nego[r][match][1][t][0]
                    flex_energy = characteristics.calc_characs_single(nodes = nodes, block_length = block_length,
                                                                      bes_id = seller_id, soc_state = res_soc_seller,
                                                                      opti_res = opti_res[seller_id], buyer = False)


                    block_bid["flex_energy"] = flex_energy
                    ### add block bid with remaining supply to next round
                    sell_list_next_round.append(block_bid)

                # store the results of the negotiation for this match and this round
                # inlcude traded quantity of each trader into the opti for next trading round r
                nego_transactions[r][match] = {
                    "buyer": matched_bids_info_nego[r][match][0]["bes_id"],
                    "seller": matched_bids_info_nego[r][match][1]["bes_id"],
                    "price": trade_price,
                    "quantity": trade_power,
                    "trading_cost": trading_cost,
                    "saved_costs": saved_costs,
                    "trading_revenue": trading_revenue,
                    "additional_revenue": additional_revenue,
                    "remaining_demand": remaining_demand,
                    "remaining_supply": remaining_supply,
                    "opti_bes_res_buyer": opti_bes_res_buyer,
                    "opti_bes_res_seller": opti_bes_res_seller,
                }
            except:
                pass

        # Add all buyers/sellers that weren't matched (but were in sorted bids list) to the new sorted_bids_nego lists
        if len(sorted_bids_nego[r]["buy_blocks"]) > len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining buy blocks
            remaining_buy_blocks = sorted_bids_nego[r]["buy_blocks"][len(sorted_bids_nego[r]["sell_blocks"]):]
            for buy_block in remaining_buy_blocks:
                if buy_block["quantity"] > 0:
                    buy_list_next_round.append(buy_block)

        elif len(sorted_bids_nego[r]["buy_blocks"]) < len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining sell blocks
            remaining_sell_blocks = sorted_bids_nego[r]["sell_blocks"][len(sorted_bids_nego[r]["buy_blocks"]):]
            for sell_block in remaining_sell_blocks:
                if sell_block["quantity"] > 0:
                    sell_list_next_round.append(sell_block)

        # --------------------- SORT BUYERS AND SELLERS FOR NEXT TRADING ROUND ---------------------
        #buy_list = copy.deepcopy(sorted_bids_nego[r + 1]["buy_blocks"])
        #sell_list = copy.deepcopy(sorted_bids_nego[r + 1]["sell_blocks"])

        if options["crit_prio"] == "mean_price":
            # highest paying and lowest asking first if descending has been set True in options
            if options["descending"]:
                sorted_buy_list = sorted(buy_list_next_round, key=lambda x: x["mean_price"], reverse=True)
                sorted_sell_list = sorted(sell_list_next_round, key=lambda x: x["mean_price"], reverse=True)
                #sorted_bids_nego[r + 1]["sell_blocks"].clear()
                #sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        elif options["crit_prio"] == "quantity":
            if options["descending"]:
                sorted_buy_list = sorted(buy_list_next_round, key=lambda x: x["quantity"], reverse=True)
                sorted_sell_list = sorted(sell_list_next_round, key=lambda x: x["quantity"], reverse=True)
                #sorted_bids_nego[r + 1]["sell_blocks"].clear()
                #sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
                # todo: to avoid that exactly the same buyers and sellers are matched for the next round
                sorted_bids_nego[r + 1]["buy_blocks"] = sorted_bids_nego[r + 1]["buy_blocks"][1:] + \
                                                            sorted_bids_nego[r + 1]["buy_blocks"][:1]


        elif options["crit_prio"] == "flex_energy":
            # highest (lowest) energy flexibility of seller (buyer) first if descending has been set True in options
            if options["descending"]:
                sorted_sell_list = sorted(sell_list_next_round, key=lambda x: x[options["crit_prio"]])
                sorted_buy_list = sorted(buy_list_next_round, key=lambda x: x[options["crit_prio"]], reverse=True)
                #sorted_bids_nego[r + 1]["sell_blocks"].clear()
                #sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
                # todo: to avoid that exactly the same buyers and sellers are matched for the next round
                sorted_bids_nego[r + 1]["buy_blocks"] = sorted_bids_nego[r + 1]["buy_blocks"][1:] + \
                                                            sorted_bids_nego[r + 1]["buy_blocks"][:1]

        elif options["crit_prio"] == "flex_quantity":
            # highest (lowest) energy flexibility of seller (buyer) first if descending has been set True in options
            if options["descending"]:
                sorted_sell_list = sorted(sell_list_next_round, key=lambda x: x["quantity"], reverse=True)
                sorted_buy_list = sorted(buy_list_next_round, key=lambda x: x["flex_energy"], reverse=True)
                #sorted_bids_nego[r + 1]["sell_blocks"].clear()
                #sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
                # todo: to avoid that exactly the same buyers and sellers are matched for the next round
                sorted_bids_nego[r + 1]["buy_blocks"] = sorted_bids_nego[r + 1]["buy_blocks"][1:] + sorted_bids_nego[r + 1]["buy_blocks"][:1]


        # randomly sort buy_list and sell_list if it has been specified as criteria in options
        elif options["crit_prio"] == "random":
            sorted_buy_list = copy.deepcopy(buy_list_next_round)
            random.shuffle(sorted_buy_list)
            sorted_sell_list = copy.deepcopy(sell_list_next_round)
            random.shuffle(sorted_sell_list)

            #sorted_bids_nego[r + 1]["sell_blocks"].clear()
            #sorted_bids_nego[r + 1]["buy_blocks"].clear()
            for e in sorted_sell_list:
                sorted_bids_nego[r + 1]["sell_blocks"].append(e)
            for e in sorted_buy_list:
                sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        # match all buyers and sellers for the next trading round
        matched_bids_info_nego[r + 1] = matching_nego(sorted_bids_nego[r + 1], matched_pairs)

        # go to next negotiation trading round
        r += 1

    print("Finished all negotiations for time steps " + str(block_bid_time_steps[0]) + " to " + str(block_bid_time_steps[-1]) + ".")

    return (nego_transactions, sorted_bids_nego, last_time_step,
            matched_bids_info_nego), opti_res

def trade_with_grid(sorted_bids, params, par_rh, n_opt, block_length, opti_res):

    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    nb_bes = len(opti_res)

    # Initialize all necessary variables
    power_from_grid = {}
    power_to_grid = {}
    costs_power_from_grid = {}
    revenue_power_to_grid = {}
    for bes_id in range(nb_bes):
        power_from_grid[bes_id] = {}
        power_to_grid[bes_id] = {}
        costs_power_from_grid[bes_id] = {}
        revenue_power_to_grid[bes_id] = {}

        for t in time_steps:
            # --------------------- BUYERS IMPORT FROM GRID ---------------------
            if opti_res[bes_id][17] != {}:
                power_from_grid[bes_id][t] = opti_res[bes_id][17][t]
                costs_power_from_grid[bes_id][t] = opti_res[bes_id][17][t]/1000 * params["eco"]["pr", "el"]
            # --------------------- SELLERS INJECT INTO GRID ---------------------
            if opti_res[bes_id][18] != {}:
                power_to_grid[bes_id][t] = opti_res[bes_id][18][t]
                revenue_power_to_grid[bes_id][t] = opti_res[bes_id][18][t]/1000 * params["eco"]["sell" + "_" + "pv"]

    for seller in sorted_bids["sell_blocks"]:
        # trade ignored demand of sellers with grid
        for t in time_steps:
            power_from_grid[seller["bes_id"]][t] = seller.get("ignored_demand")[t]
            costs_power_from_grid[seller["bes_id"]][t] = (power_from_grid[seller["bes_id"]][t]/1000 * params["eco"]["pr", "el"])

    # --------------------- STORE THE RESULTS OF TRANSACTIONS WITH THE GRID ---------------------

    grid_transactions = {
        "power_from_grid": power_from_grid,
        "power_to_grid": power_to_grid,
        "costs_power_from_grid": costs_power_from_grid,
        "revenue_power_to_grid": revenue_power_to_grid,
    }

    return grid_transactions
