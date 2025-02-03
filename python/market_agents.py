import numpy as np
from python.css_functions.solar import Sun
import python.css_functions.wind_turbines as wind_turbines
import random

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

        #self.p_feed_in = 0.0803 # feed-in tariff price (per kWh)
        #self.p_rate = 0.30 # utility service rate (per kWh)
        self.p_reg = 0.001 # price regulation for CES

    def __setitem__(self, key, value):
        self.__dict__["q_table"] = self.q_table

    def __getitem__(self, key):
        return getattr(self, key)

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

    # TODO: code for calculating the bidding price with q learning for BES
    # Todo: Ray done need to include capacity of WP or BHWK and max PV generation for relative calculation of buying and selling quantity

    def q_learning_bids(self, buying_quantity, selling_quantity, n_opt):
        # This function is used to calculate the bidding price for the BES using Q-learning
        # Based on current state and q-table, the agent selects an action (price) to bid, (buying or selling)
        # The agent then generates a bid based on the selected action
        self.decay_rate = 0.99 # decay rate for epsilon
        self.epsilon = max(0.1, self.epsilon_init * (self.decay_rate ** n_opt)) # decay epsilon over time until 0.1
        if n_opt == 0:
            action = random.choice(self.q_actions_BES)
        elif random.uniform(0, 1) < self.epsilon:
            action = random.choice(self.q_actions_BES)
        else:
            state_index = tuple(self.q_state)
            action = self.q_actions_BES[np.argmax(self.q_table[state_index])]

            # here q-table is used for determining the final bidding price
        if buying_quantity > 0:
            p = action
            q = buying_quantity
            buying = str("True")
        else:
            p = action
            q = selling_quantity
            buying = str("False")
        # Create an empty bid when no electricity needs to be bought or sold.
        if buying_quantity == 0 and selling_quantity == 0:
            p = action  # usage in block bid calculation and opti model
            q = 0
            buying = str("None")

        # Return the bid
        return [p, q, buying, self.bes_id]

    def initialize_q_table_q_learning(self):
        # This function is used to initialize the Q-table for Q-learning
        self.alpha, self.gamma, self.epsilon_init = 0.1, 0.4, 0.8  # learning rate, discount factor, exploration rate
        # The Q-table is a 4D numpy array that stores q-values for each state-action pair of each BES
        self.q_table = {}
        self.q_actions_BES = [round(x, 2) for x in np.arange(self.p_min + 0.01, self.p_max, self.step_size_price)]
        state_space = [10, 10, 10]
        self.q_state = ()

        # Initialize Q-tables (4D) for storing q-values for each state-action pair of each BES
        self.q_table = np.zeros(state_space + [len(self.q_actions_BES)])

        return self.q_table

    def get_state_q_learning(self, buying_quantity, buying_capacity, selling_quantity, selling_capacity, soc_state):
        # This function is used to map input variables to a discrete state index
        # The state space consists of relative buying quantity, relative selling quantity, and SOC state

        if not hasattr(self, 'buying_capacity'):
            self.buying_capacity = buying_capacity

        if not hasattr(self, 'selling_capacity'):
            self.selling_capacity = selling_capacity

        def discretize(value):
            if value == 0:
                return 0  # Special case for zero
            for n in range(1, 10):  # Range is [1, 9]
                lower_bound = 0.11 * (n - 1)
                upper_bound = 0.11 * n
                if lower_bound <= value < upper_bound:
                    return n
            return 9  # If value is outside the range, map it to the highest discrete value (9)

        # Calculate relative buying and selling quantities, and SOC
        bq_rel = buying_quantity / self.buying_capacity if self.buying_capacity != 0 else 0  # Relative to buying capacity
        sq_rel = selling_quantity / self.selling_capacity if self.selling_capacity != 0 else 0  # Relative to selling capacity
        soc = soc_state  # Current state of charge

        # Discretize values to get state
        bq_t = discretize(bq_rel)
        sq_t = discretize(sq_rel)
        ct = discretize(soc)

        # Combine into a state tuple
        self.q_state = (bq_t, sq_t, ct)
        return self.q_state

    def calc_reward_and_update_q_table(self, options, nodes, n, par_rh, n_opt, block_length, opti_res, mar_dict):
        # This function is used to calculate the reward for Q-learning and update the Q-table
        t = par_rh["time_steps"][n_opt][0]
        buying = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][2]
        q_dem = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
        p_match = 0.5 * (options["p_max"] + options["p_min"])
        q_match = 0
        p_min_sell = options["p_max"] - 0.001
        p_max_buy = options["p_min"] + 0.001
        soc_state = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]

        # update q-tables of BES agents after each negotiation round
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            if buying == "True":
                p_match = options["p_max"] - 0.001
            elif buying == "False":
                p_match = options["p_min"] + 0.001

            # if any negotiation results exist, get the trading price and quantity
            if len(mar_dict["negotiation_results"][n_opt][0]) > 0:
                match_nr = None
                for match in mar_dict["negotiation_results"][n_opt][0]:  # find match number
                    if (mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == n or
                            mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == n):
                        match_nr = match  # Store the match number/key
                        break  # Exit the loop as the desired match is found

                if match_nr is not None:  # Access trading_price for the respective match
                    p_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_price"][t]
                    q_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_quantity"][t]

            if len(mar_dict["sell_list"][n_opt]) > 0:
                p_min_sell = min(mar_dict["sell_list"][n_opt][n]["mean_price"]
                                 for n in range(len(mar_dict["sell_list"][n_opt])))

            if len(mar_dict["buy_list"][n_opt]) > 0:
                p_max_buy = max(mar_dict["buy_list"][n_opt][n]["mean_price"]
                                for n in range(len(mar_dict["buy_list"][n_opt])))

            if opti_res[n_opt][n][12]["bat"] != 0: # if battery exists
                soc_state = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]

        # calculate reward
        reward1 = self.calc_reward_q_learning_v1(buying, p_match, q_match, q_dem)
        reward2 = self.calc_reward_q_learning_v2(buying, p_min_sell, p_max_buy, p_match, soc_state)
        reward3 = self.calc_reward_q_learning_v3(buying, p_match, q_match, q_dem, soc_state)
        reward4 = self.calc_reward_q_learning_v4(buying, p_match, q_match, q_dem, soc_state)

        # Calculate new buying/selling quantity & SoC
        new_buy_quant = 0
        new_sell_quant = 0
        new_soc = soc_state
        # eta_tes = nodes[n]["devs"]["tes"]["eta_tes"]
        # for t in par_rh["time_steps"][n_opt][0:block_length]:
        #     current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
        #     ch_tes = opti_res[n_opt][n][5]["tes"][t]
        #     dch_tes = opti_res[n_opt][n][6]["tes"][t]
        # new_soc = max(0, current_soc * eta_tes + (ch_tes - dch_tes) / opti_res[n_opt][n][12]["tes"])
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            # get remaining demand and remaining supply
            if buying == "True":  # when buying
                # look for the matched bid and find the matched buying quantity
                remaining_demand = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    match_nr = None
                    for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        if mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == n:
                            match_nr = match
                            break
                    if match_nr is not None:
                        remaining_demand = mar_dict["negotiation_results"][n_opt][0][match_nr][
                            "remaining_demand"][t]
                new_buy_quant = remaining_demand
            elif buying == "False":  # when selling
                remaining_supply = mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][1]
                # look for the matched bid and find the matched buying quantity
                if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    match_nr = None
                    for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        if mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == n:
                            match_nr = match
                            break
                            # todo: check if this is correct
                    if match_nr is not None:
                        remaining_supply = mar_dict["negotiation_results"][n_opt][0][match_nr][
                            "remaining_supply"][t]
                new_sell_quant = remaining_supply

            # calculate new SoC
            if opti_res[n_opt][n][12]["bat"] == 0:  # if battery doesn't exist
                current_soc = opti_res[n_opt][n][3]["tes"][t] / opti_res[n_opt][n][12]["tes"]
                eta_tes = nodes[n]["devs"]["tes"]["eta_tes"]
                ch_tes = opti_res[n_opt][n][5]["tes"][t]
                dch_tes = opti_res[n_opt][n][6]["tes"][t]
                new_soc = max(0, current_soc * eta_tes + (ch_tes - dch_tes) / opti_res[n_opt][n][12]["tes"])
                # todo: how to correctly calculate new soc for TES?
            else:  # if battery exist
                current_soc = opti_res[n_opt][n][3]["bat"][t] / opti_res[n_opt][n][12]["bat"]
                eta_bat = nodes[n]["devs"]["bat"]["eta_bat"]
                ch_bat = opti_res[n_opt][n][5]["bat"][t]
                dch_bat = opti_res[n_opt][n][6]["bat"][t]
                k_loss = nodes[n]["devs"]["bat"]["k_loss"]
                new_soc = (1 - k_loss) * current_soc + eta_bat * (ch_bat - dch_bat) / opti_res[n_opt][n][12]["bat"]

        # update q-table
        # reward can be chosen from available reward functions
        self.q_table = (
            self.update_q_table_q_learning(action=mar_dict["block_bids"][n_opt]["bes_" + str(n)][t][0],
                                           reward=reward1,
                                           new_buy_quant=new_buy_quant, new_sell_quant=new_sell_quant,
                                           new_soc=new_soc))

        #mar_dict["q_tables"][n] = self.q_table
        return self.q_table

    def calc_reward_q_learning_v1(self, buying, p_match, q_match, q_dem):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        eco_coeff = 0.7
        trade_coeff = 0.3
        if buying == "True":
            reward = (eco_coeff * (self.p_max - p_match) / ((self.p_max - self.p_min)) +
                      trade_coeff * q_match / q_dem)
        elif buying == "False":
            reward = (eco_coeff * (p_match - self.p_min) / ((self.p_max - self.p_min)) +
                      trade_coeff * q_match / q_dem)
        else:
            reward = 0
        return reward

    def calc_reward_q_learning_v2(self, buying, p_min_sell, p_max_buy, p_match, soc_state):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        g_buy = 5
        g_sell = 2.5
        h_buy = 2
        h_sell = 2
        if buying == "True":
            reward = g_buy * (self.p_max - p_min_sell) - h_buy * soc_state
        elif buying == "False":
            reward = g_sell * (p_max_buy - p_match) + h_sell * soc_state
        else:
            reward = 0
        return reward

    def calc_reward_q_learning_v3(self, buying, p_match, q_match, q_dem, soc_state):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        eco_coeff = 0.3
        trade_coeff = 0.6
        soc_coeff = 0.1
        if buying == "True":
            reward = (eco_coeff * (self.p_max - p_match) / (self.p_max - self.p_min) +
                      trade_coeff * q_match / q_dem - soc_coeff * soc_state)
        elif buying == "False":
            reward = (eco_coeff * (p_match - self.p_min) / (self.p_max - self.p_min) +
                      trade_coeff * q_match / q_dem + soc_coeff * soc_state)
        else:
            reward = 0
        return reward

    def calc_reward_q_learning_v4(self, buying, p_match, q_match, q_dem, soc_state):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        eco_coeff = 0.3
        trade_coeff = 0.6
        soc_coeff = 0.1
        if buying == "True":
            reward = (eco_coeff * (self.p_max - p_match) * q_match / ((self.p_max - self.p_min) * q_dem) + trade_coeff * q_match / q_dem - soc_coeff * soc_state)
        elif buying == "False":
            reward = (eco_coeff * (p_match - self.p_min) * q_match / ((self.p_max - self.p_min) * q_dem) + trade_coeff * q_match / q_dem + soc_coeff * soc_state)
        else:
            reward = 0
        return reward

    def update_q_table_q_learning(self, action, reward, new_buy_quant, new_sell_quant, new_soc):
        # This function is used to update the Q-table for Q-learning
        # The Q-table is updated based on the current state, action, reward, and next state
        # Reward calculated beforehand, and given as input

        # Get the index of the current state
        state_index = tuple(self.q_state)

        # Calculate the next state and get its index
        next_state = self.get_state_q_learning(new_buy_quant, self.buying_capacity, new_sell_quant,
                                               self.selling_capacity, new_soc)
        next_state_index = tuple(next_state)

        # Get the index of the action in the actions list
        action = round(action, 2)
        action_index = self.q_actions_BES.index(action)

        # Retrieve the current q-value from the Q-table
        current_q = self.q_table[state_index + (action_index,)]

        # Calculate the new q-value based on the Bellman equation
        max_future_q = np.max(self.q_table[next_state_index])
        new_q = (1 - self.alpha) * current_q + self.alpha * (reward + self.gamma * max_future_q)

        # Update the Q-table with the new q-value
        self.q_table[state_index + (action_index,)] = new_q

        return self.q_table

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

    def compute_weights(self, propensities):
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
        self.css_id = options["nb_bes"]
        self.p_min = options["p_min"] + 0.001
        self.p_max = options["p_max"] - 0.001
        self.step_size_price = 0.01  # step size for bidding (zero, learning)
        self.p_feed_in = 0.05  # feed-in tariff price (per kWh)
        self.p_rate = 0.30  # utility service rate (per kWh)

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
        self.k_loss = 0.005 # 0.005 = 0.5% losses during charging

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

    def zero_bids_css(self, buying_quantity, selling_quantity):
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

        return [p, q, buying, self.css_id]

    def q_learning_bids00(self, buying_quantity, selling_quantity, p_feed_in, p_rate, p_reg,
                        p_i_sell, p_j_buy, e_t_SES, E_SES,
                        min_offer_price, max_bid_price,
                        gbuy, gsell, hbuy, hsell, beta,
                        alpha=0.1, gamma=0.9, epsilon=0.1):

        """
           Q-learning algorithm for bid pricing in energy markets.

           :param p_feed_in: Feed-in tariff price (per kWh).
           :param p_rate: Utility service rate (per kWh).
           :param p_reg: Price regulation for CES.
           :param state_space: Tuple defining state space dimensions (e.g., (10, 10, 10)).
           :param p_i_sell: List of seller prices.
           :param p_j_buy: List of buyer prices.
           :param e_t_SES: Current SES energy level.
           :param E_SES: Total SES capacity.
           :param min_offer_price: Minimum price offered by sellers.
           :param max_bid_price: Maximum price offered by buyers.
           :param gbuy: Coefficient for buy reward.
           :param gsell: Coefficient for sell reward.
           :param hbuy: Coefficient for buy penalty (SOC effect).
           :param hsell: Coefficient for sell reward (SOC effect).
           :param beta: Penalty for trying to sell without buyers.
           :param alpha: Learning rate.
           :param gamma: Discount factor.
           :param epsilon: Exploration rate for epsilon-greedy policy.
           :return: Selected action, updated Q-table, and generated bid.
           """
        state_space = (10, 10, 10)  # Tuple defining state space dimensions ((ot, bt, ct))
        actions_SES = ['charge', 'discharge', 'idle']
        actions_RES = ['peers', 'battery', 'grid', 'idle']

        # Initialize Q-tables for CES & BES
        q_table_ces = np.zeros(state_space + (len(actions_SES),))
        q_table_PV = np.zeros(state_space + (len(actions_RES),))
        q_table_WT = np.zeros(state_space + (len(actions_RES),))

        def get_state(self, p_i_sell, p_j_buy, e_t_SES, E_SES):
            """
            Map input variables to a discrete state index.

            :param ot: Seller's offer state (integer, 0-9).
            :param bt: Buyer's bid state (integer, 0-9).
            :param ct: CES SOC state (integer, 0-9).
            :return: Tuple representing the state (ot, bt, ct).
            """

            def discretize(value):
                for n in range(0, 9):  # Range is [1, 8] inclusive
                    lower_bound = 0.11 * (n - 1)
                    upper_bound = 0.11 * n

                    # Check if value satisfies the condition for this n
                    if p_i_sell == 0:
                        discr_value = 0
                    elif lower_bound <= value < upper_bound:
                        discr_value = n
                    else:
                        discr_value = 9
                    return discr_value

            # Calculate p_t_charge first, then discretize to get ot
            p_t_charge = ((min(p_i_sell) - p_feed_in) /
                          (p_rate - (p_feed_in + p_reg)))
            ot = discretize(p_t_charge)

            # calculate p_t_discharge first, then discretize to get bt
            p_t_discharge = ((max(p_j_buy) - self.p_feed_in - self.p_reg) /
                             (self.p_rate - (self.p_feed_in + self.p_reg)))
            bt = discretize(p_t_discharge)

            # calculate soc_t_SES first, then discretize to get ct
            soc_t_SES = e_t_SES / E_SES
            ct = discretize(soc_t_SES)

            state = (ot, bt, ct)
            return state

        state = get_state(p_i_sell, p_j_buy, e_t_SES, E_SES)

        # Epsilon-greedy action selection
        def select_action(state):
            if random.uniform(0, 1) < epsilon:
                return random.choice(actions_SES)
            else:
                state_index = tuple(state)
                return actions_SES[np.argmax(q_table_ces[state_index])]

        action = select_action(state)

        # Calculate reward
        def calculate_reward(action, state, soc_t_SES, min_offer_price, max_bid_price):
            if action == "charge":
                return gbuy * (p_rate - p_reg - min_offer_price) - hbuy * soc_t_SES
            elif action == "discharge":
                if state[1] == 0:  # No buyers
                    return -beta
                return gsell * (max_bid_price - min_offer_price) + hsell * soc_t_SES
            else:
                return 0

        reward = calculate_reward(action, state, e_t_SES / E_SES, min_offer_price, max_bid_price)

        # Update Q-table
        def update_q_table(state, action, reward, next_state):
            state_index = tuple(state)
            next_state_index = tuple(next_state)
            action_index = actions_SES.index(action)

            current_q = q_table_ces[state_index + (action_index,)]
            max_future_q = np.max(q_table_ces[next_state_index])
            new_q = (1 - alpha) * current_q + alpha * (reward + gamma * max_future_q)
            q_table_ces[state_index + (action_index,)] = new_q

        # Generate bid
        def generate_bid(action):
            if action == "charge":
                return {"action": "buy", "price": "min_offer_price"}
            elif action == "discharge":
                return {"action": "sell", "price": "max_bid_price"}
            else:
                return {"action": "idle"}

        if action == "buy":
            p = random.uniform(self.p_min, self.p_max)  # Price within range
            q = buying_quantity if buying_quantity > 0 else 0
            buying = "True"
        elif action == "sell":
            p = random.uniform(self.p_min, self.p_max)  # Price within range
            q = selling_quantity if selling_quantity > 0 else 0
            buying = "False"
        else:
            p = 0
            q = 0
            buying = "None"

        # Simulate next state and update Q-table
        next_state = get_state()
        update_q_table(state, action, reward, next_state)

        return action, q_table_ces, generate_bid(action)

    def q_learning_bids(self, buying_quantity, selling_quantity, n_opt):
        # This function is used to calculate the bidding price for the BES using Q-learning
        # Based on current state and q-table, the agent selects an action (price) to bid, (buying or selling)
        # The agent then generates a bid based on the selected action
        #self.epsilon = 0.1
        #if random.uniform(0, 1) < self.epsilon:
        #    action = random.choice(self.q_actions_CSS)
        #else:
        #    state_index = tuple(self.q_state)
        #    action = self.q_actions_CSS[np.argmax(self.q_table[state_index])]
            # here q-table is used for determining the final bidding price

        #if action == self.p_min - 0.01:
        #    action = self.p_min
        #elif action == self.p_max + 0.01:
        #    action = self.p_max

        self.decay_rate = 0.99  # decay rate for epsilon
        self.epsilon = max(0.1, self.epsilon_init * (self.decay_rate ** n_opt))  # decay epsilon over time until 0.1
        if n_opt == 0:
            action = random.choice(self.q_actions_CSS)
        elif random.uniform(0, 1) < self.epsilon:
            action = random.choice(self.q_actions_CSS)
        else:
            state_index = tuple(self.q_state)
            action = self.q_actions_CSS[np.argmax(self.q_table[state_index])]

        if buying_quantity > 0:
            p = action
            q = buying_quantity
            buying = str("True")
        else:
            p = action
            q = selling_quantity
            buying = str("False")
        # Create an empty bid when no electricity needs to be bought or sold.
        if buying_quantity == 0 and selling_quantity == 0:
            p = self.p_min  # has to be p_min because of usage in block bid calculation and opti model
            q = 0
            buying = str("None")

        # Return the bid
        return [p, q, buying, self.css_id]

    def initialize_q_table_q_learning(self):
        # This function is used to initialize the Q-table for Q-learning
        self.alpha, self.gamma, self.epsilon_init = 0.1, 0.4, 0.8  # learning rate, discount factor, exploration rate
        # The Q-table is a 4D numpy array that stores q-values for each state-action pair of each BES
        self.q_table = {}
        self.q_actions_CSS = [round(x, 2) for x in np.arange(self.p_min + 0.01, self.p_max, self.step_size_price)]
            #[round(x, 2) for x in np.arange(self.p_min, (self.p_max + self.step_size_price),
            #                                     self.step_size_price)]
        state_space = [10, 10, 10]
        self.q_state = ()

        # Initialize Q-tables (4D) for storing q-values for each state-action pair of each BES
        self.q_table = np.zeros(state_space + [len(self.q_actions_CSS)])

        return self.q_table

    def get_state_q_learning(self, buying_quantity, selling_quantity, soc_state):
        # This function is used to map input variables to a discrete state index
        # The state space consists of relative buying quantity, relative selling quantity, and SOC state

        buying_capacity = self.bat_soc_ch_max * self.bat_capacity
        selling_capacity = self.pv_power.max() + self.wind_power.max() + self.bat_soc_dch_max * self.bat_capacity

        def discretize(value):
            if value == 0:
                return 0  # Special case for zero
            for n in range(1, 10):  # Range is [1, 9]
                lower_bound = 0.11 * (n - 1)
                upper_bound = 0.11 * n
                if lower_bound <= value < upper_bound:
                    return n
            return 9  # If value is outside the range, map it to the highest discrete value (9)

        # Calculate relative buying and selling quantities, and SOC
        bq_rel = buying_quantity / buying_capacity  # Relative to buying capacity
        sq_rel = selling_quantity / selling_capacity  # Relative to selling capacity
        soc = soc_state  # Current state of charge

        # Discretize values to get state
        bq_t = discretize(bq_rel)
        sq_t = discretize(sq_rel)
        ct = discretize(soc)

        # Combine into a state tuple
        self.q_state = (bq_t, sq_t, ct)
        return self.q_state

    def calc_reward_and_update_q_table(self, options, opti_res_css, par_rh, n_opt, block_length, mar_dict):
        p_match = 0.5 * (options["p_max"] + options["p_min"])
        q_match = 0
        p_min_sell = options["p_max"] - 0.001
        p_max_buy = options["p_min"] + 0.001
        t = par_rh["time_steps"][n_opt][0]
        soc_state = opti_res_css[n_opt]["res_soc"]["s_bat"][t] / self.bat_capacity  # SoC %
        buying = mar_dict["block_bids"][n_opt]["css"][t][2]
        q_dem = mar_dict["block_bids"][n_opt]["css"][t][1]

        for t in par_rh["time_steps"][n_opt][0:block_length]:
            # get the inputs for reward calculation
            # buying = mar_dict["block_bids"][n_opt]["css"][t][2]
            # q_dem = mar_dict["block_bids"][n_opt]["css"][t][1]
            if len(mar_dict["buy_list"][n_opt]) > 0:  # if any buying bid exists
                # get the maximum price of all buying bids
                p_max_buy = max(mar_dict["buy_list"][n_opt][bid]["mean_price"]
                                for bid in range(len(mar_dict["buy_list"][n_opt])))
            if len(mar_dict["sell_list"][n_opt]) > 0:  # if any selling offer exists
                p_min_sell = min(mar_dict["sell_list"][n_opt][bid]["mean_price"]
                                 for bid in range(len(mar_dict["sell_list"][n_opt])))

            # find the matched bid and find the matched buying/selling quantity
            # if any negotiation results exist, get the trading price and quantity
            if len(mar_dict["negotiation_results"][n_opt][0]) > 0:
                match_nr = None
                for match in range(len(mar_dict["negotiation_results"][n_opt][0])):  # find match number
                    if (mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == options["nb_bes"] or
                            mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == options["nb_bes"]):
                        match_nr = match  # Store the match number/key
                        break  # Exit the loop as the desired match is found

                if match_nr is not None:  # Access trading_price for the respective match
                    p_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_price"][t]
                    q_match = mar_dict["negotiation_results"][n_opt][0][match_nr]["trading_quantity"][t]

        # calc reward for CSS agent
        reward_CSS1 = self.calc_reward_q_learning_v1(buying, p_match, q_match, q_dem)
        reward_CSS2 = self.calc_reward_q_learning_v2(buying, p_min_sell, p_max_buy, p_match, soc_state)

        # Calculate new buying/selling quantity & SoC
        new_buy_quant = 0
        new_sell_quant = 0
        new_soc = 0
        for t in par_rh["time_steps"][n_opt][0:block_length]:
            # get remaining demand and remaining supply
            if buying == "True":  # when buying
                # look for the matched bid and find the matched buying quantity
                remaining_demand = mar_dict["block_bids"][n_opt]["css"][t][1]
                if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    match_nr = None
                    for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        if mar_dict["negotiation_results"][n_opt][0][match]["buyer_id"] == options["nb_bes"]:
                            match_nr = match
                            break
                    if match_nr is not None:  # if match is found
                        remaining_demand = mar_dict["negotiation_results"][n_opt][0][match_nr][
                            "remaining_demand"][t]
                new_buy_quant = remaining_demand
            elif buying == "False":  # when selling
                remaining_supply = mar_dict["block_bids"][n_opt]["css"][t][1]
                # look for the matched bid and find the matched buying quantity
                if len(mar_dict["matched_bids_info"][n_opt][0]) > 0:
                    match_nr = None
                    # todo: check if this is correct
                    for match in range(len(mar_dict["negotiation_results"][n_opt][0])):
                        if mar_dict["negotiation_results"][n_opt][0][match]["seller_id"] == options["nb_bes"]:
                            match_nr = match
                            break
                            # todo: check if this is correct
                    if match_nr is not None:
                        remaining_supply = mar_dict["negotiation_results"][n_opt][0][match_nr][
                            "remaining_supply"][t]
                new_sell_quant = remaining_supply

            # calculate new SoC
            current_soc = soc_state
            eta_bat = self.bat_eta
            ch_bat = opti_res_css[n_opt]["res_p_ch"]["s_bat"][t]
            dch_bat = opti_res_css[n_opt]["res_p_dch"]["s_bat"][t]
            k_loss = self.k_loss
            new_soc = (1 - k_loss) * current_soc + eta_bat * (ch_bat - dch_bat) / self.bat_capacity

        # update q-table
        self.q_table = (
            self.update_q_table_q_learning(action=mar_dict["block_bids"][n_opt]["css"][t][0], reward=reward_CSS2,
                                           new_buy_quant=new_buy_quant, new_sell_quant=new_sell_quant, new_soc=new_soc))

        return self.q_table

    def calc_reward_q_learning_v1(self, buying, p_match, q_match, q_dem):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        eco_coeff = 0.7
        trade_coeff = 0.3
        if buying == "True":
            reward = (eco_coeff * (self.p_rate - p_match) * q_match / (self.p_rate - self.p_min) * q_dem +
                      trade_coeff * q_match / q_dem)
        elif buying == "False":
            reward = (eco_coeff * (p_match - self.p_feed_in) * q_match / (self.p_max - self.p_feed_in) * q_dem +
                      trade_coeff * q_match / q_dem)
        else:
            reward = 0
        return reward

    def calc_reward_q_learning_v2(self, buying, p_min_sell, p_max_buy, p_match, soc_state):
        # This function is used to calculate the reward for Q-learning
        # The reward is based on the buying/selling action, SOC state, and prices
        g_buy = 5
        g_sell = 2.5
        h_buy = 2
        h_sell = 2
        if buying == "True":
            reward = g_buy * (self.p_rate - p_min_sell) - h_buy * soc_state
        elif buying == "False":
            reward = g_sell * (p_max_buy - p_match) + h_sell * soc_state
        else:
            reward = 0
        return reward

    def update_q_table_q_learning(self, action, reward, new_buy_quant, new_sell_quant, new_soc):
        # This function is used to update the Q-table for Q-learning
        # The Q-table is updated based on the current state, action, reward, and next state
        # Reward calculated beforehand, and given as input

        # Get the index of the current state
        state_index = tuple(self.q_state)

        # Calculate the next state and get its index
        next_state = self.get_state_q_learning(new_buy_quant, new_sell_quant, new_soc)
        next_state_index = tuple(next_state)

        # Get the index of the action in the actions list
        action = round(action, 2)
        action_index = self.q_actions_CSS.index(action)

        # Retrieve the current q-value from the Q-table
        current_q = self.q_table[state_index + (action_index,)]

        # Calculate the new q-value based on the Bellman equation
        max_future_q = np.max(self.q_table[next_state_index])
        new_q = (1 - self.alpha) * current_q + self.alpha * (reward + self.gamma * max_future_q)

        # Update the Q-table with the new q-value
        self.q_table[state_index + (action_index,)] = new_q

        return self.q_table

