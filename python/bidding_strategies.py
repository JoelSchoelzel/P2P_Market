import numpy as np


class mar_agent_bes(object):
    """Market agent for each building energy system (BES) that creates the bids."""

    def __init__(self, options, par_rh, node):
        self.p_min = options["p_min"] + 0.001
        self.p_max = options["p_max"] - 0.001
        self.p = {}
        self.q = {}
        # self.dt = par_rh["duration"][0][0]
        self.dt = next(iter(par_rh["duration"][0].values()))
        self.soc_nom_tes = node["devs"]["tes"]["cap"]
        self.soc_nom_bat = node["devs"]["bat"]["cap"]
        self.power_nom_bat = node["devs"]["bat"]["max_ch"]
        self.heat_hp_min = 0
        self.heat_hp_max = node["devs"]["hp35"]["cap"] + node["devs"]["hp55"]["cap"]
        self.heat_chp_min = 0
        self.heat_chp_max = node["devs"]["chp"]["cap"]
        self.eta_ch = node["devs"]["tes"]["eta_ch"]
        self.eta_dch = node["devs"]["tes"]["eta_dch"]

    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options, strategies, weights):
        """Compute the bid when electricity for the heat pump needs to be bought."""

        # compute bids with ZERO-INTELLIGENCE
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 1000, self.p_max * 1000) / 1000
            q = p_imp
        # compute bids with LEARNING
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_buy"])
            q = p_imp

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

        buying = str("True")

        return [p, q, buying, n], unflex

    def compute_chp_bids(self, chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options, strategies, weights):
        """Compute the bid when electricity from the CHP needs to be sold."""

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 1000, self.p_max * 1000) / 1000
        # compute bids with learning
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_sell"])

        unflex = 0
        # calculate unflexible bids if flexible demands are enabled
        if options["flexible_demands"]:
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
            if self.soc_nom_tes == 0 or soc >= self.soc_nom_tes:
                unflex = chp_sell
        # if flexible demands are disabled, everything is unflexible
        else:
            unflex = chp_sell

        q = chp_sell

        buying = str("False")

        return [p, q, buying, n], unflex

    def compute_empty_bids(self, n):
        """Create an empty bid when no electricity needs to be bought or sold."""
        p = self.p_min # has to be p_min because of usage in block bid calculation and opti model
        q = 0
        buying = str("None")
        # buying = str("True")
        return [p, q, buying, n], 0

    def compute_pv_bids(self, soc_bat, p_ch_bat, pv_sell, n, bid_strategy,
                        strategies, weights, options):
        """Compute the bid when electricity from the PV needs to be sold."""

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 1000, self.p_max * 1000) / 1000
        # compute bids with learning
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_sell"])

        unflex = 0
        soc_set_max = self.soc_nom_bat - (p_ch_bat + pv_sell) * self.dt
        if options["flexible_demands"]:
            if soc_bat >= soc_set_max:
                unflex = pv_sell
            else:
                unflex = 0
        else:
            unflex = pv_sell

        q = pv_sell
        buying = str("False")

        return [p, q, buying, n], unflex

    def one_price(self, bid, par_rh, n_opt, block_length):

        price_list = []
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            if bid[t][0] > 0:
                price_list.append(bid[t][0])
        #try:
        #    mean_price = sum(price_list) / len(price_list)
        #except ZeroDivisionError:
        #    mean_price = 0
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            if bid[t][0] > 0:
                bid[t][0] = price_list[0]

        return bid