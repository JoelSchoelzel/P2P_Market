from python import opti_bes_negotiation
# from python import opti_css
from python import block_bids
from python import opti_css_negotiation

import copy
import numpy as np

# from python.market_agents import mar_agent_css


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


def matching_price_check(sorted_bids):
    """Match the sorted block bids of the buyers to the ones of the sellers with price checking and buyer rolling.
    If the price condition (buyer_price >= seller_price) is not met, the buyer will be rolled.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Only pairs where buyer price >= seller price are included.
    """
    matched_bids_info = []

    # Check if there are both buyers and sellers
    if len(sorted_bids["buy_blocks"]) != 0 and len(sorted_bids["sell_blocks"]) != 0:
        buyers = sorted_bids["buy_blocks"]
        sellers = sorted_bids["sell_blocks"]

        # Iterate through each seller
        for seller in sellers:
            seller_price = seller["mean_price"]
            match_found = False

            # Try to match the seller with buyers
            for _ in range(len(sorted_bids.get("buy_blocks", [])[:])):
                if not buyers:  # If no buyers are left
                    break

                # Take the first buyer
                buyer = buyers[0]
                buyer_price = buyer["mean_price"]

                # Check price condition
                if buyer_price >= seller_price:
                    # Valid match, append and remove buyer from the queue
                    matched_bids_info.append((buyer, seller))
                    # buyers.pop(0)  # Remove matched buyer
                    remaining_buyers = buyers[1:]
                    buyers = remaining_buyers
                    match_found = True
                    break
                else:
                    # Roll the buyer (move to the end of the list)
                    buyers.append(buyers.pop(0))

    else:
        print("No matched bids for this optimization period.")

    return matched_bids_info


