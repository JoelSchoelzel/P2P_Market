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

    opti_nego_res = opti_bes_negotiation.compute_opti(node, params, par_rh, building_param, init_val, n_opt, options, matched_bids_info, block_bid)

    return opti_nego_res



