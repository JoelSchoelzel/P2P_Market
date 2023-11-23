import numpy as np


class mar_agent_bes(object):
    def __init__(self, p_max, p_min, pars_rh):
        self.p_min = p_min
        self.p_max = p_max

        self.p = {}
        self.q = {}


    def compute_hp_bids(self, p_imp, n, bid_strategy):


        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100 #TODO set the price
            q = p_imp
            q_2 = 0
            p_2 = 0

        buying = str("True")
        #p = np.around(p, decimals=4)
        #p_2 = np.around(p_2, decimals=4)

        return [p, q, buying, n]


    def compute_chp_bids(self, chp_sell, n, bid_strategy):


        q = chp_sell
        buying = str("False")

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100 #TODO set the
        p = np.around(p, decimals=6)

        return [p, q, buying, n]


    def compute_empty_bids(self, n):

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n]


