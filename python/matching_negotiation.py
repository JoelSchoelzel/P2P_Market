import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import python.market_preprocessing as mar_pre

from python import opti_bes_negotiation


def matching (block_bids, n_opt):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a list [price, quantity, buying:True/False, building_id]"""

   # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st sell bid,
   # 2nd buy bid matches with 2nd sell bid, etc.)
    if len(block_bids["buy_blocks"]) != 0 and len(block_bids["sell_blocks"]) != 0:
       matched_bids_info = list(zip(block_bids["buy_blocks"], block_bids["sell_blocks"]))

    else:
       matched_bids_info = []
       print("No matched bids for this optimization period.")


    return matched_bids_info



def negotiation(node, params, par_rh, building_param, init_val, n_opt, options, matched_bids_info, block_bid):

    """Run the optimization problem for the negotiation phase (taking into account
    quantities and prices of matched peer."""


    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    bes_0 = block_bid["bes_0"]
    # List of known non-time-step keys
    non_time_step_keys = ["bes_id", "mean_price", "sum_energy", "total_price", "mean_quantity", "mean_energy_forced", "mean_energy_delayed"]
    # Count keys that are integers (time steps t) and not in the list of known non-time-step keys
    block_length = sum(1 for key in bes_0 if str(key).isdigit() and key not in non_time_step_keys)
    time_steps = par_rh["time_steps"][n_opt][0:block_length]

    # Create all necessary dictionaries to store the results of the negotiation
    transactions = {}
    #buyer_diff_to_average = {}
    #seller_diff_to_average = {}
    delta_price = 0

    trade_power = {}
    trade_power_sum = 0
    trade_price = {}
    trade_price_sum = 0

    large_number = float('inf')  # This represents infinity, which is effectively a very large number
    average_trade_price = {}
    buyer_trade_price = {}
    seller_trade_price = {}
    buyer_diff_to_average = {}
    seller_diff_to_average = {}


    sup_total = 0
    dem_total = 0
    total_trade_price = 0
    total_average_trade_price = 0
    trade_cost_sum = 0
    total_trade_cost_sum = 0
    average_trade_price_sum = 0

    for match in range(len(matched_bids_info)):
        for t in time_steps:
            sup_total += matched_bids_info[match][1][t][1]
            dem_total += matched_bids_info[match][0][t][1]

    # buyer and seller of each match run their optimization model until their price_trade difference to average price
    # is less than 0.05
    for match in range(len(matched_bids_info)):
        for t in time_steps:
            trade_power[t] = {}
            average_trade_price[t] = {}
            buyer_trade_price[t] = {}
            seller_trade_price[t] = {}
            buyer_diff_to_average[t] = large_number
            seller_diff_to_average[t] = large_number
            while buyer_diff_to_average[t] > 0.05 and seller_diff_to_average[t] > 0.05:
                opti_bes_res_buyer = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                                       n_opt, options, matched_bids_info[match],
                                                                       block_bid, is_buying=True, delta_price=delta_price)
                opti_bes_res_seller = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                                        n_opt, options, matched_bids_info[match],
                                                                        block_bid, is_buying=False, delta_price=delta_price)


                average_trade_price[t] = opti_bes_res_buyer["average_trade_price"][t]
                buyer_trade_price[t] = opti_bes_res_buyer["res_price_trade"][t]
                seller_trade_price[t] = opti_bes_res_seller["res_price_trade"][t]
                buyer_diff_to_average[t] = abs(buyer_trade_price[t]- average_trade_price[t]) # opti_bes_res_buyer["res_price_trade"][t]
                seller_diff_to_average[t] = abs(seller_trade_price[t] - average_trade_price[t])

                trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t], opti_bes_res_seller["res_power_trade"][t])
                trade_price[t] = (buyer_trade_price[t] + seller_trade_price[t]) / 2

                trade_power_sum += trade_power[t]
                trade_cost_sum += trade_price[t]*trade_power[t]
                trade_price_sum += trade_price[t]
                delta_price += 0.05

            """trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t], opti_bes_res_seller["res_power_trade"][t])
            trade_price[t] = (buyer_trade_price[t] + seller_trade_price[t]) / 2


        # quantity is minimum of both
        transaction_quantity = min(bids[n]["sell"][prio]["quantity"], bids[n]["buy"][prio]["quantity"])

        # add transaction to the dict to keep record
        transactions[count_trans] = {
            "buyer": bids[n]["buy"][prio]["building"],
            "seller": bids[n]["sell"][prio]["building"],
            "price": transaction_price,
            "quantity": transaction_quantity,
            "trading_round": (n + 1)
        }"""


        transactions[match] = {
                "buyer": matched_bids_info[match][0]["bes_id"],
                "seller": matched_bids_info[match][1]["bes_id"],
                "price": trade_price,
                "quantity": trade_power,
                "trade_power_sum": trade_power_sum,
                "average_trade_price": trade_price_sum/len(time_steps)
        }

        sup_total = 0
        for matches in transactions:
            sup_total += 1
            total_trade_cost_sum += transactions[matches]["trade_cost_sum"]
            average_trade_price_sum += transactions[matches]["average_trade_price"]

        total_average_trade_price = average_trade_price_sum / sup_total


    total_market_info = {
        "total_trade_cost_sum": total_trade_cost_sum,
        "total_average_trade_price": total_average_trade_price,
        "sup_total": sup_total,
        "dem_total": dem_total
    }
    return transactions, total_market_info







