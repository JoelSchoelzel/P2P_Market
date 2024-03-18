import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import python.market_preprocessing as mar_pre

from python import opti_bes_negotiation
import copy


def matching(sorted_block_bids, n_opt):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

   # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st sell bid,
   # 2nd buy bid matches with 2nd sell bid, etc.)

    if len(sorted_block_bids["buy_blocks"]) != 0 and len(sorted_block_bids["sell_blocks"]) != 0:
       matched_bids_info = list(zip(sorted_block_bids["buy_blocks"], sorted_block_bids["sell_blocks"]))

    else:
       matched_bids_info = []


       print("No matched bids for this optimization period.")

    return matched_bids_info



def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, sorted_bids, block_length):

    """Run the optimization problem for the negotiation phase (taking into account
    bid quantities and prices of matched peer).

    Returns:
        nego_transactions (dict): Dictionary containing the results of the negotiation phase for each match.
        total_market_info (dict): Dictionary containing the results of the total market (all matched and unmatched peers).
        last_time_step (int): Last time step of the optimization horizon."""

    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    last_time_step = time_steps[-1]

    # initialize all necessary variables
    trade_power = {}
    trade_price = {}
    average_bids_price = {}
    buyer_trade_price = {}
    seller_trade_price = {}
    buyer_diff_to_average = {}
    seller_diff_to_average = {}
    power_from_grid = {}
    power_to_grid = {}
    remaining_demand = {}
    remaining_supply = {}
    saved_costs = {}
    additional_revenue = {}
    opti_bes_res_buyer = {}
    opti_bes_res_seller = {}
    delta_price = 0
    trade_price_sum = 0
    total_average_trade_price = 0
    total_trade_cost_sum = 0


    ### CALCULATE SUPPLY & DEMAND COVER FACTOR FOR EACH TIME STEP BEFORE TRADING
    total_demand = {}
    total_supply = {}
    supply_cover_factor = {}
    demand_cover_factor = {}

    for t in time_steps:
        total_demand[t] = 0  # Initialize total_demand for time step t
        total_supply[t] = 0  # Initialize total_supply for time step t

        # Calculate total demand for time step t
        for buyer_block in sorted_bids["buy_blocks"]:
            if t in buyer_block:  # Check if time step t exists in the buyer_block
                total_demand[t] += buyer_block[t][1]  # Add the quantity for time step t

        # Calculate total supply for time step t
        for seller_block in sorted_bids["sell_blocks"]:
            if t in seller_block:  # Check if time step t exists in the seller_block
                total_supply[t] += seller_block[t][1]  # Add the quantity for time step t

        # Calculate SCF and DCF before trading for time step t
        if total_supply[t] > 0:  # Ensure there's no division by zero
            supply_cover_factor[t] = min(total_supply[t], total_demand[t]) / total_supply[t]
        else:
            supply_cover_factor[t] = 0
        if total_demand[t] > 0:
            demand_cover_factor[t] = min(total_supply[t], total_demand[t]) / total_demand[t]
        else:
            demand_cover_factor[t] = 0


    # --------------------- START NEGOTIATION ---------------------

    # Multiple rounds of trading
    r = 0
    max_rounds = 1000
    sorted_bids_nego = {r: sorted_bids}
    matched_bids_info = {r: matched_bids_info}
    nego_transactions = {r: {}}
    # Initialize a set to keep track of buildings that participated in negotiations
    participating_buildings = set()


    # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
    while len(sorted_bids_nego[r]["sell_blocks"]) > 0 and len(sorted_bids_nego[r]["buy_blocks"]) > 0 and r < max_rounds:

        # create dicts for next trading round
        sorted_bids_nego[r + 1] = {"buy_blocks": [], "sell_blocks": []}
        matched_bids_info[r + 1] = []
        nego_transactions[r + 1] = {}

        # buyer and seller of each match run their optimization model until their price_trade difference to
        # average price is less than 0.005
        for match in range(len(matched_bids_info[r])):
            nego_transactions[r][match] = {}
            add_buy_bid = False
            add_sell_bid = False

            for t in time_steps:
                # initialize variables
                trade_power[t] = {}
                average_bids_price[t] = {}
                buyer_trade_price[t] = {}
                seller_trade_price[t] = {}
                buyer_diff_to_average[t] = float('inf')
                seller_diff_to_average[t] = float('inf')
                buyer_id = matched_bids_info[r][match][0]["bes_id"]
                seller_id = matched_bids_info[r][match][1]["bes_id"]
                participating_buildings.add(buyer_id)
                participating_buildings.add(seller_id)
                saved_costs[t] = 0
                additional_revenue[t] = 0
                saved_costs_sum = 0
                additional_rev_sum = 0


                # run the optimization model for buyer and seller
                while buyer_diff_to_average[t] > 0.005 and seller_diff_to_average[t] > 0.005:

                    opti_bes_res_buyer \
                            = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                                                init_val=init_val["building_" + str(buyer_id)],
                                                                n_opt=n_opt, options=options,
                                                                matched_bids_info=matched_bids_info[r][match],
                                                                is_buying=True,
                                                                delta_price=delta_price, block_length=block_length)
                    opti_bes_res_seller \
                            = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                                init_val=init_val["building_" + str(seller_id)],
                                                                n_opt=n_opt, options=options,
                                                                matched_bids_info=matched_bids_info[r][match],
                                                                is_buying=False,
                                                                delta_price=delta_price, block_length=block_length)

                    # compare trade price of buyer and seller (resulting from opti) with average price of initial bids
                    average_bids_price[t] = opti_bes_res_buyer["average_bids_price"][t]
                    buyer_trade_price[t] = opti_bes_res_buyer["res_price_trade"][t]
                    seller_trade_price[t] = opti_bes_res_seller["res_price_trade"][t]
                    buyer_diff_to_average[t] = abs(buyer_trade_price[t] - average_bids_price[t])
                    seller_diff_to_average[t] = abs(seller_trade_price[t] - average_bids_price[t])

                    # update delta price
                    delta_price += 0.005


                ## RESULTS OF NEGOTIATION FOR THIS MATCH AND THIS ROUND

                # Set trade power and trade price of this match
                trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t], opti_bes_res_seller["res_power_trade"][t])
                trade_price[t] = (buyer_trade_price[t] + seller_trade_price[t]) / 2
                trade_price_sum += trade_price[t]

                # calculate the saved costs for this match compared to trading with grid
                saved_costs[t] = trade_power[t] * (params["eco"]["pr", "el"] - trade_price[t])
                saved_costs_sum += saved_costs[t]

                # calculate the additional revenue for this match compared to trading with grid
                if opti_bes_res_seller["res_p_sell"]["chp"][t] > 1e-4:
                    additional_revenue[t] = trade_power[t] * (trade_price[t] - params["eco"]["sell" + "_" + "chp"])
                elif opti_bes_res_seller["res_p_sell"]["pv"][t] > 1e-4:
                    additional_revenue[t] = trade_power[t] * (trade_price[t] - params["eco"]["sell" + "_" + "pv"])
                additional_rev_sum += additional_revenue[t]

                # calculate demand & supply that haven't been fulfilled
                remaining_demand[t] = abs(matched_bids_info[r][match][0][t][1] - trade_power[t])
                remaining_supply[t] = abs(matched_bids_info[r][match][1][t][1] - trade_power[t])

                if remaining_demand[t] > 0 and not add_buy_bid:
                    add_buy_bid = True

                if remaining_supply[t] > 0 and not add_sell_bid:
                    add_sell_bid = True

            # add unsatisfied buyers and sellers to next trading round with remaining demand/supply
            # if remaining_demand[t] > 0:
            if add_buy_bid:
                copy_of_buy_bid = copy.deepcopy(matched_bids_info[r][match][0])
                sorted_bids_nego[r + 1]["buy_blocks"].append(copy_of_buy_bid)
                position_b = len(sorted_bids_nego[r + 1]["buy_blocks"]) - 1  # position of the new buy block in the list
                for t in time_steps:
                    sorted_bids_nego[r + 1]["buy_blocks"][position_b][t][1] = remaining_demand[t]

            #if remaining_supply[t] > 0:
            if add_sell_bid:
                copy_of_sell_bid = copy.deepcopy(matched_bids_info[r][match][1])
                sorted_bids_nego[r + 1]["sell_blocks"].append(copy_of_sell_bid)
                position_s = len(sorted_bids_nego[r + 1]["sell_blocks"]) - 1  # position of the new sell block in the list
                for t in time_steps:
                    sorted_bids_nego[r + 1]["sell_blocks"][position_s][t][1] = remaining_supply[t]


            # store the results of the negotiation for this match and this round
            nego_transactions[r][match] = {
                "buyer": matched_bids_info[r][match][0]["bes_id"],
                "seller": matched_bids_info[r][match][1]["bes_id"],
                "price": trade_price,
                "quantity": trade_power,
                "saved_costs": saved_costs,
                "additional_revenue": additional_revenue,
                "remaining_demand": remaining_demand,
                "remaining_supply": remaining_supply,
                "opti_bes_res_buyer": opti_bes_res_buyer,
                "opti_bes_res_seller": opti_bes_res_seller,
                "average_trade_price": trade_price_sum / len(time_steps)
            }


        # Add all buyers/sellers that weren't matched (but were in sorted bids list) to the new sorted_bids_nego lists
        if len(sorted_bids_nego[r]["buy_blocks"]) > len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining buy blocks
            remaining_buy_blocks = sorted_bids_nego[r]["buy_blocks"][len(sorted_bids_nego[r]["sell_blocks"]):]
            for buy_block in remaining_buy_blocks:
                sorted_bids_nego[r + 1]["buy_blocks"].append(buy_block)

        elif len(sorted_bids_nego[r]["buy_blocks"]) < len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining sell blocks
            remaining_sell_blocks = sorted_bids_nego[r]["sell_blocks"][len(sorted_bids_nego[r]["buy_blocks"]):]
            for sell_block in remaining_sell_blocks:
                sorted_bids_nego[r + 1]["sell_blocks"].append(sell_block)

        # TODO:     1. recalculate mean matching criteria
        #           2. resort the new sorted_bids_nego lists according to criteria before matching

        # match all buyers and sellers for the next trading round
        matched_bids_info[r + 1] = matching(sorted_bids_nego[r + 1], n_opt)

        # go to next negotiation trading round
        r += 1

    return nego_transactions, participating_buildings, sorted_bids_nego, last_time_step #total_market_info