def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, sorted_bids, block_length,
                opti_res, opti_res_css: dict = None, mar_agent_css: object = None):
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
    r = 0  # trading rounds start at 0
    max_rounds = options["max_trading_rounds"]  # maximum number of trading rounds
    num_bes = len(opti_res)
    t = par_rh["time_steps"][n_opt][0]

    # Dicts to store results
    neg_res = {r: {}}
    prev_trade = {}
    for n in range(num_bes):
        prev_trade[n] = {}
        prev_trade[n]["sell"] = {}
        prev_trade[n]["buy"] = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            prev_trade[n]["sell"][t] = 0
            prev_trade[n]["buy"][t] = 0
    if options["central_supply_system"]:
        prev_trade["css"] = {}
        prev_trade["css"]["sell"] = {}
        prev_trade["css"]["buy"] = {}
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            prev_trade["css"]["sell"][t] = 0
            prev_trade["css"]["buy"][t] = 0
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
                    "buyer_id": matched_bids_info[r][match][0][t][3],
                    "seller_id": matched_bids_info[r][match][1][t][3],
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

            buyer_id = matched_bids_info[r][match][0][t][3]
            seller_id = matched_bids_info[r][match][1][t][3]

            # price adjustment for negotiation
            trading_price = calculate_trading_price(par_rh, n_opt, block_length, matched_bids_info, r, match)
            neg_res[r][match]["trading_price"] = trading_price

            #### run the optimization model for buyer and seller ###
            #try:
            opti_bes_res_buyer = {}
            opti_bes_res_seller = {}
            if buyer_id < options["nb_bes"]:
                opti_bes_res_buyer \
                        = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params,
                                                            par_rh=par_rh,
                                                            init_val=init_val["building_" + str(buyer_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded=prev_trade[buyer_id], r=r,
                                                            is_buying=True, trading_price=trading_price,
                                                            block_length=block_length, opti_res=opti_res[buyer_id],
                                                            opti_bes_res_buyer=opti_bes_res_buyer)
            elif buyer_id == options["nb_bes"]:  # if buyer is the central supply system
                opti_bes_res_buyer \
                        = opti_css_negotiation.compute_opti(params=params, par_rh=par_rh,
                                                            init_val=init_val["css"],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded=prev_trade["css"], r=r,
                                                            is_buying=True, trading_price=trading_price,
                                                            block_length=block_length,
                                                            opti_bes_res_buyer=opti_bes_res_buyer,
                                                            opti_res_css=opti_res_css,
                                                            mar_agent_css=mar_agent_css)

            if seller_id < options["nb_bes"]:
                opti_bes_res_seller \
                        = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(seller_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded=prev_trade[seller_id], r=r,
                                                            is_buying=False, trading_price=trading_price,
                                                            block_length=block_length, opti_res=opti_res[seller_id],
                                                            opti_bes_res_buyer=opti_bes_res_buyer)
            elif seller_id == options["nb_bes"]:  # if seller is the central supply system
                opti_bes_res_seller \
                        = opti_css_negotiation.compute_opti(params=params, par_rh=par_rh,
                                                            init_val=init_val["css"],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[r][match],
                                                            prev_traded=prev_trade["css"], r=r,
                                                            is_buying=False, trading_price=trading_price,
                                                            block_length=block_length,
                                                            opti_bes_res_buyer=opti_bes_res_buyer,
                                                            opti_res_css=opti_res_css,
                                                            mar_agent_css=mar_agent_css)

            # replacing the initial opti results with opti regarding trading
            if buyer_id < options["nb_bes"]:
                opti_res[buyer_id] = opti_bes_negotiation.replace_opti_res(opti_res[buyer_id], opti_bes_res_buyer,
                                                                           par_rh, n_opt)
            elif buyer_id == options["nb_bes"]:  # if buyer is the central supply system
                opti_res_css = opti_css_negotiation.replace_opti_res_css(opti_res_css, opti_bes_res_buyer,
                                                                         par_rh, n_opt)
            if seller_id < options["nb_bes"]:
                opti_res[seller_id] = opti_bes_negotiation.replace_opti_res(opti_res[seller_id], opti_bes_res_seller,
                                                                            par_rh, n_opt)
            elif seller_id == options["nb_bes"]:  # if seller is the central supply system
                opti_res_css = opti_css_negotiation.replace_opti_res_css(opti_res_css, opti_bes_res_seller,
                                                                         par_rh, n_opt)

            # store the matched pairs
            matched_pairs.append([buyer_id, seller_id])

            # store the results of the negotiation for this match and this round
            neg_res[r][match], prev_trade = save_negotiation_results(neg_res[r][match], opti_bes_res_buyer,
                                                                     opti_bes_res_seller, trading_price, prev_trade,
                                                                     buyer_id, seller_id, block_bid_time_steps, params,
                                                                     options)
            #except:
            #    print(1111111111)
            #    pass

            # ---------- BIDS FOR NEXT ROUND ---------- #
            # if buyer and seller are not the central supply system
            if buyer_id < options["nb_bes"] and seller_id < options["nb_bes"]:
                buy_list_next_round, sell_list_next_round = \
                        block_bids.compute_block_bids_during_negotiation(matched_bids_info, r, match,
                                                                         neg_res[r][match]["remaining_demand"],
                                                                         block_bid_time_steps, nodes, block_length,
                                                                         buyer_id, opti_bes_res_buyer, opti_res,
                                                                         buy_list_next_round,
                                                                         neg_res[r][match]["remaining_supply"],
                                                                         seller_id, opti_bes_res_seller,
                                                                         sell_list_next_round, options)
            # if buyer or seller is the central supply system
            elif buyer_id == options["nb_bes"] or seller_id == options["nb_bes"]:
                buy_list_next_round, sell_list_next_round = \
                        block_bids.compute_block_bids_during_negotiation(matched_bids=matched_bids_info, r=r, match=match,
                                                                         remaining_demand=neg_res[r][match]["remaining_demand"],
                                                                         block_bid_time_steps=block_bid_time_steps,
                                                                         nodes=nodes, block_length=block_length,
                                                                         buyer_id=buyer_id, opti_bes_res_buyer=opti_bes_res_buyer,
                                                                         opti_res=opti_res,
                                                                         buy_list_next_round=buy_list_next_round,
                                                                         remaining_supply=neg_res[r][match]["remaining_supply"],
                                                                         seller_id=seller_id, opti_bes_res_seller=opti_bes_res_seller,
                                                                         sell_list_next_round=sell_list_next_round,
                                                                         options=options, opti_res_css=opti_res_css,
                                                                         mar_agent_css=mar_agent_css)

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
                                                 sell_list=sell_list_next_round, sorted_bids=sorted_bids, r=r,
                                                 par_rh=par_rh, n_opt=n_opt, block_length=block_length)

        # match all buyers and sellers for the next trading round
        if options["price_based_matching"]:
            matched_bids_info[r + 1] = matching_during_negotiation_price_check(sorted_bids[r + 1], matched_pairs,
                                                                               par_rh, n_opt, block_length)
        else:
            matched_bids_info[r + 1] = matching_during_negotiation(sorted_bids[r + 1], matched_pairs)

        # go to next negotiation trading round
        r += 1

    print("Finished all negotiations for time steps " + str(block_bid_time_steps[0]) + " to "
          + str(block_bid_time_steps[-1]) + ".")

    return (neg_res, sorted_bids,  matched_bids_info), opti_res, opti_res_css


