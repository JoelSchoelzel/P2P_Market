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

        self.soc_nom_bat = node["devs"]["bat"]["cap"]
        self.power_nom_bat = node["devs"]["bat"]["max_ch"]
        self.heat_hp_min = 0
        self.heat_hp_max = node["devs"]["hp35"]["cap"] + node["devs"]["hp55"]["cap"]
        self.eta_ch = node["devs"]["tes"]["eta_ch"]
        self.eta_dch = node["devs"]["tes"]["eta_dch"]


    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options, strategies,
                        weights, heat_hp, heat_devs, soc_set_max):
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


        # compute bids with DEVICE ORIENTED STRATEGY
        if bid_strategy == "devices":
            #x = []

            #for i in range(7):
            #    x.append(sum(dem_heat[i * 24:i * 24 + 24]) + 0.5 * sum(dem_dhw[i * 24:i * 24 + 24]))
            # soc_set_max = max(x)
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt

            charge = self.eta_ch * heat_devs
            discharge = 1 / self.eta_dch * (dem_heat + 0.5 * dem_dhw)

            if self.soc_nom_tes == 0:
                p = self.p_max
            else:
                if soc <= soc_set_min:
                    p = self.p_max
                elif discharge > charge and soc > soc_set_min and soc <= soc_set_max:
                    # p = self.p_min + (self.p_max - self.p_min) * (heat_hp / self.heat_hp_max)
                    p = self.p_min + (self.p_max - self.p_min) * (
                                (dem_heat - heat_hp) / (dem_heat - self.heat_hp_min))
                    # heat_hp >= (dem_heat[t] + 0.5 * dem_dhw[t]), wegen Auslegung
                    # p = self.p_max + (- self.p_max + self.p_min) * ((np.absolute(heat_hp - (dem_heat[t] + 0.5 * dem_dhw[t]))) / (self.heat_hp_max - self.heat_hp_min))
                elif charge > discharge and soc > soc_set_min and soc <= soc_set_max:
                    # p = self.p_min + (self.p_max - self.p_min) * (heat_hp / self.heat_hp_max)
                    p = self.p_max - (self.p_max - self.p_min) * (
                                (np.absolute(heat_hp - dem_heat)) / (self.heat_hp_max - dem_heat))
                    # p = self.p_max + (- self.p_max + self.p_min) * ((np.absolute(heat_hp - (dem_heat[t] + 0.5 * dem_dhw[t]))) / (self.heat_hp_max - self.heat_hp_min))
                else:
                    p = self.p_min

            q = p_imp # Annahme, dass komplette Menge flexibel ist

            #
            # if p_imp == power_hp:
            #     q = power_hp
            #     q_2 = 0
            #     p_2 = 0
            # elif p_imp > power_hp:
            #     q = power_hp
            #     q_2 = p_imp - power_hp
            #     p_2 = self.p_max
            # elif p_imp < power_hp:
            #     q = p_imp


        # compute bids with ZERO-INTELLIGENCE
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
            q = p_imp
        # compute bids with LEARNING
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_buy"])
            q = p_imp

        buying = str("True")

        return [p, q, buying, n], unflex

    def compute_chp_bids(self, chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options, strategies,
                         weights, heat_chp, heat_devs, soc_set_max):
        """Compute the bid when electricity from the CHP needs to be sold."""

        unflex = 0

        # calculate unflexible bids if flexible demands are enabled
        if options["flexible_demands"]:
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
            if self.soc_nom_tes == 0 or soc >= self.soc_nom_tes:
                unflex = chp_sell
        # if flexible demands are disabled, everything is unflexible
        else:
            unflex = chp_sell


        # compute bids with device oriented strategy
        if bid_strategy == "devices":
            x = []
            #for i in range(7):
            #    x.append(sum(dem_heat[i*24:i*24+24]) + sum(dem_dhw[i*24:i*24+24]))
            #soc_set_max = max(x)

            soc_set_min = (dem_heat + dem_dhw) * self.dt

            charge = self.eta_ch * heat_devs
            discharge = 1 / self.eta_dch * dem_heat

            if self.soc_nom_tes == 0:
                p = self.p_min
            else:
                if soc <= soc_set_min:
                    p = self.p_min
                elif discharge > charge and soc > soc_set_min and soc <= soc_set_max:
                    p = self.p_min + (self.p_max - self.p_min) * ((dem_heat - heat_chp) / (dem_heat - self.heat_chp_min))
                    #p = self.p_min + (self.p_max - self.p_min) * ((np.absolute(heat_chp - (dem_heat[t] + dem_dhw[t]))) / (self.heat_chp_max - self.heat_chp_min))
                elif charge > discharge and soc > soc_set_min and soc <= soc_set_max:
                    p = self.p_max - (self.p_max - self.p_min) * ((np.absolute(heat_chp - dem_heat)) / (self.heat_chp_max - dem_heat))
                    #p = self.p_min + (self.p_max - self.p_min) * ((np.absolute(heat_chp - (dem_heat[t] + dem_dhw[t]))) / (self.heat_chp_max - self.heat_chp_min))

                else:
                    p = self.p_max


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
        buying = str("None")
        # buying = str("True")
        return [p, q, buying, n], 0


    # NEW! copied from https://github.com/JoelSchoelzel/local_market/blob/main/python/bidding_strategies.py
    def compute_pv_bids(self, dem_elec, soc_bat, power_pv, p_ch_bat, p_dch_bat, pv_sell, pv_peak, t, n, bid_strategy,
                        strategies, weights, options):
        """Compute the bid when electricity from the PV needs to be sold."""

        soc_nom = self.soc_nom_bat
        power_nom = self.power_nom_bat
        soc_set_max = soc_nom - (p_ch_bat + pv_sell) * self.dt
        soc_set_min = p_dch_bat * self.dt
        unflex = 0

        if options["flexible_demands"]:
            if soc_bat >= soc_set_max:
                unflex = pv_sell
            else:
                unflex = 0
        else:
            unflex = pv_sell

        # compute bids with device oriented strategy
        if bid_strategy == "devices":
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


        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        # compute bids with learning
        elif bid_strategy == "learning":
            p = np.random.choice(strategies, p=weights["bes_" + str(n) + "_sell"])

        q = pv_sell
        buying = str("False")

        return [p, q, buying, n], unflex