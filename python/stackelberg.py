""" Sequential Stackelberg game for market clearing """

import numpy as np
#import cProfile

from python import opti_bes_stack
from python import opti_bes
from sklearn.preprocessing import MinMaxScaler
from python import opti_bes_last


def initial_price_signal(sell_list):
    '''
    Get initial price signal from sellers

    ***Parameters***

    *'sell_list': Dictionary of sellers and their information
    *'return': Dictionary of sellers and their initial price signals

    '''

    result_price = {}

    # iterate over sellers in sell_list
    for seller, seller_info in sell_list.items():
        initial_price_signal = {}
        building = seller_info["building"]
        bid_price = seller_info["price"]

        initial_price_signal[building] = bid_price
        result_price[seller] = initial_price_signal

    return result_price

def supply_amount(sell_list):

    ''' Get the possible supply amount from sellers

    ***Parameters***

    *'return': available supply of each seller
    '''

    result_quantity = {}

    # iterate over seller in sell_list
    for seller, seller_info in sell_list.items():
        supply_amount = {}
        building = seller_info["building"]
        bid_quantity = seller_info["quantity"]

        supply_amount[building] = bid_quantity
        result_quantity[seller] = supply_amount

    return result_quantity

# define the initial buyer demand
def initial_demand(buy_list):

        ''' Get the initial demand of buyers

        ***Parameters***

        *'buy_list': Dictionary of buyers and their information
        *'return': Dictionary of buyers and their initial demand

        '''

        result_demand = {}

        # iterate over buyers in buy_list
        for buyer, buyer_info in buy_list.items():
            initial_demand = {}
            building = buyer_info["building"]
            bid_quantity = buyer_info["quantity"]

            initial_demand[building] = bid_quantity
            result_demand[buyer] = initial_demand

        return result_demand


