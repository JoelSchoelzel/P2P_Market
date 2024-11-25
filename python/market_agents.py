import numpy as np


class mar_agent_bes(object):
    """
    Market agent for each building energy system (BES) that creates the bids.
    This class contains various bidding strategies
    """

    def __init__(self, options, n):
        self.bes_id = n
        self.p_min = options["p_min"] + 0.001
        self.p_max = options["p_max"] - 0.001
        self.step_size_price = 0.01  # step size for bidding (zero, learning)

        self.rec_erev_roth = 0.08  # recency parameter for learning intelligence agent [0,1]
        self.exp_erev_roth = 0.99  # experimentation parameter for learning intelligence agent [0,1]

        self.initial_propensity = 0.01 # initial propensities for learning intelligence agent


    def zero_bids(self, buying_quantity, selling_quantity):
        """Compute the bid when electricity for the heat pump needs to be bought."""

        # create random price between p_min and p_max
        p = np.random.randint(self.p_min * 1000, self.p_max * 1000) / 1000
        if buying_quantity > 0:
            q = buying_quantity
            buying = str("True")
        else:
            q = selling_quantity
            buying = str("False")

        # Create an empty bid when no electricity needs to be bought or sold.
        if buying_quantity == 0 and selling_quantity == 0:
            p = self.p_min  # has to be p_min because of usage in block bid calculation and opti model
            q = 0
            buying = str("None")

        return [p, q, buying, self.bes_id]

    def erev_roth_learning_bids(self, buying_quantity, selling_quantity):
        """

        :param buying_quantity:
        :param selling_quantity:

        :return:
        """

        ## calculate the weights based on markets results from previous trading round
        #weights =
        ## compute bids with learning
        #p = np.random.choice(allowed_bid_prices, p = weights["bes_" + str(n) + "_sell"])

        if buying_quantity > 0:
            q = buying_quantity
            buying = str("True")
        else:
            q = selling_quantity
            buying = str("False")

        # Create an empty bid when no electricity needs to be bought or sold.
        if buying_quantity == 0 and selling_quantity == 0:
            p = self.p_min  # has to be p_min because of usage in block bid calculation and opti model
            q = 0
            buying = str("None")

        return [p, q, buying, self.bes_id]

    # TODO: add here the code for calculating the bidding price with q learning
    def q_learning_bids(self):

        return

    def initial_propensities_erev_roth(self):
        """
        creates initial propensities for the first market round
        """
        # list of possible bid prices
        allowed_bid_prices = [round(x, 2) for x in np.arange(self.p_min, (self.p_max + self.step_size_price),
                                                         self.step_size_price)]
        # set inital propensities
        propensities = {}
        for n in range(self.nb_bes):
            propensities["bes_" + str(n) + "_buy"] = []
            propensities["bes_" + str(n) + "_sell"] = []
            for l in range(len(allowed_bid_prices)):
                propensities["bes_" + str(n) + "_buy"].append(self.initial_propensity)
                propensities["bes_" + str(n) + "_sell"].append(self.initial_propensity)

        return propensities, allowed_bid_prices

    def update_propensities_erev_roth(self, mar_dict, par_rh, n_opt, bes, options, pars_li, trade_res, strategies):
        # Todo: Integrate central supply systems
        # Todo: jsc: die Berechnung des Gebotspreises soll unabhängig vom Systems möglich sein

        # update the propensities depending on trading results for the next step

        # clearing_price = trade_res["average_trade_price"]
        # get last bid price of each building
        price = {n: 0 for n in range(options["nb_bes"])}
        sorted_bids = mar_dict["sorted_bids"][n_opt]
        for trading_round in range(len(sorted_bids)):
            for bid in range(len(sorted_bids[trading_round]["buy"])):
                building = sorted_bids[trading_round]["buy"][bid]["building"]
                price[building] = sorted_bids[trading_round]["buy"][bid]["price"]
            for bid in range(len(sorted_bids[trading_round]["sell"])):
                building = sorted_bids[trading_round]["sell"][bid]["building"]
                price[building] = sorted_bids[trading_round]["sell"][bid]["price"]
        for n in range(len(price)):
            price[n] = np.round(price[n], 2)

        bid = mar_dict["bid"]
        dem_total = trade_res["dem_total"]
        sup_total = trade_res["sup_total"]

        t = par_rh["time_steps"][n_opt][0]
        # if no supply or demand at all (trading not possible), the propensities do not change
        if dem_total[t] == 0 or sup_total[t] == 0:
            mar_dict["propensities"][n_opt+1] = mar_dict["propensities"][n_opt]

        else:
            for n in range(options["nb_bes"]):
                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"] = []
                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"] = []
                # if the bid was empty, the propensities do not change
                if bid[n_opt]["bes_" + str(n)][1] == 0:
                    mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"] \
                        = mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"]
                    mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"] \
                        = mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"]
                # if buying, only update prop buy
                elif bid[n_opt]["bes_" + str(n)][2] == "True":
                    mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"] \
                        = mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"]
                    for l in range(len(strategies)):
                        if price[n] == strategies[l]:

                            # r = bes[n]["tra_dem"][n_opt,t-par_rh["hour_start"][n_opt]] * (options["p_max"] - clearing_price[n_opt])
                            r = trade_res["el_from_distr"][n] * (options["p_max"] - price[n])

                            if ((1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"][l]) + (
                                    (1 - pars_li["exp"]) * r) >= 0:
                                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"].append(
                                    ((1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"][l])
                                    + ((1 - pars_li["exp"]) * r))
                            else:
                                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"].append(0)

                        else:
                            mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"].append(
                                (1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"][l] + \
                                mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"][l] * (
                                        pars_li["exp"] / (len(strategies) - 1)))
                # if selling, only update prop sell
                else:
                    mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_buy"] = mar_dict["propensities"][n_opt]["bes_" + str(n) + "_buy"]
                    for l in range(len(strategies)):
                        if price[n] == strategies[l]:

                            # r = (bes[n]["tra_gen"][n_opt, t - par_rh["hour_start"][n_opt]]) * (clearing_price[n_opt] - options["p_min"])
                            r = trade_res["el_to_distr"][n] * (price[n] - options["p_min"])

                            if (1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"][l] + (
                                    1 - pars_li["exp"]) * r >= 0:
                                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"].append(
                                    (1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"][l] \
                                    + (1 - pars_li["exp"]) * r)
                            else:
                                mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"].append(0)
                        else:
                            mar_dict["propensities"][n_opt+1]["bes_" + str(n) + "_sell"].append(
                                (1 - pars_li["rec"]) * mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"][l] \
                                + mar_dict["propensities"][n_opt]["bes_" + str(n) + "_sell"][l] \
                                * (pars_li["exp"] / (len(strategies) - 1)))

        return mar_dict["propensities"]

    def compute_weights(self):
        # calculates the weights of the bid prices depending on propensities
        weights = {}

        weights["bes_" + str(self.bes_id) + "_buy"] = []
        for s in range(len(propensities["bes_" + str(self.bes_id) + "_buy"])):
            if propensities["bes_" + str(self.bes_id) + "_buy"][s] > 0:
                weights["bes_" + str(self.bes_id) + "_buy"].append(
                    propensities["bes_" + str(self.bes_id) + "_buy"][s] / sum(propensities["bes_" + str(self.bes_id) + "_buy"]))
            else:
                weights["bes_" + str(self.bes_id) + "_buy"].append(0)

        weights["bes_" + str(self.bes_id) + "_sell"] = []
        for s in range(len(propensities["bes_" + str(self.bes_id) + "_sell"])):
            if propensities["bes_" + str(self.bes_id) + "_sell"][s] > 0:
                weights["bes_" + str(self.bes_id) + "_sell"].append(
                    propensities["bes_" + str(self.bes_id) + "_sell"][s] / sum(propensities["bes_" + str(self.bes_id) + "_sell"]))
            else:
                weights["bes_" + str(self.bes_id) + "_sell"].append(0)

        return weights


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


# TODO: Implement the market agent for the central supply system (CSS) that creates the bids.
class mar_agent_css(object):
    """Market agent for the central supply system (CSS) that creates the bids."""
    def __init__(self, options, par_rh, node):
        self.p_min = options["p_min"] + 0.001
        self.p_max = options["p_max"] - 0.001
        self.p = {}
        self.q = {}
        self.dt = next(iter(par_rh["duration"][0].values()))
        # self.soc_nom_tes = node.get("devs", {}).get("tes", {}).get("cap", 0)
        #self.soc_nom_bat = node["devs"]["bat"]["cap"]
        #self.power_nom_bat = node["devs"]["bat"]["max_ch"]
        #self.heat_hp_min = 0
        #self.heat_hp_max = node["devs"]["hp35"]["cap"] + node["devs"]["hp55"]["cap"]
        #self.heat_chp_min = 0
        #self.heat_chp_max = node["devs"]["chp"]["cap"]
        #self.eta_ch = node["devs"]["tes"]["eta_ch"]
        #self.eta_dch = node["devs"]["tes"]["eta_dch"]


    def compute_zero_bids(self, n, p_imp, dem_heat, soc, power_hp, options, p_min, p_max,
                          energy_range, buy_price_range, sell_price_range, node):
        ''' Create zero bids for the CSS based on random intelligence. '''
        bids = []

        if 's_hp35' in node["devs"] or 's_hp55' in node["devs"]:
            q = np.random.uniform(*energy_range)
            p = np.random.randint(self.p_min * 1000, self.p_max * 1000) / 1000
            buying = str("True")
            bids.append([p, q, buying, n])

        if 's_bat' in node["devs"]:
            q = np.random.uniform(*energy_range)
            p = np.random.uniform(*buy_price_range)
            buying = str("True")
            bids.append([p, q, buying, n])

            q = np.random.uniform(*energy_range)
            p = np.random.uniform(*sell_price_range)
            buying = str("False")
            bids.append([p, q, buying, n])

        if 's_pv' in node["devs"]:
            q = np.random.uniform(*energy_range)
            p = np.random.uniform(*sell_price_range)
            buying = str("False")
            bids.append([p, q, buying, n])

        if 's_wind' in node["devs"]:
            q = np.random.uniform(*energy_range)
            p = np.random.uniform(*sell_price_range)
            buying = str("False")
            bids.append([p, q, buying, n])

        return bids
"""
    def compute_learning_bids(self, n, p_imp, dem_heat, soc, power_hp, options, strategies, weights, node):
        ''' Create learning bids for the CSS based on predefined strategies and weights. '''
        bids = []

        if 's_hp35' in node["devs"] or 's_hp55' in node["devs"]:
            price = np.random.choice(strategies, p=weights["css_hp_buy"])
            energy_quantity = p_imp
            buying = str("True")
            bids.append([price, energy_quantity, buying, n])

        if 's_bat' in node["devs"]:
            price = np.random.choice(strategies, p=weights["css_bat_buy"])
            energy_quantity = p_imp
            buying = str("True")
            bids.append([price, energy_quantity, buying, n])

            price = np.random.choice(strategies, p=weights["css_bat_sell"])
            energy_quantity = p_imp
            buying = str("False")
            bids.append([price, energy_quantity, buying, n])

        if 's_pv' in node["devs"]:
            price = np.random.choice(strategies, p=weights["css_pv_sell"])
            energy_quantity = p_imp
            buying = str("False")
            bids.append([price, energy_quantity, buying, n])

        if 's_wind' in node["devs"]:
            price = np.random.choice(strategies, p=weights["css_wind_sell"])
            energy_quantity = p_imp
            buying = str("False")
            bids.append([price, energy_quantity, buying, n])

        return bids
"""

"""    
    def compute_hp_bids(self, p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options, strategies,
                        weights, heat_hp, heat_devs, node):  # soc_set_max
        '''Compute the bid when electricity for the heat pump needs to be bought.'''

        # compute bids with DEVICE ORIENTED STRATEGY
        if bid_strategy == "devices":
            x = []
            for i in range(7):
                x.append(sum(node["heat"][i * 24:i * 24 + 24]) + 0.5 * sum(node["dhw"][i * 24:i * 24 + 24]))
            # soc_set_max = max(x)
            soc_set_max = self.soc_nom_tes
            soc_set_min = (dem_heat + 0.5 * dem_dhw) * self.dt
            charge = self.eta_ch * heat_devs
            discharge = 1 / self.eta_dch * (dem_heat + 0.5 * dem_dhw)

            if self.soc_nom_tes == 0:
                p = self.p_max

    def compute_battery_bids(self, p_imp, soc, bid_strategy, dem_elec, elec_devs, options, strategies, weights):
        '''Compute the bid for the shared battery.'''

        # compute bids with DEVICE ORIENTED STRATEGY
        if bid_strategy == "devices":
            soc_set_max = self.soc_nom_bat
            soc_set_min = dem_elec * self.dt
            charge = self.eta_ch * elec_devs
            discharge = 1 / self.eta_dch * dem_elec
            if soc <= self.soc_set_min:
                p = self.p_max
            elif soc >= self.soc_nom_bat:
                p = self.p_min
            else:
                p = self.p_min + (self.p_max - self.p_min) * (soc / self.soc_nom_bat)
            q = p_imp
            buying = str("True")

            return [p, q, buying]

        # compute bids with LEARNING STRATEGY
        # ToDo: Implement learning strategy
        '''
        elif bid_strategy == "learning":
            p = 
            q = p_imp
            buying = str("True")

            return [p, q, buying]
        '''

    def compute_pv_bids(self, dem_elec, soc_bat, p_ch_bat, p_dch_bat, pv_sell, pv_peak, n, bid_strategy,
                        strategies, weights, options): # power_pv,
        '''Compute the bid for the shared PV park.'''
        # compute bids with DEVICE ORIENTED STRATEGY
        # ToDo: bid price for DO-Strategy is based on demand and supply?
        # compute bids with device oriented strategy
        if bid_strategy == "devices":
            soc_nom = self.soc_nom_bat
            # soc_set_max = soc_nom - (p_ch_bat + pv_sell) * self.dt
            soc_set_max = soc_nom
            soc_set_min = p_dch_bat * self.dt
            # power_nom = self.power_nom_bat

            if self.soc_nom_bat == 0:
                p = self.p_min
            else:
                # flexi mit bat    --> soc_bat nach Markt anpassen --> mar_dat --> init_val
                if soc_bat <= 0:  # soc_set_min:
                    p = self.p_max  # p_max, weil noch ausreichend Kapazität vorhanden ist, um Strom einzuspeichern
                elif p_dch_bat > p_ch_bat and soc_set_min <= soc_bat < soc_set_max:
                    p = self.p_max + (self.p_min - self.p_max) * (pv_sell / pv_peak)
                elif p_ch_bat > p_dch_bat and soc_set_min <= soc_bat < soc_set_max:
                    p = self.p_min + (self.p_max - self.p_min) * (np.absolute(pv_sell - dem_elec) / pv_peak)
                else:  # soc_bat <= soc_set_max:
                    p = self.p_min  # p_min, weil Speicher fast voll und Strom weg muss

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
        # compute bids with LEARNING STRATEGY
        # ToDo: Implement learning strategy
        '''
        elif bid_strategy == "learning":
            p = 
            q = pv_sell
            buying = str("False")

            return [p, q, buying]
        '''

    def compute_wind_bids(self, dem_elec, soc_bat, p_ch_bat, p_dch_bat, wind_sell, wind_peak, n, bid_strategy,
                        strategies, weights, options): # power_wind,
        '''Compute the bid for the shared wind park.'''
        if bid_strategy == "devices":
            p = self.p_min + (self.p_max - self.p_min) * (wind_sell / wind_peak)
            q = wind_sell
            buying = str("False")
            return [p, q, buying]

        # compute bids with LEARNING STRATEGY
        # ToDo: Implement learning strategy
    
"""

