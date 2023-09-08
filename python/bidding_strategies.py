import numpy as np


class mar_agent_bes(object):
    """Market agent for each building energy system (BES) that creates the bids."""

    def __init__(self, options, par_rh, node):
        self.p_min = options["p_min"]
        self.p_max = options["p_max"]

        self.p = {}
        self.q = {}

        self.dt = par_rh["duration"][0][0]
        self.soc_nom_tes = node["devs"]["tes"]["cap"]

    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options, strategies, weights):
        """Compute the bid when electricity for the heat pump needs to be bought."""

        # calculate unflexible bids if flexible demands are enabled
        if options["flexible_demands"]:
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
            if self.soc_nom_tes == 0 or soc <= soc_set_min:
                unflex = p_imp
            elif p_imp > power_hp:
                unflex = p_imp - power_hp
            else:
                unflex = 0
        # if flexible demands are disabled, everything is unflexible
        else:
            unflex = p_imp

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
            q = p_imp
        # compute bids with learning
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_buy"])
            q = p_imp

        buying = str("True")

        return [p, q, buying, n], unflex

    def compute_chp_bids(self, chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options, strategies, weights):
        """Compute the bid when electricity from the CHP needs to be sold."""

        unflex = 0

        # calculate unflexible bids if flexible demands are enabled
        if options["flexible_demands"]:
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
            if self.soc_nom_tes == 0 or soc <= soc_set_min:
                unflex = chp_sell
        # if flexible demands are disabled, everything is unflexible
        else:
            unflex = chp_sell

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        # compute bids with learning
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_sell"])

        q = chp_sell

        buying = str("False")

        return [p, q, buying, n], unflex

    def compute_empty_bids(self, n):
        """Create an empty bid when no electricity needs to be bought or sold."""

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n], 0
