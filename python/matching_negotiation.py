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

    # Run the optimization until trading price of both peers converges to the average of
    # buying/selling price (with a certain tolerance)

    opti_bes_res = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val, n_opt, options, matched_bids_info, block_bid)
    # current_price_trade = {}

    # rerun the optimization model so that the price_trade iteratively converges to the average of the buying/selling price

    # Create list of time steps per optimization horizon (dt --> hourly resolution)
    bes_0 = block_bid["bes_0"]
    # List of known non-time-step keys
    non_time_step_keys = ["bes_id", "mean_price", "sum_energy", "total_price", "mean_quantity", "mean_energy_forced", "mean_energy_delayed"]
    # Count keys that are integers (time steps t) and not in the list of known non-time-step keys
    block_length = sum(1 for key in bes_0 if str(key).isdigit() and key not in non_time_step_keys)
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    iteration = 0
    max_iterations = 10

    for t in time_steps:
        while abs(opti_bes_res["price_trade"][t] - (opti_bes_res["price_buyer"][t] + opti_bes_res["price_seller"][t]) / 2) > 0.01 and iteration < max_iterations:
            iteration += 1
            opti_bes_res = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val, n_opt, options, matched_bids_info, block_bid)

    final_price_trade = opti_bes_res["res_price_trade"]
    final_power_trade = opti_bes_res["res_power_trade"]

    opti_nego_res = (final_price_trade, final_power_trade)

    return opti_nego_res