def calculate_trading_price(par_rh, n_opt, block_length, matched_bids, r, match):
    # todo: delta_prices in abh. der Gebotsmengen und deren Differenzen
    bid_quantity_seller = {}
    bid_quantity_buyer = {}
    ratio = {}
    trading_price = {}
    # if buyer has more flex energy
    if matched_bids[r][match][0]["flex_energy"] >= matched_bids[r][match][1]["flex_energy"]:
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            bid_quantity_seller[t] = matched_bids[r][match][1][t][1]
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            try:
                ratio[t] = bid_quantity_seller[t] / max(bid_quantity_seller.values())
            except ZeroDivisionError:
                ratio[t] = 0
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            trading_price[t] = (min(matched_bids[r][match][1][t][0], matched_bids[r][match][0][t][0])
                                + (1 - ratio[t]) * (max(matched_bids[r][match][1][t][0],
                                                        matched_bids[r][match][0][t][0])
                                                    - min(matched_bids[r][match][1][t][0],
                                                          matched_bids[r][match][0][t][0])))

    # else if seller has more flex energy
    elif matched_bids[r][match][1]["flex_energy"] > matched_bids[r][match][0]["flex_energy"]:
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            bid_quantity_buyer[t] = matched_bids[r][match][0][t][1]
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            try:
                ratio[t] = bid_quantity_buyer[t] / max(bid_quantity_buyer.values())
            except ZeroDivisionError:
                ratio[t] = 0
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            trading_price[t] = max(matched_bids[r][match][1][t][0], matched_bids[r][match][0][t][0]) \
                              + (1 - ratio[t]) * (min(matched_bids[r][match][1][t][0],
                                                      matched_bids[r][match][0][t][0])
                                                  - max(matched_bids[r][match][1][t][0],
                                                        matched_bids[r][match][0][t][0]))

    return trading_price


def save_negotiation_results(neg_res, opti_bes_res_buyer, opti_bes_res_seller, trading_price, prev_trade,
                             buyer_id, seller_id, block_bid_time_steps, params, options):
    # ---------- RESULTS OF NEGOTIATION FOR THIS MATCH AND THIS ROUND ---------- #
    for t in block_bid_time_steps:

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
        if buyer_id < options["nb_bes"]:
            prev_trade[buyer_id]["buy"][t] += neg_res["trading_quantity"][t]  # buyer
        elif buyer_id == options["nb_bes"]: # if buyer is the central supply system
            prev_trade["css"]["buy"][t] += neg_res["trading_quantity"][t]
        if seller_id < options["nb_bes"]:
            prev_trade[seller_id]["sell"][t] += neg_res["trading_quantity"][t]  # seller
        elif seller_id == options["nb_bes"]:  # if seller is the central supply system
            prev_trade["css"]["sell"][t] += neg_res["trading_quantity"][t]

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
    already_matched = []
    not_possible_matches = []
    not_yet_matched = []
    if len(sorted_block_bids["buy_blocks"]) != 0 and len(sorted_block_bids["sell_blocks"]) != 0:
        if len(sorted_block_bids["buy_blocks"]) <= len(sorted_block_bids["sell_blocks"]):
            for b in range(len(sorted_block_bids["buy_blocks"])):
                # buyer = sorted_block_bids["buy_blocks"][b]
                # seller = sorted_block_bids["sell_blocks"][b]
                # buyer_price = buyer["mean_price"]
                # seller_price = seller["mean_price"]
                #
                # # Check if the buyer's price is >= seller's price before adding to possible matches
                # if buyer_price >= seller_price:
                #     if [buyer["bes_id"], seller["bes_id"]] not in matched_pairs:  # Check if the pair is already matched
                #         possible_matches.append([buyer["bes_id"], seller["bes_id"]])  # Add to possible matches
                #     else:  # If the pair is already matched, add to not possible matches
                #         not_possible_matches.append([buyer["bes_id"], seller["bes_id"]])
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
                    # buyer = sorted_block_bids["buy_blocks"][b]
                    # if buyer["bes_id"] == possible_matches[i][0]:
                    #     # Ensure buyer price >= seller price
                    #     for s in range(len(sorted_block_bids["sell_blocks"])):
                    #         seller = sorted_block_bids["sell_blocks"][s]
                    #         if seller["bes_id"] == possible_matches[i][1]:
                    #             if buyer["price"] >= seller["price"]:
                    #                 matched_bids_info[i] = [buyer, seller]
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
        # Convert matched_bids_info to a list of its values before returning
        matched_bids_info = list(matched_bids_info.values())
    else:
        matched_bids_info = []
        print("No matched bids for this optimization period.")

    return matched_bids_info


