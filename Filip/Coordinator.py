from python.market_preprocessing import sort_bids
from python.auction import single_round, multi_round


class Coordinator:

    def __init__(self, bid):
        self.bid = bid
        self.transaction_1 = self.get_transactions_1()
        self.transactions_2 = self.get_transactions_2()
        self.bids = sort_bids(self.bid, options=__main__. )

    def get_transactions_1(self):
        transactions_1, bids_1 = single_round(self.bids)
        return transactions_1

    def get_transactions_2(self):
        transactions_2, bids_2 = multi_round(self.bids)
        return transactions_2

    def send_back(self):
        if self.transaction_1:





