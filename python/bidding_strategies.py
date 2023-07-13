import numpy as np


class mar_agent_bes(object):
    def __init__(self, p_max, p_min, par_rh, node):
        self.p_min = p_min
        self.p_max = p_max

        self.p = {}
        self.q = {}

        self.dt = par_rh["duration"][0][0]
        self.soc_nom_tes = node["devs"]["tes"]["cap"]

    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp):

        # calculate unflexible bids
        soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
        if self.soc_nom_tes == 0 or soc <= soc_set_min:
            unflex = p_imp
        elif p_imp > power_hp:
            unflex = p_imp - power_hp
        else:
            unflex = 0

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
            q = p_imp
            q_2 = 0
            p_2 = 0

        buying = str("True")

        return [p, q, buying, n], unflex

    def compute_chp_bids(self, chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc):

        # calculate unflexible bids
        soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
        if self.soc_nom_tes == 0 or soc <= soc_set_min:
            unflex = chp_sell

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        q = chp_sell

        buying = str("False")

        return [p, q, buying, n], unflex

    def compute_empty_bids(self, n):

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n], 0