def matching_during_negotiation_price_check(sorted_block_bids, matched_pairs, par_rh, n_opt, block_length):
    """Match the sorted block bids of buyers to sellers based on the condition (seller price >= buyer price),
    with a rolling mechanism to try alternative buyer-seller combinations.
    If no valid matches are found, the buyers and sellers will be included in matched_bids_info as fallback.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

    # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st
    # sell bid, 2nd buy bid matches with 2nd sell bid, etc.)
    matched_bids_info = []
    unmatched_buyers = []
    unmatched_sellers = []

    # Extract buyers and sellers from sorted block bids
    buyers = sorted_block_bids.get("buy_blocks", [])
    sellers = sorted_block_bids.get("sell_blocks", [])

    # Create a copy of buyers and sellers to keep track of unmatched ones
    buyer_queue = buyers[:]
    seller_queue = sellers[:]

    # Process each seller by attempting to match them with buyers
    for seller in seller_queue[:]:  # Use a copy of the queue to allow mutations
        seller_price = seller["mean_price"]
        matched = False

        # Attempt to match with buyers in the buyer queue
        for _ in range(len(buyer_queue)):
            buyer = buyer_queue[0]  # Take the first buyer
            buyer_price = buyer["mean_price"]

            # Check the price condition for match
            if buyer_price >= seller_price and [buyer["bes_id"], seller["bes_id"]] not in matched_pairs\
                    and any(buyer[t][1] >= 0.01 and seller[t][1] >= 0.01 for t in buyer if t in seller):  #for t in par_rh["time_steps"][n_opt][0:block_length]):
                # Valid match
                matched_bids_info.append([buyer, seller])
                buyer_queue.pop(0)  # Remove matched buyer from the queue
                matched = True
                break  # Stop looking for buyers for this seller (once matched)
            else:
                # Rotate (move the buyer to the end of the queue)
                if [buyer["bes_id"], seller["bes_id"]] in matched_pairs:
                    buyer_queue.pop(0)
                else:
                    buyer_queue.append(buyer_queue.pop(0))

        # If no valid matches found for this seller, mark as unmatched
        # if not matched:
        #     unmatched_sellers.append(seller)

    # After processing sellers, handle remaining unmatched buyers
    # unmatched_buyers.extend(buyer_queue)

    # # If there are unmatched buyers and sellers, use fallback to pair them
    # while unmatched_sellers and unmatched_buyers:
    #     # Pair one unmatched buyer with one unmatched seller
    #     matched_bids_info.append([unmatched_buyers.pop(0), unmatched_sellers.pop(0)])

    # # If there are still unmatched buyers (no sellers left), add them with None
    # for unmatched_buyer in unmatched_buyers:
    #     matched_bids_info.append([unmatched_buyer, None])
    #
    # # If there are still unmatched sellers (no buyers left), add them with None
    # for unmatched_seller in unmatched_sellers:
    #     matched_bids_info.append([None, unmatched_seller])

    # # If there are unmatched buyers and sellers, use fallback to pair them
    # for unmatched_buyer in unmatched_buyers:
    #     if unmatched_sellers:
    #         # Pair each unmatched buyer with an unmatched seller
    #         matched_bids_info.append([unmatched_buyer, unmatched_sellers.pop(0)])
    #     else:
    #         # If no unmatched sellers are left, still include buyer as unmatched
    #         matched_bids_info.append([unmatched_buyer, None])
    #
    # # Add remaining unmatched sellers (if any) paired with None
    # for unmatched_seller in unmatched_sellers:
    #     matched_bids_info.append([None, unmatched_seller])

    # Return the final matched bids info
    return matched_bids_info


def negotiation_with_css():
    pass


def trade_with_grid(params, par_rh, n_opt, block_length, opti_res, options, opti_res_css: dict = None):

    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    nb_bes = len(opti_res)
    #if options["central_supply_system"]:
    #    nb_agents += 1

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

    if options["central_supply_system"]:
        power_from_grid[nb_bes] = {}
        power_to_grid[nb_bes] = {}
        costs_power_from_grid[nb_bes] = {}
        revenue_power_to_grid[nb_bes] = {}
        for t in time_steps:
            # --------------------- CSS AS BUYER IMPORTS FROM GRID ---------------------
            if opti_res_css["res_p_grid_buy"] != {}:
                power_from_grid[nb_bes][t] = opti_res_css["res_p_grid_buy"][t]
                costs_power_from_grid[nb_bes][t] = opti_res_css["res_p_grid_buy"][t]/1000 * params["eco"]["pr", "el"]
            # --------------------- CSS AS SELLER INJECTS INTO GRID ---------------------
            if opti_res_css["res_p_grid_sell"] != {}:
                power_to_grid[nb_bes][t] = opti_res_css["res_p_grid_sell"][t]
                revenue_power_to_grid[nb_bes][t] = opti_res_css["res_p_grid_sell"][t]/1000 * params["eco"]["sell" + "_" + "pv"]
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
