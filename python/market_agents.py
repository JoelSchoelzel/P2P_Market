import numpy as np
from python.css_functions.solar import Sun
import python.css_functions.wind_turbines as wind_turbines

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
    def __init__(self, options, districtData):
        self.p_min = options["p_min"] + 0.001
        self.p_max = options["p_max"] - 0.001
        self.filePath = districtData.filePath
        self.time = districtData.time
        self.site = districtData.site

        self.pv_area = 100 # m^2
        self.wind_turbine_model = "WT_Enercon_E40" # csv: wind_speed in m/s; power in kW
        self.bat_capacity = 300 # kWh
        self.bat_soc_max = 0.9 # 0.9 = 90% of the capacity
        self.bat_soc_min = 0.1  # 0.1 = 10% of the capacity
        self.bat_eta = 0.97 # 0.97 --> 3% losses during charging
        self.bat_soc_ch_max = 0.5 # 0.5 = 50% of capacity as charging power in kW
        self.bat_soc_dch_max = 0.5 # 0.5 = 50% of capacity as charging power in kW

        self.pv_power, self.wind_power = self.generation()

    def generation(self):

        global sun
        sun = Sun(filePath=self.filePath)
        # calculate theoretical PV generation
        potentialPV, defaultSTC = \
            sun.calcPVAndSTCProfile(time=self.time,
                                    site=self.site,
                                    area_roof=self.pv_area,
                                    beta=[35], # In Germany, this is a roof pitch between 30 and 35 degrees
                                    gamma=[0], # surface azimuth angles (Orientation to the south: 0°)
                                    usageFactorPV=1,
                                    usageFactorSTC=0)

        potentialWIND = wind_turbines.wind_turbine_generation(self.site["wind_speed"], self.wind_turbine_model)

        return potentialPV, potentialWIND