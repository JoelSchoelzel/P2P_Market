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

    # Create a dictionary to store the results of the negotiation
    negotiation_res = {}
    all_matches = len(matched_bids_info)


    # buyer and seller of each match run their optimization model
    for match in range(all_matches):
        opti_bes_res_buyer = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                               n_opt, options, matched_bids_info[match],
                                                               block_bid, is_buying=True)
        opti_bes_res_seller = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                                n_opt, options, matched_bids_info[match],
                                                                block_bid, is_buying=False)

        current_price_trade_buyer = opti_bes_res_buyer["res_price_trade"]
        current_price_trade_seller = opti_bes_res_seller["res_price_trade"]


    # rerun the optimization for matched buyer and seller until price_trade difference of buyer and seller
    # is less than 0.05 or the maximum iteration is reached
    """for match in range(len(matched_bids_info)):
        price_bid_buyer = {}
        price_bid_buyer[match] = {}
        price_bid_seller = {}
        price_bid_seller[match] = {}
        price_difference = {}
        for t in time_steps:
            price_bid_buyer[match][t] = matched_bids_info[0][0][t][0]
            price_bid_seller[t] = matched_bids_info[0][1][t][0]
            price_difference[t] = abs(price_bid_buyer[t]-price_bid_seller[t])
            iteration = 0
            max_iteration = 10
            while price_difference[t] > 0.05 and iteration < max_iteration:
                opti_bes_res_buyer = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                                       n_opt, options, matched_bids_info[match],
                                                                       block_bid, is_buying=True)
                opti_bes_res_seller = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val,
                                                                        n_opt, options, matched_bids_info[match],
                                                                        block_bid, is_buying=False)

                # store new quantities and prices of buyer and seller optimization results
                buyer = {}
                buyer[t] = (opti_bes_res_buyer["res_price_trade"][t], opti_bes_res_buyer["res_power_trade"][t])
                seller = {}
                seller[t] = (opti_bes_res_seller["res_price_trade"][t], opti_bes_res_seller["res_power_trade"][t])
                matched_bids_info[match] = (buyer, seller)

                # update the price difference and iteration step
                price_difference = abs(opti_bes_res_buyer["res_price_trade"][t] - opti_bes_res_seller["res_price_trade"][t])
                iteration += 1"""

    negotiation_res[match] = {
            "buyer": opti_bes_res_buyer,
            "seller": opti_bes_res_seller
    }



    return negotiation_res



