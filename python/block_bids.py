## Block bid class which contains the logic to compute block bids for each BES
##


class BlockBid(object):
    ""
    def __init__(self, id, bids):
        self.id = id
        self.bids = {}

    def add_bid(self, timestep, bid_result):
        self.bids[timestep] = bid_result

    def get_block_bid(self, start_timestep):
        block_bid = {}
        for t in range(start_timestep, start_timestep + 4):
            if t in self.bids:
                block_bid[t] = self.bids[t]
        return block_bid



