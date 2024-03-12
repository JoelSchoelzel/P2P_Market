""" Sequential Stackelberg game for market clearing """

import numpy as np

from python import opti_bes_stack
from python import opti_bes
from sklearn.preprocessing import MinMaxScaler


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

    stack_trans_res = {}

    # Small positive constant for stopping criteria
    epsilon = 0.01

    # iteration step size
    l = 0.05

    # initialize the required dictionaries
    p_transaction = {}
    net_cost = {}
    total_demand_seller = {}
    total_revenue_seller = {}
    total_trade_buyer = {}
    total_cost_buyer = {}
    power_from_grid = {}
    power_to_grid = {}
    opti_stack_res_buyer = {}
    opti_stack_res_seller = {}

    # Get initial shares for each seller
    num_sellers = len(sell_list)
    share_seller = {seller["building"]: 1 / num_sellers for seller in sell_list.values()}

    # Get initial price signal and available supply amount of sellers
    #price_signal = initial_price_signal(sell_list)
    #available_supply = supply_amount(sell_list)

    ### Alternative way to get the initial price signal and available supply amount of sellers
    price_signal = {seller["building"]: seller["price"] for seller in sell_list.values()}
    available_supply = {seller["building"]: seller["quantity"] for seller in sell_list.values()}

    # Get initial demand of buyers
    # initial_demand_buyer = initial_demand(buy_list)

    ### Alternative way to get the initial demand of buyers
    initial_demand_buyer = {buyer["building"]: buyer["quantity"] for buyer in buy_list.values()}


    ### Start Stackelberg game

    # iterate until stopping criteria: when available amount of each seller is equal to demanded amount of buyers from that seller
    while True:

        # For each buyer calculate the optimal amount of possible energy trading with each seller
        # Use price_signal from each seller to calculate the optimal transaction amount
        for buyer in buy_list.values():
            for seller in sell_list.values():

                opti_stack_res_buyer = opti_bes_stack.compute_opti_stack(node=nodes[buyer["building"]], params=params,
                                                                         par_rh=par_rh, building_param=building_param,
                                                                         init_val=init_val, n_opt=n_opt, options=options,
                                                                         buy_list=buy_list, sell_list=sell_list,
                                                                         is_buying=True, price_signal=price_signal[seller["building"]],
                                                                         )

                # get the optimal transaction amount of each buyer with each seller
                p_transaction[buyer["building"]][seller["building"]] = opti_stack_res_buyer["res_p_transaction_buyer_seller"]

                # for each buyer calculate the total traded amount using optimal transaction amount and shares of sellers
                total_trade_buyer[buyer["building"]] = sum(p_transaction[buyer["building"]][seller["building"]] * share_seller[seller["building"]])
                # total trading cost
                total_cost_buyer[buyer["building"]] = total_trade_buyer[buyer["building"]] * price_signal[seller["building"]]
                # and amount to trade with the grid
                power_from_grid[seller["building"]] = initial_demand_buyer[buyer["building"]] - total_trade_buyer[buyer["building"]]

                # Calculate the net cost of buyers from trading with a seller
                net_cost[seller["building"]] += opti_stack_res_buyer["objVal"]
                #scaled_data = MinMaxScaler(feature_range=(0, 1)).fit_transform(net_cost)

        # Calculate average net cost
        average_net_cost = sum(share_seller[seller["building"]] * net_cost[seller["building"]] for seller in sell_list.values())

        # Calculate total demand of buyers from a seller using shares and update the shares for the next iteration
        for seller in sell_list.values():
            total_demand_seller[seller["building"]] = share_seller[seller["building"]] * sum(p_transaction[buyer["building"]][seller["building"]] for buyer in buy_list.values())
            # total revenue of sellers
            total_revenue_seller[seller["building"]] = price_signal[seller["building"]] * total_demand_seller[seller["building"]]
            # and amount to trade with the grid
            power_to_grid[seller["building"]] = available_supply[seller["building"]] - total_demand_seller[seller["building"]]



        # save the result of the transaction amount and price for each buyer and seller
        for buyer in buy_list.values():
            for seller in sell_list.values():

                transaction_key = (buyer["building"], seller["building"])

                stack_trans_res[transaction_key] = {
                    "buyer": buyer["building"],
                    "seller": seller["building"],
                    "price": price_signal[seller["building"]],
                    "quantity": p_transaction[buyer["building"]][seller["building"]] * share_seller[seller["building"]],
                    "total_trade_buyer": total_trade_buyer[buyer["building"]],
                    "total_trade_seller": total_demand_seller[seller["building"]],
                    "cost_trade_buyer": total_cost_buyer[buyer["building"]],
                    "revenue_trade_seller": total_revenue_seller[seller["building"]],
                    "power_from_grid": power_from_grid[seller["building"]],
                    "power_to_grid": power_to_grid[seller["building"]],
                }

        for seller in sell_list.values():
            # if net_cost > average_net_cost, decrease the probability of trading with that seller, else increase
            share_seller[seller["building"]] = share_seller[seller["building"]] + l * share_seller[seller["building"]] * (average_net_cost - net_cost[seller["building"]])

            # Use the total demand from sellers to update the price signal of that seller
            price_signal[seller["building"]] = price_signal[seller["building"]] + l * (available_supply[seller["building"]] - total_demand_seller[seller["building"]])

        if all(abs(total_demand_seller[seller["building"]] - available_supply[seller["building"]]) <= epsilon for seller in sell_list.values()):

            break

    return stack_trans_res




       #         # resulting totals of each participant
       #         "trans_revenue_seller": price_signal[seller] * total_demand_seller[seller],
       #         "trans_cost_buyer": price_signal[seller] * total_trade_buyer[buyer],
       #         "power_to_grid": available_supply[seller] - total_demand_seller[seller],
       #         "power_from_grid": initial_demand_buyer[buyer] - total_trade_buyer[buyer],
       #         "opti_stack_res_buyer": opti_stack_res_buyer[buyer],
       #         "opti_stack_res_seller": opti_stack_res_seller[seller],







        #    # save the result of the objective function for sellers with the resulting price signal and demand
        #    seller_building = sell_list[seller]["building"]
        #    opti_stack_res_seller = opti_bes_stack.compute_opti_stack(node=seller_building, params=params,
        #                                                              par_rh=par_rh, building_param=building_param,
        #                                                              init_val=init_val, n_opt=n_opt,
        #                                                              options=options,
        #                                                              buy_list=buy_list, sell_list=sell_list,
        #                                                              is_buying=False,
        #                                                              transaction_price=price_signal[seller],
        #                                                              demand_from_seller=total_demand_seller[seller])