def trade_with_grid(nego_transactions, sorted_bids, sorted_bids_nego, participating_buildings, params, par_rh, n_opt, block_length):

    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    nb_bes = len(sorted_bids["buy_blocks"]+sorted_bids["sell_blocks"])

    # if no negotiation can occur (seller or buyer list empty), all buyers/sellers trade with grid
    total_traded_volume = {}
    total_power_to_grid = {}
    total_power_from_grid = {}
    power_from_grid = {}
    power_to_grid = {}
    costs_power_from_grid = {}
    costs_power_to_grid = {}
    for bes_id in range(nb_bes):
        power_from_grid[bes_id] = {}
        power_to_grid[bes_id] = {}
        costs_power_from_grid[bes_id] = {}
        costs_power_to_grid[bes_id] = {}


    for buyer in sorted_bids["buy_blocks"]:
        buyer_id = buyer["bes_id"]

        # if buyer didn't participate in negotiation, his initial bid quantity is traded with the grid
        if buyer_id not in participating_buildings:
            for t in time_steps:
                power_from_grid[buyer_id][t] = buyer[t][1]
                costs_power_from_grid[buyer_id][t] = buyer[t][1] * params["eco"]["pr", "el"]

        # if buyer participated in negotiation, his remaining demand (after last negotiation round and match) is
        # traded with grid
        else:
            last_round = max(sorted_bids_nego.keys())
            remaining_demand = {}
            # Iterate backwards to find the last occurrence of the bes_id
            for round_num in sorted(sorted_bids_nego.keys(), reverse=True):
                buyer_found = False
                for buy_bid in sorted_bids_nego[round_num]["buy_blocks"]:
                    if buy_bid.get("bes_id") == buyer_id:
                        for t in buy_bid:
                            if isinstance(t, int):  # Ensure it's a time step key
                                remaining_demand[t] = buy_bid[t][1]
                        buyer_found = True
                        break
                if buyer_found:
                    break  # Stop searching through rounds once the bes_id is found

            for t in time_steps:
                power_from_grid[buyer_id][t] = remaining_demand[t]
                costs_power_from_grid[buyer_id][t] = remaining_demand[t] * params["eco"]["pr", "el"]
        """else:
            last_remaining_demand = None
            # Iterate through each trading round
            for negotiation_round, round_value in nego_transactions.items():
                # Iterate through each match within the trading round
                for match_key, match_value in round_value.items():
                    # Check if the current match contains the buyer
                    if match_value.get("buyer") == buyer_id:
                        # Update the last remaining demand found for the buyer
                        last_remaining_demand = match_value['remaining_demand']

            # If the last remaining demand is not None, trade the remaining demand with the grid
            if last_remaining_demand is not None:
                for t in time_steps:
                    power_from_grid[t] = last_remaining_demand[t]
                    costs_power_from_grid[t] = power_from_grid[buyer_id][t] * params["eco"]["pr", "el"]
            # If remaining demand is None, trade the remaining demand in last round of sorted_bids_nego[r]["buy_blocks"]
            # with the grid"""


    # if seller didn't participate in negotiation, his initial bid quantity is traded with the grid
    # if a seller participated in negotiation, his remaining supply is traded with the grid
    for seller in sorted_bids["sell_blocks"]:
        seller_id = seller["bes_id"]
        if seller_id not in participating_buildings:
            for t in time_steps:
                power_from_grid[seller_id][t] = seller[t][1]
                costs_power_to_grid[seller_id][t] = seller[t][1] * params["eco"]["pr", "el"]
        # TODO: trade the remaining supply after last negotiation round in which seller occurs with the grid
        else:
            for t in time_steps:
                power_from_grid[seller_id][t] = nego_transactions[r][match]["remaining_demand"][t]
                costs_power_from_grid[seller_id][t] = 0
    # Trade the initial bid quantity with the grid








    """for building in nodes:
        power_to_grid = {building: {}}
        power_from_grid = {building: {}}


    # only buyers remaining
    if len(sorted_bids["sell_blocks"]) == 0:
        for buyer in sorted_bids_nego[r]["buy_blocks"]:
            for bes_id in buyer["bes_id"]:
                for t in time_steps:
                    power_to_grid[bes_id][t] = buyer[t][1]
                    total_power_to_grid[bes_id][t] = total_demand
                    total_power_from_grid[t] = 0
                    total_traded_volume[t] = 0

    # only sellers remaining
    if len(sorted_bids["buy_blocks"]) == 0:
        for t in time_steps:
            power_from_grid[t] = total_demand
            total_power_to_grid[t] = 0
            total_traded_volume[t] = 0"""

    #TODO: trade ignored demand of sellers with grid


    ### STORE THE RESULTS OF THE TOTAL MARKET

    total_market_info = {
        "supply_cover_factor": supply_cover_factor,
        "demand_cover_factor": demand_cover_factor,
        "market_based_scf": 0,
        "market_based_dcf": 0,
        "total_traded_volume": total_traded_volume,
        "total_average_trade_price": total_average_trade_price,
        "total_saved_costs": 0,
        "total_additional_revenue": 0,
        "total_economic_gain": 0,
        "total_power_to_grid": total_power_to_grid,
        "total_power_from_grid": total_power_from_grid,
        "total_trade_cost_sum": total_trade_cost_sum,
        "soc_last_time_step": 0
    }

    print("Finished all negotiations for time steps " + str(time_steps[0]) + " to " + str(time_steps[-1]) + ".")

    return total_market_info







