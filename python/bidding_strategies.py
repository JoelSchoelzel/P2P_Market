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
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
            q = p_imp
            q_2 = 0
            p_2 = 0

        buying = str("True")
        #p = np.around(p, decimals=4)
        #p_2 = np.around(p_2, decimals=4)

        return [p, q, buying, n]


    def compute_chp_bids(self, chp_sell, n, bid_strategy,):


        q = chp_sell
        buying = str("False")

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        p = np.around(p, decimals=6)

        return [p, q, buying, n]


    def compute_empty_bids(self, n):

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n]


    #Added newly from https://github.com/JoelSchoelzel/local_market/blob/main/python/bidding_strategies.py
    def compute_pv_bids(self, dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat, pv_sell, pv_peak, t, n, bid_strategy,
                        strategies, weights):

        soc_nom = self.soc_nom_bat
        power_nom = self.power_nom_bat

        soc_set_max = soc_nom - (p_ch_bat + pv_sell) * self.dt
        soc_set_min = p_dch_bat * self.dt

        if self.soc_nom_bat == 0:
            p = self.p_min
        else:
            # flexi mit bat    --> soc_bat nach Markt anpassen --> mar_dat --> init_val
            if soc_bat <= 0:  # soc_set_min:
                p = self.p_max  # p_max, weil noch ausreichend Kapazität vorhanden ist, um Strom einzuspeichern
            elif p_dch_bat > p_ch_bat and soc_bat >= soc_set_min and soc_bat < soc_set_max:
                p = self.p_max + (self.p_min - self.p_max) * (pv_sell / pv_peak)

            elif p_ch_bat > p_dch_bat and soc_bat >= soc_set_min and soc_bat < soc_set_max:
                p = self.p_min + (self.p_max - self.p_min) * (np.absolute(pv_sell - dem_elec[t]) / pv_peak)

            else:  # soc_bat <= soc_set_max:
                p = self.p_min  # p_min, weil Speicher fast voll und Strom weg muss

        q = pv_sell
        buying = str("False")

        unflex = 0
        if bid_strategy != "devices":
            # check which bids are unflexible by checking which bids would have been placed with p_max for device oriented bidding
            if p == self.p_min:
                unflex = q

            if bid_strategy == "learning":
                p = np.random.choice(strategies, p=weights[t]["bes_" + str(n) + "_sell"])
            # compute bids with zero-intelligence
            elif bid_strategy == "zero":
                # create random price between p_min and p_max
                p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        p = np.around(p, decimals=6)

        return [p, q, buying, n] #, unflex
