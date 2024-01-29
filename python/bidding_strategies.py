import numpy as np


class mar_agent_bes(object):
    """Market agent for each building energy system (BES) that creates the bids."""

    def __init__(self, options, par_rh, node):
        self.p_min = options["p_min"]
        self.p_max = options["p_max"]

        self.p = {}
        self.q = {}

        # self.dt = par_rh["duration"][0][0]
        self.dt = next(iter(par_rh["duration"][0].values()))
        self.soc_nom_tes = node["devs"]["tes"]["cap"]

       # self.soc_nom_bat = node["devs"]["BAT"]["cap"]
       # self.power_nom_bat = node["devs"]["BAT"]["load"]

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
        hp_bid = [p, q, buying, n]

        return hp_bid, unflex

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


    # NEW! copied from https://github.com/JoelSchoelzel/local_market/blob/main/python/bidding_strategies.py
    def compute_pv_bids(self, dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat, pv_sell, pv_peak, t, n, bid_strategy,
                        strategies, weights):
        """Compute the bid when electricity from the PV needs to be sold."""

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

        # return [n, p, q, t, "selling"], unflex

        return [p, q, buying, n], unflex

    def compute_block_bid(bes, opti_res, par_rh, mar_agent_prosumer, n_opt, options, nodes, init_val, propensities,
                          strategies):
        """computes i hour block bids for every building and the bids are created by each building's mar_agent.
        Returns:
            bid (dict): 3 hour block bids containing price, quantity, Boolean whether buying/selling, building number.
            bes (object): inflexible demand is stored in bes for each building"""

        block_bids = {
            "p": [],
            "q": [],

        }
        block_length = 3

        for t_offset in range(block_length):  # for t, t+1, t+2
            t = par_rh["time_steps"][n_opt][0] + t_offset
            for n in range(len(opti_res)):
                # get parameters for bidding at time t
                p_imp = opti_res[n][4][t]
                chp_sell = opti_res[n][8]["chp"][t]
                bid_strategy = options["bid_strategy"]

                # compute bids for time t
                if p_imp > 0.0:
                    bid_key = f"bes_{n}_t{t_offset}"
                    block_bids[bid_key] = mar_agent_prosumer[n].compute_hp_bids(p_imp, n, bid_strategy)

                elif chp_sell > 0:
                    bid_key = f"bes_{n}_t{t_offset}"
                    block_bids[bid_key] = mar_agent_prosumer[n].compute_chp_bids(chp_sell, n, bid_strategy)

                else:
                    bid_key = f"bes_{n}_t{t_offset}"
                    block_bids[bid_key] = mar_agent_prosumer[n].compute_empty_bids(n)

        return block_bids

