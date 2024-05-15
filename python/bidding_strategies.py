import numpy as np

class mar_agent_bes(object):
    def __init__(self, p_max, p_min, par_rh, node):
        self.p_min = p_min
        self.p_max = p_max

        self.p = {}
        self.q = {}

        #self.dt = par_rh["duration"][0][0]
        self.dt = next(iter(par_rh["duration"][0].values()))
        self.soc_nom_tes = node["devs"]["tes"]["cap"]
        self.soc_nom_bat = node["devs"]["bat"]["cap"]


    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options):


        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
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


    def compute_chp_bids(self, chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options):

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        p = np.around(p, decimals=6)

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

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n], 0


    #Added newly from https://github.com/JoelSchoelzel/local_market/blob/main/python/bidding_strategies.py
    def compute_pv_bids(self, dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat, pv_sell, pv_peak, t, n, bid_strategy,
                        strategies, weights, options):

        # compute bids with device oriented bidding
        if bid_strategy == "devices":
            soc_nom = self.soc_nom_bat
            #power_nom = self.power_nom_bat

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

        if bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights[t]["bes_" + str(n) + "_sell"])

        # compute bids with zero-intelligence
        elif bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100

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

        # if bid_strategy != "devices":
        #     # check which bids are unflexible by checking which bids would have been placed with p_max for device oriented bidding
        #     if p == self.p_min:
        #         unflex = q

        return [p, q, buying, n], unflex