def stackelberg_game(buy_list, sell_list, nodes, params, par_rh, building_param, init_val, n_opt, options):

    # Get the time step
    time_steps = par_rh["time_steps"][n_opt][0:4]

    # Dictionary to store results of stackelberg game
    stack_trans_res = {}

    # Small positive constant for stopping criteria
    epsilon = 0.01

    # iteration step size
    l = {}
    sigma = {}

    buyer_list = {}
    seller_list = {}

    # initialize the required dictionaries
    p_transaction = {}
    obj_val_buyer = {}
    obj_val_adj = {}
    net_cost_value = {}
    net_cost = {}
    average_net_cost = {}
    initial_demand_buyer = {}
    total_demand_seller = {}
    actual_trade_seller = {}
    total_revenue_seller = {}
    total_trade_buyer = {}
    demand_buyer = {}
    total_cost_buyer = {}
    power_from_grid = {}
    power_to_grid = {}
    previous_price_signal = {}
    new_price_signal = {}
    opti_stack_res_buyer = {}
    opti_stack_res_seller = {}
    opti_stack_adj = {}

    # Get initial shares for each seller
    share_seller = {}

    ### Get initial price signal and available supply amount of sellers
    #price_signal = {t: {seller["building"]: seller["price"] for seller in sell_list[t].values()} for t in time_steps}
    init_price_signal = {t: {seller["building"]: seller["price"] for seller in sell_list[t].values()} for t in time_steps}
    available_supply = {t: {seller["building"]: seller["quantity"] for seller in sell_list[t].values()} for t in time_steps}
    initial_demand_buyer = {t: {buyer["building"]: buyer["quantity"] for buyer in buy_list[t].values()} for t in time_steps}
    sdr = {t: {seller["building"]: 1 for seller in sell_list[t].values()} for t in time_steps}

    k = {}
    total_initial_sdd = {}
    for t in time_steps:
        total_initial_sdd[t] = sum(initial_demand_buyer[t].values()) - sum(available_supply[t].values())

        k[t] = 0
        l[t] = 0.05
        sigma[t] = 1000

        if total_initial_sdd[t] <= 8000:
            l[t] = 0.05
            sigma[t] = 1000
        elif total_initial_sdd[t] > 8000 and total_initial_sdd[t] <= 12000:
            l[t] = 0.033
            sigma[t] = 1000
        elif total_initial_sdd[t] > 12000 and total_initial_sdd[t] <= 16000:
            l[t] = 0.025
            sigma[t] = 2000
        elif total_initial_sdd[t] > 16000 and total_initial_sdd[t] <= 20000:
            l[t] = 0.02
            sigma[t] = 2500
        elif total_initial_sdd[t] > 20000 and total_initial_sdd[t] <= 24000:
            l[t] = 0.017
            sigma[t] = 3000
        elif total_initial_sdd[t] > 24000 and total_initial_sdd[t] <= 28000:
            l[t] = 0.014
            sigma[t] = 3500
        elif total_initial_sdd[t] > 28000 and total_initial_sdd[t] <= 32000:
            l[t] = 0.012
            sigma[t] = 4000
        elif total_initial_sdd[t] > 32000 and total_initial_sdd[t] <= 36000:
            l[t] = 0.011
            sigma[t] = 4500

    # Case of price signals initialized with same average value
    price_signal = {t: {seller["building"]: (params["eco"]["pr", "el"] + params["eco"]["sell_chp"]) / 2 for seller in sell_list[t].values()} for t in time_steps}

    ### Start Stackelberg game
    for t in time_steps:
        num_sellers = len(sell_list[t])
        share_seller[t] = {seller["building"]: 1 / num_sellers for seller in sell_list[t].values()}
        opti_stack_res_buyer[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        opti_stack_adj[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        p_transaction[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        obj_val_buyer[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        obj_val_adj[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        net_cost_value[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        net_cost[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        total_demand_seller[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        actual_trade_seller[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        total_revenue_seller[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        total_trade_buyer[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        demand_buyer[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        total_cost_buyer[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        power_from_grid[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        power_to_grid[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        previous_price_signal[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        new_price_signal[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        average_net_cost[t] = {}
        stack_trans_res[t] = {}



        if not buy_list[t] or not sell_list[t]:
            stack_trans_res[t] = 0

        else:

            # iterate until stopping criteria: no more price difference between iterations
            while True:

                # iteration counter
                k[t] += 1

                # For each buyer calculate the optimal amount of possible energy trading with each seller
                # Use price_signal from each seller to calculate the optimal transaction amount
                for buyer in buy_list[t].values():
                    for seller in sell_list[t].values():

                        opti_stack_res_buyer[t][buyer["building"]][seller["building"]] = opti_bes_stack.compute_opti_stack(node=nodes[buyer["building"]], params=params,
                                                                                 par_rh=par_rh, building_param=building_param,
                                                                                 init_val=init_val["building_" + str(buyer["building"])],
                                                                                 n_opt=n_opt, options=options,
                                                                                 is_buying=True, price_signal=price_signal,
                                                                                 sdr=sdr, adjust_demand=False, seller=seller["building"]
                                                                                 )

                        # get the optimal transaction amount of each buyer with each seller
                        res_p_trans_buyer_seller = opti_stack_res_buyer[t][buyer["building"]][seller["building"]][-1]
                        p_transaction[t][buyer["building"]][seller["building"]] = res_p_trans_buyer_seller[t]

                        # Get the total objective function value of each buyer with each seller
                        objective_val_buyer = opti_stack_res_buyer[t][buyer["building"]][seller["building"]][11]
                        obj_val_buyer[t][buyer["building"]][seller["building"]] = objective_val_buyer


                # Calculate total demand of buyers from a seller using shares and update the shares for the next iteration
                for seller in sell_list[t].values():
                    total_demand_seller[t][seller["building"]] = share_seller[t][seller["building"]] * sum(p_transaction[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values())

                # Calculate the net cost of buyers from trading with a seller
                # If the available supply of a seller is less than the total demand of buyers from that seller,
                # run the optimization again with adjusted demand
                #for seller in sell_list[t].values():
                    if available_supply[t][seller["building"]] < total_demand_seller[t][seller["building"]]:
                        sdr[t][seller["building"]] = available_supply[t][seller["building"]] / total_demand_seller[t][
                            seller["building"]]
                        # for buyer in buy_list[t].values():
                        #
                        #     opti_stack_adj[t][buyer["building"]][seller["building"]] = opti_bes_stack.compute_opti_stack(node=nodes[buyer["building"]], params=params,
                        #                                                        par_rh=par_rh, building_param=building_param,
                        #                                                        init_val=init_val["building_" + str(buyer["building"])],
                        #                                                        n_opt=n_opt, options=options,
                        #                                                        is_buying=True,
                        #                                                        price_signal=price_signal,
                        #                                                        sdr=sdr, adjust_demand=True, seller=seller["building"])
                        #
                        #     obj_val_adj[t][buyer["building"]][seller["building"]] = opti_stack_adj[t][buyer["building"]][seller["building"]][11]
                        #
                        # net_cost_value[t][seller["building"]] = sum(obj_val_adj[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values())
                    else:
                        sdr[t][seller["building"]] = 1
                        # net_cost[t][seller["building"]] = sum(obj_val_buyer[t][buyer["building"]][seller["building"]] for buyer in buy_list.values())
                        # net_cost_scaled = MinMaxScaler(feature_range=(0, 1)).fit_transform(net_cost)
                    net_cost_value[t][seller["building"]] = sum(obj_val_buyer[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values())

                # Get actual amount traded by the seller
                #for seller in sell_list[t].values():
                    actual_trade_seller[t][seller["building"]] = sum(p_transaction[t][buyer["building"]][seller["building"]] *
                                                                     share_seller[t][seller["building"]] * sdr[t][seller["building"]] for buyer in buy_list[t].values())

                    # total revenue of sellers
                    total_revenue_seller[t][seller["building"]] = price_signal[t][seller["building"]] \
                                                                  * min(available_supply[t][seller["building"]],
                                                                        actual_trade_seller[t][seller["building"]])
                    # and amount to trade with the grid
                    power_to_grid[t][seller["building"]] = (available_supply[t][seller["building"]] -
                                                            min(actual_trade_seller[t][seller["building"]],
                                                                available_supply[t][seller["building"]]))

                # Get the min and max values from net_cost_value dictionary as floats
                max_net_cost = max(net_cost_value[t].values())
                min_net_cost = min(net_cost_value[t].values())

                # Normalize the net cost values
                if max_net_cost == min_net_cost:
                    for seller in sell_list[t].values():
                        net_cost[t][seller["building"]] = 0.5
                else:
                    for seller in sell_list[t].values():
                        net_cost[t][seller["building"]] = (net_cost_value[t][seller["building"]] - min_net_cost) / (
                                    max_net_cost - min_net_cost)

                # Calculate average net cost
                # average_net_cost[t] = sum(share_seller[t][seller["building"]] * net_cost[t][seller["building"]] for seller in sell_list.values())
                average_net_cost[t] = sum(
                    share_seller[t][seller["building"]] * net_cost[t][seller["building"]] for seller in
                    sell_list[t].values())

                for buyer in buy_list[t].values():
                    # for each buyer calculate the total traded amount using optimal transaction amount and shares of sellers
                    total_trade_buyer[t][buyer["building"]] = sum(
                        p_transaction[t][buyer["building"]][seller["building"]] * sdr[t][seller["building"]] *
                        share_seller[t][seller["building"]] for seller in sell_list[t].values())

                    demand_buyer[t][buyer["building"]] = sum(p_transaction[t][buyer["building"]][seller["building"]]  *
                        share_seller[t][seller["building"]] for seller in sell_list[t].values())

                    # total trading cost
                    total_cost_buyer[t][buyer["building"]] = sum(
                        p_transaction[t][buyer["building"]][seller["building"]] * sdr[t][seller["building"]] * share_seller[t][seller["building"]] *
                        price_signal[t][seller["building"]] for seller in sell_list[t].values())
                    # and amount to trade with the grid
                    power_from_grid[t][buyer["building"]] = (initial_demand_buyer[t][buyer["building"]] -
                                                             total_trade_buyer[t][buyer["building"]])
                    # or from opti_bes_stack??
                    # power_from_grid[t][buyer["building"]] = power_demand_buyer[t][buyer["building"]] - total_trade_buyer[t][buyer["building"]]

                # save the result of the transaction amount and price for each buyer and seller
                for buyer in buy_list[t].values():
                    for seller in sell_list[t].values():

                        price = price_signal[t][seller["building"]]
                        quantity = p_transaction[t][buyer["building"]][seller["building"]] * sdr[t][seller["building"]] * share_seller[t][seller["building"]]
                        seller_share = share_seller[t][seller["building"]]
                        init_price = init_price_signal[t][seller["building"]]
                        total_trans_buyer = total_trade_buyer[t][buyer["building"]]
                        init_demand_buyer = initial_demand_buyer[t][buyer["building"]]
                        possible_demand_seller = total_demand_seller[t][seller["building"]]
                        total_trans_seller = actual_trade_seller[t][seller["building"]]
                        available_supply_seller = available_supply[t][seller["building"]]
                        total_trans_cost_buyer = total_cost_buyer[t][buyer["building"]]
                        total_trans_revenue_seller = total_revenue_seller[t][seller["building"]]
                        power_to_buy_from_grid = power_from_grid[t][buyer["building"]]
                        power_to_sell_to_grid = power_to_grid[t][seller["building"]]

                        transaction_key = (buyer["building"], seller["building"])

                        stack_trans_res[t][transaction_key] = {
                            "buyer": buyer["building"],
                            "seller": seller["building"],
                            "price": price,
                            "quantity": quantity,
                            "seller_share": seller_share,
                            "init_price_seller": init_price,
                            "total_trade_buyer": total_trans_buyer,
                            "init_demand_buyer": init_demand_buyer,
                            "possible_demand_seller": possible_demand_seller,
                            "total_demand_seller": total_trans_seller,
                            "available_supply_seller": available_supply_seller,
                            "total_cost_trade_buyer": total_trans_cost_buyer,
                            "total_revenue_trade_seller": total_trans_revenue_seller,
                            "power_from_grid": power_to_buy_from_grid,
                            "power_to_grid": power_to_sell_to_grid,
                        }

                # Update the shares and price signals of sellers
                for seller in sell_list[t].values():
                    # Update shares: if net_cost > average_net_cost, decrease the probability of trading
                    # with that seller, else increase
                    share_seller[t][seller["building"]] = (share_seller[t][seller["building"]] + 0.05 *
                                                           share_seller[t][seller["building"]] *
                                                           (average_net_cost[t] - net_cost[t][seller["building"]]))

                    # Update price: if total demand of buyers from a seller is greater than available supply,
                    # increase the price signal, else decrease

                    # First save the previous price signal
                    previous_price_signal[t][seller["building"]] = price_signal[t][seller["building"]]

                    # Secondly update the price_signal
                    # scale down the available supply and total demand
                    scaling_factor = 0.0001
                    new_price_signal[t][seller["building"]] = (price_signal[t][seller["building"]] + l[t] *
                                                            ((total_demand_seller[t][seller["building"]] -
                                                              available_supply[t][seller["building"]]) * scaling_factor))

                    # if new price signal is smaller/larger than FiT/Grid price, set it to FiT/Grid price
                    new_price_signal[t][seller["building"]] = max((params["eco"]["sell_chp"]+0.001),
                                                               min(new_price_signal[t][seller["building"]],
                                                                   (params["eco"]["pr", "el"]-0.0001)))
                    price_signal[t][seller["building"]] = new_price_signal[t][seller["building"]]

                # Normalize the shares
                total_share = sum(share_seller[t][seller["building"]] for seller in sell_list[t].values())
                share_seller[t] = {seller["building"]: share_seller[t][seller["building"]] /
                                                       total_share for seller in sell_list[t].values()}


                # Stopping criteria: supply demand difference
                if (all(abs(total_demand_seller[t][seller["building"]] - available_supply[t][seller["building"]]) <= sigma[t] for seller in sell_list[t].values())
                or all(abs(price_signal[t][seller["building"]] - previous_price_signal[t][seller["building"]]) <= 0.0001 for seller in sell_list[t].values())
                        or k[t] == 50):
                    for seller in sell_list[t].values():
                        price_signal[t][seller["building"]] = previous_price_signal[t][seller["building"]]

                    break

                # Stopping criteria: SDR
                # if all(sdr[t][seller["building"]] < 0.01 or sdr[t][seller["building"]] >= 0.8 for seller in sell_list[t].values()) or k[t] == 20:
                #     break

                # Stopping criteria: price signal
                # if all(abs(price_signal[t][seller["building"]] - previous_price_signal[t][seller["building"]]) <= epsilon
                #        for seller in sell_list[t].values()) or k[t] == 10:
                #     break
    # Calculate SOC and transaction amount with the grid
    opti_last = {}
    power_imported_grid = {}
    power_exported_grid = {}
    res_soc = {}

    for n in nodes:
        opti_last[n] = opti_bes_last.compute_opti_last(node=nodes[n], params=params,par_rh=par_rh, building_param=building_param,
                                                    init_val = init_val["building_" + str(n)], n_opt=n_opt, options=options, id=n,
                                                    price_signal=price_signal, available_supply=available_supply, trade_buyer=total_trade_buyer, trade_seller=actual_trade_seller,
                                                    trade_cost_buyer=total_cost_buyer, trade_revenue_seller=total_revenue_seller)

        power_imported_grid[n] = opti_last[n][3]
        power_exported_grid[n] = opti_last[n][9]
        res_soc[n] = opti_last[n][1]

    return stack_trans_res, res_soc

#cProfile.run('stackelberg_game(buy_list, sell_list, nodes, params, par_rh, building_param, init_val, n_opt, options)')