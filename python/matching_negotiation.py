import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import python.market_preprocessing as mar_pre

def matching (block_bids):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched peer tuples."""

   # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st sell bid,
   # 2nd buy bid matches with 2nd sell bid, etc.)
    if len(block_bids["buy_blocks"]) != 0 and len(block_bids["sell_blocks"]) != 0:
       matched_bids_info = list(zip(block_bids["buy_blocks"], block_bids["sell_blocks"]))

    else:
       matched_bids_info = []
       print("No matched bids for this optimization period.")

    return matched_bids_info









   #matched_peers_info = {
    #   "buyer": {},
    #   "seller": {}
    #}

   #return matched_peers_info


#def negotiation(options):


