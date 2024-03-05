import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import python.market_preprocessing as mar_pre

from python import opti_bes_negotiation


def matching (block_bids, n_opt):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

   # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st sell bid,
   # 2nd buy bid matches with 2nd sell bid, etc.)

    unmatched_blocks = []
    if len(block_bids["buy_blocks"]) != 0 and len(block_bids["sell_blocks"]) != 0:
       matched_bids_info = list(zip(block_bids["buy_blocks"], block_bids["sell_blocks"]))

       # Calculate the number of matched bids
      # num_matched_bids = len(matched_bids_info)

       # Create lists of unmatched buy and sell blocks
       #unmatched_buy_blocks = block_bids["buy_blocks"][num_matched_bids:] if len(
       #    block_bids["buy_blocks"]) > num_matched_bids else []
       #unmatched_sell_blocks = block_bids["sell_blocks"][num_matched_bids:] if len(
       #    block_bids["sell_blocks"]) > num_matched_bids else []
       #unmatched_blocks = unmatched_buy_blocks + unmatched_sell_blocks

    else:
       matched_bids_info = []
       print("No matched bids for this optimization period.")


    return matched_bids_info #, unmatched_blocks



def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, block_bids, block_length):

    """Run the optimization problem for the negotiation phase (taking into account
    bid quantities and prices of matched peer).

    Returns:
        nego_transactions (dict): Dictionary containing the results of the negotiation phase for each match.
        total_market_info (dict): Dictionary containing the results of the total market (all matches).
        last_time_step (int): Last time step of the optimization horizon."""

    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    last_time_step = time_steps[-1]

    # Create all necessary dictionaries to store the results of the negotiation
    nego_transactions = {}

    # initialize all necessary variables
    delta_price = 0
    trade_power = {}
    trade_power_sum = 0
    trade_price = {}
    trade_price_sum = 0
    average_bids_price = {}
    buyer_trade_price = {}
    seller_trade_price = {}
    buyer_diff_to_average = {}
    seller_diff_to_average = {}
    power_from_grid = {}
    power_to_grid = {}
    power_from_grid_sum = 0
    power_to_grid_sum = 0


    total_sup_matched = 0
    total_dem_matched = 0
    total_average_trade_price = 0
    trade_cost_sum = 0
    total_trade_cost_sum = 0
    average_trade_price_sum = 0
    total_traded_volume = 0
    total_power_to_grid = 0
    total_power_from_grid = 0
    saved_costs = {}
    additional_revenue = {}


    for match in range(len(matched_bids_info)):
        for t in time_steps:
            total_dem_matched += matched_bids_info[match][0][t][1]
            total_sup_matched += matched_bids_info[match][1][t][1]


    # buyer and seller of each match run their optimization model until their price_trade difference to average price
    # is less than 0.05
    for match in range(len(matched_bids_info)):
        for t in time_steps:
            trade_power[t] = {}
            average_bids_price[t] = {}
            buyer_trade_price[t] = {}
            seller_trade_price[t] = {}
            buyer_diff_to_average[t] = float('inf')
            seller_diff_to_average[t] = float('inf')
            buyer_id = matched_bids_info[match][0]["bes_id"]
            seller_id = matched_bids_info[match][1]["bes_id"]
            saved_costs[t] = {}
            additional_revenue[t] = {}
            saved_costs_sum = 0
            additional_rev_sum = 0

            while buyer_diff_to_average[t] > 0.005 and seller_diff_to_average[t] > 0.005:

                opti_bes_res_buyer \
                        = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(buyer_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[match], is_buying=True,
                                                            delta_price=delta_price, block_length=block_length)
                opti_bes_res_seller \
                        = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                            init_val=init_val["building_" + str(seller_id)],
                                                            n_opt=n_opt, options=options,
                                                            matched_bids_info=matched_bids_info[match], is_buying=False,
                                                            delta_price=delta_price, block_length=block_length)



                # compare trade price of buyer and seller (resulting from opti) with average price of initial bids
                average_bids_price[t] = opti_bes_res_buyer["average_bids_price"][t]
                buyer_trade_price[t] = opti_bes_res_buyer["res_price_trade"][t]
                seller_trade_price[t] = opti_bes_res_seller["res_price_trade"][t]
                buyer_diff_to_average[t] = abs(buyer_trade_price[t] - average_bids_price[t]) # opti_bes_res_buyer["res_price_trade"][t]
                seller_diff_to_average[t] = abs(seller_trade_price[t] - average_bids_price[t])

                # update delta price
                delta_price += 0.005

                # if difference is less than 0.005, trade power and trade price of this match are set
                trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t], opti_bes_res_seller["res_power_trade"][t])
                trade_price[t] = (buyer_trade_price[t] + seller_trade_price[t]) / 2


                ## Calculate results of transaction for this match and all time steps within block bid
                # calculate sum of traded power and trade price for this match
                trade_power_sum += trade_power[t]
                if trade_power_sum > 0:
                    trade_cost_sum += trade_price[t]*trade_power[t]
                    trade_price_sum += trade_price[t]
                else:
                    trade_cost_sum += trade_price[t]*trade_power[t]
                    trade_price_sum += 0

                # calculate power that has to be imported/sold to/from the grid
                power_from_grid[t] = abs(matched_bids_info[match][0][t][1] - trade_power[t])
                power_to_grid[t] = abs(matched_bids_info[match][1][t][1] - trade_power[t])

                # calculate sum of power that has to be imported/sold to/from the grid for this match
                power_from_grid_sum += power_from_grid[t]
                power_to_grid_sum += power_to_grid[t]

                # calculate the additional revenue and saved costs for this match compared to trading with grid
                saved_costs[t] = trade_power[t] * (params["eco"]["pr", "el"] - trade_price[t])

                #TODO: add additional revenue for the sellers in comparison to selling to the grid
                if opti_bes_res_seller["res_rev"]["chp"][t] > 0:
                    additional_revenue[t] = trade_power[t] * (trade_price[t] - params["eco"]["sell" + "_" + "chp"])
                elif opti_bes_res_seller["res_rev"]["pv"][t] > 0:
                    additional_revenue[t] = trade_power[t] * (trade_price[t] - params["eco"]["sell" + "_" + "pv"])

                additional_rev_sum += additional_revenue[t]
                saved_costs_sum += saved_costs[t]



        # store the results of the transaction for this match and all time steps within block bid
        nego_transactions[match] = {
                "buyer": matched_bids_info[match][0]["bes_id"],
                "seller": matched_bids_info[match][1]["bes_id"],
                "price": trade_price,
                "quantity": trade_power,
                "trade_power_sum": trade_power_sum,
                "trade_cost_sum": trade_cost_sum,
                "power_to_grid": power_to_grid_sum,
                "power_from_grid": power_from_grid_sum,
                "average_trade_price": trade_price_sum/len(time_steps),
                "saved_costs": saved_costs_sum,
                "additional_revenue": additional_rev_sum,
                "opti_bes_res_buyer": opti_bes_res_buyer,
                "opti_bes_res_seller": opti_bes_res_seller
        }

        # calculate the total results of all matches
        count = 0
        for matches in nego_transactions:
            count += 1
            total_trade_cost_sum += nego_transactions[matches]["trade_cost_sum"]
            average_trade_price_sum += nego_transactions[matches]["average_trade_price"]
            total_traded_volume += nego_transactions[matches]["trade_power_sum"]
            total_power_to_grid += nego_transactions[matches]["power_to_grid"]
            total_power_from_grid += nego_transactions[matches]["power_from_grid"]

        total_average_trade_price = average_trade_price_sum / count

    total_demand = {}
    total_supply = {}
    supply_cover_factor = {}
    demand_cover_factor = {}

    for t in time_steps:
        for buyer in block_bids["buy_blocks"]:
            total_demand[t] = block_bids["buy_blocks"][buyer][t][1]
        for seller in block_bids["sell_blocks"]:
            total_supply[t] = block_bids["sell_blocks"][seller][t][1]

        supply_cover_factor[t] = total_traded_volume[t] / total_supply[t]
        demand_cover_factor[t] = total_traded_volume[t] / total_demand[t]



    # TODO: add unmatched buyers/sellers to the total_market_info
    # store the results of the total market (all matches)
    total_market_info = {
        "total_trade_cost_sum": total_trade_cost_sum,
        "total_average_trade_price": total_average_trade_price,
        "total_traded_volume": total_traded_volume,
        "total_power_to_grid": total_power_to_grid,
        "total_power_from_grid": total_power_from_grid,
        "total_sup_matched": total_sup_matched, #here the supply of unmatched sellers is missing
        "total_dem_matched": total_dem_matched, #here the demand of unmatched buyers is missing
        "power_from_grid_unmatched": 0,
        "power_to_grid_unmatched": 0
    }
    return nego_transactions, total_market_info, last_time_step







