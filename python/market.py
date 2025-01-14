from python import opti_bes_negotiation
from python import opti_css
from python import block_bids

import copy
import numpy as np

def matching(sorted_bids):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

    # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st
    # sell bid, 2nd buy bid matches with 2nd sell bid, etc.)
    if len(sorted_bids["buy_blocks"]) != 0 and len(sorted_bids["sell_blocks"]) != 0:
        matched_bids_info = list(zip(sorted_bids["buy_blocks"], sorted_bids["sell_blocks"]))

    else:
        matched_bids_info = []
        print("No matched bids for this optimization period.")

    return matched_bids_info

def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, sorted_bids, block_length,
                opti_res):
    """Run the optimization problem for the negotiation phase (taking into account
    bid quantities and prices of matched peer).

    Returns:
        nego_transactions (dict): Dictionary containing the results of the negotiation phase for each match.
        total_market_info (dict): Dictionary containing the results of the total market (all matched and unmatched peers).
        last_time_step (int): Last time step of the optimization horizon.

        nego_transactions, participating_buyers, participating_sellers, sorted_bids, last_time_step, matched_bids_info
        """

    # Get the last time step of the block bid
    block_bid_time_steps = par_rh["time_steps"][n_opt][0:block_length]

    # Initialize variables for the negotiation phase
    # todo: determine the number of trading rounds r
    r = 1  # trading rounds
    max_rounds = options["max_trading_rounds"]  # maximum number of trading rounds
    num_bes = len(opti_res)

    # Dicts to store results
    neg_res = {r: {}}
    prev_trade = {}
    for n in range(num_bes):
        prev_trade[n]  = {}
        prev_trade[n]["sell"] = {}
        prev_trade[n]["buy"] = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            prev_trade[n]["sell"][t] = 0
            prev_trade[n]["buy"][t] = 0
    matched_pairs = []

    # --------------------- START NEGOTIATION ---------------------

    # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
    while len(sorted_bids[r]["sell_blocks"]) > 0 and len(sorted_bids[r]["buy_blocks"]) > 0 and r < max_rounds:

        # create new variables for the next trading round
        sorted_bids[r + 1] = {"buy_blocks": [], "sell_blocks": []}
        matched_bids_info[r + 1] = []
        neg_res[r + 1] = {}
        buy_list_next_round = []
        sell_list_next_round = []
        # buyer and seller of each match run their optimization model
        # until their price_trade difference to average price is less than 0.005
        for match in range(len(matched_bids_info[r])):

            neg_res[r][match] = {
                    "buyer_id": matched_bids_info[r][match][0]["bes_id"],
                    "seller_id": matched_bids_info[r][match][1]["bes_id"],
                    "trading_price": {},
                    "trading_quantity": {},
                    "trading_cost": {},
                    "saved_costs": {},
                    "trading_revenue": {},
                    "additional_revenue": {},
                    "remaining_demand": {},
                    "remaining_supply": {},
                    # "opti_bes_res_buyer": opti_bes_res_buyer,
                    # "opti_bes_res_seller": opti_bes_res_seller,
                }

            buyer_id = matched_bids_info[r][match][0]["bes_id"]
            seller_id = matched_bids_info[r][match][1]["bes_id"]

            # price adjustment for negotiation
            trading_price = calculate_trading_price(par_rh, n_opt, block_length, matched_bids_info, r, match)

            #### run the optimization model for buyer and seller ###
            #try:
            opti_bes_res_buyer = {}
            opti_bes_res_buyer \
                        = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params,
                                                            par_rh=par_rh,
                                                            init_val=init_val["building_" + str(buyer_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded = prev_trade[buyer_id], r = r,
                                                            is_buying=True, trading_price=trading_price,
                                                            block_length=block_length, opti_res = opti_res[buyer_id],
                                                            opti_bes_res_buyer = opti_bes_res_buyer)

            opti_bes_res_seller \
                        = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(seller_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded=prev_trade[seller_id], r=r,
                                                            is_buying=False, trading_price=trading_price,
                                                            block_length=block_length, opti_res = opti_res[seller_id],
                                                            opti_bes_res_buyer = opti_bes_res_buyer)

            # replacing the initial opti results with opti regarding trading
            opti_res[buyer_id] = opti_bes_negotiation.replace_opti_res(opti_res[buyer_id], opti_bes_res_buyer,
                                                                           par_rh, n_opt)
            opti_res[seller_id] = opti_bes_negotiation.replace_opti_res(opti_res[seller_id], opti_bes_res_seller,
                                                                            par_rh, n_opt)
            matched_pairs.append([buyer_id, seller_id])

            # store the results of the negotiation for this match and this round
            neg_res[r][match], prev_trade = save_negotiation_results(neg_res[r][match], opti_bes_res_buyer,
                                                                     opti_bes_res_seller, trading_price, prev_trade,
                                                                     buyer_id, seller_id, block_bid_time_steps, params)
            #except:
            #    print(1111111111)
            #    pass

            # ---------- BIDS FOR NEXT ROUND ---------- #
            buy_list_next_round , sell_list_next_round = \
                    block_bids.compute_block_bids_during_negotiation(matched_bids_info, r, match, neg_res[r][match]["remaining_demand"],
                                          block_bid_time_steps, nodes, block_length, buyer_id, opti_bes_res_buyer, opti_res, buy_list_next_round,
                                          neg_res[r][match]["remaining_supply"], seller_id, opti_bes_res_seller, sell_list_next_round)


        # Add all buyers/sellers that weren't matched (but were in sorted bids list) to the new sorted_bids_nego lists
        if len(sorted_bids[r]["buy_blocks"]) > len(sorted_bids[r]["sell_blocks"]):
            # Retrieve the remaining buy blocks
            remaining_buy_blocks = sorted_bids[r]["buy_blocks"][len(sorted_bids[r]["sell_blocks"]):]
            for buy_block in remaining_buy_blocks:
                if buy_block["quantity"] > 0:
                    buy_list_next_round.append(buy_block)

        elif len(sorted_bids[r]["buy_blocks"]) < len(sorted_bids[r]["sell_blocks"]):
            # Retrieve the remaining sell blocks
            remaining_sell_blocks = sorted_bids[r]["sell_blocks"][len(sorted_bids[r]["buy_blocks"]):]
            for sell_block in remaining_sell_blocks:
                if sell_block["quantity"] > 0:
                    sell_list_next_round.append(sell_block)

        # --------------------- SORT BUYERS AND SELLERS FOR NEXT TRADING ROUND ---------------------
        sorted_bids = block_bids.sort_block_bids(options=options, buy_list=buy_list_next_round,
                                                 sell_list=sell_list_next_round, sorted_bids=sorted_bids, r=r)

        # match all buyers and sellers for the next trading round
        matched_bids_info[r + 1] = matching_during_negotiation(sorted_bids[r + 1], matched_pairs)

        # go to next negotiation trading round
        r += 1

    print("Finished all negotiations for time steps " + str(block_bid_time_steps[0]) + " to " + str(block_bid_time_steps[-1]) + ".")

    return (neg_res, sorted_bids,  matched_bids_info), opti_res

def calculate_trading_price(par_rh, n_opt, block_length, matched_bids, r, match):
    # todo: delta_prices in abh. der Gebotsmengen und deren Differenzen
    bid_quantity_seller = {}
    bid_quantity_buyer = {}
    ratio = {}
    if matched_bids[r][match][0]["flex_energy"] >= matched_bids[r][match][1]["flex_energy"]:
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            bid_quantity_seller[t] = matched_bids[r][match][1][t][1]
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            try:
                ratio[t] = bid_quantity_seller[t] / max(bid_quantity_seller.values())
            except ZeroDivisionError:
                ratio[t] = 0
        trading_price = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            trading_price[t] = min(matched_bids[r][match][1][t][0], matched_bids[r][match][0][t][0]) \
                               + (1 - ratio[t]) * (max(matched_bids[r][match][1][t][0],
                                                       matched_bids[r][match][0][t][0])
                                                   - min(matched_bids[r][match][1][t][0],
                                                         matched_bids[r][match][0][t][0]))
    elif matched_bids[r][match][1]["flex_energy"] > matched_bids[r][match][0]["flex_energy"]:
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            bid_quantity_buyer[t] = matched_bids[r][match][0][t][1]
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            try:
                ratio[t] = bid_quantity_buyer[t] / max(bid_quantity_buyer.values())
            except ZeroDivisionError:
                ratio[t] = 0
        trading_price = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            trading_price[t] = max(matched_bids[r][match][1][t][0], matched_bids[r][match][0][t][0]) \
                               + (1 - ratio[t]) * (min(matched_bids[r][match][1][t][0],
                                                       matched_bids[r][match][0][t][0])
                                                   - max(matched_bids[r][match][1][t][0],
                                                         matched_bids[r][match][0][t][0]))

    return trading_price

def save_negotiation_results(neg_res, opti_bes_res_buyer, opti_bes_res_seller, trading_price, prev_trade,
                             buyer_id, seller_id, block_bid_time_steps, params):
    # ---------- RESULTS OF NEGOTIATION FOR THIS MATCH AND THIS ROUND ---------- #
    for t in block_bid_time_steps:

        # todo: hier nach noch eine opti?
        neg_res["trading_quantity"][t] = min(opti_bes_res_buyer["res_power_trade"][t],
                                             opti_bes_res_seller["res_power_trade"][t])

        # calculate the saved costs for this match compared to trading with grid
        neg_res["saved_costs"][t] = neg_res["trading_quantity"][t] / 1000 * (params["eco"]["pr", "el"] - trading_price[t])
        # calculate the trading costs
        neg_res["trading_cost"][t] = neg_res["trading_quantity"][t] / 1000 * trading_price[t]
        # calculate the additional revenue for this match compared to trading with grid
        neg_res["additional_revenue"][t] = neg_res["trading_quantity"][t] / 1000 * abs(trading_price[t] - params["eco"]["sell" + "_" + "pv"])
        # calculate the trading costs
        neg_res["trading_revenue"][t] = neg_res["trading_quantity"][t] / 1000 * trading_price[t]

        # remaining demand
        neg_res["remaining_demand"][t] = opti_bes_res_buyer["res_p_grid_buy"][t] + (
                    opti_bes_res_buyer["res_power_trade"][t] - neg_res["trading_quantity"][t])
        # remaining supply
        neg_res["remaining_supply"][t] = opti_bes_res_seller["res_p_grid_sell"][t] + (
                    opti_bes_res_seller["res_power_trade"][t] - neg_res["trading_quantity"][t])


        # store the traded quantity of each trader for the opti of next trading round r
        prev_trade[buyer_id]["buy"][t] += neg_res["trading_quantity"][t]  # buyer
        prev_trade[seller_id]["sell"][t] += neg_res["trading_quantity"][t]  # seller

    return neg_res, prev_trade

def matching_during_negotiation(sorted_block_bids, matched_pairs):
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

def negotiation_with_css():

    # while
    opti_res_css[n_opt] = opti_css.compute(mar_agent_css, params, par_rh, init_val, n_opt, matched_bids, prev_traded,
                                           trading_price, block_length)

def trade_with_grid(params, par_rh, n_opt, block_length, opti_res):

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

    #for seller in sorted_bids["sell_blocks"]:
    #    # trade ignored demand of sellers with grid
    #    for t in time_steps:
    #        power_from_grid[seller["bes_id"]][t] = seller.get("ignored_demand")[t]
   #         costs_power_from_grid[seller["bes_id"]][t] = (power_from_grid[seller["bes_id"]][t]/1000 * params["eco"]["pr", "el"])

    # --------------------- STORE THE RESULTS OF TRANSACTIONS WITH THE GRID ---------------------

    grid_transactions = {
        "power_from_grid": power_from_grid,
        "power_to_grid": power_to_grid,
        "costs_power_from_grid": costs_power_from_grid,
        "revenue_power_to_grid": revenue_power_to_grid,
    }

    return grid_transactions
