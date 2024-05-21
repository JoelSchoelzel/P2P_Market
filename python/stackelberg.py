""" Sequential Stackelberg game for market clearing """

import numpy as np
#import cProfile

from python import opti_bes_stack
from python import opti_bes
from sklearn.preprocessing import MinMaxScaler
from python import opti_bes_last
from collections import defaultdict
from itertools import islice


def recursive_defaultdict(depth):
    # Create a recursive defaultdict
    if depth == 1:
        return defaultdict(float)
    else:
        return defaultdict(lambda: recursive_defaultdict(depth - 1))

def take(n, iterable):
    # Return first n items of the iterable as a dictionary
    return dict(islice(iterable, n))


def stackelberg_game(buy_list, sell_list, nodes, params, par_rh, building_param, init_val, n_opt, options):

    # Get the time step
    if options["block_bids"] == True:
        time_steps = par_rh["time_steps"][n_opt][0:options["block_length"]]
    else:
        time_steps = par_rh["time_steps"][n_opt]

    # Dictionary to store results of stackelberg game
    stack_trans_res = {}

    # Small positive constant for stopping criteria
    epsilon = 0.01

    # iteration step size
    l = {}
    sigma = {}

    init_kum_dem = 0
    res_kum_dem = 0

    end_trans_res = recursive_defaultdict(3)

    # initialize the required dictionaries
    p_transaction = {}
    obj_val_buyer = {}
    obj_val_adj = {}
    net_cost_value = {}
    net_cost = {}
    average_net_cost = {}
    total_demand_seller = {}
    actual_trade_seller = {}
    total_revenue_seller = {}
    total_trade_buyer = {}
    demand_buyer = {}
    total_cost_buyer = {}
    previous_price_signal = {}
    new_price_signal = {}
    opti_stack_res_buyer = {}
    opti_stack_adj = {}
    step_cost_buyer = {}

    #end_trans_res = {}
    resulting_trade_seller = {}
    resulting_rev_seller = {}
    resulting_trade_buyer = {}
    resulting_cost_buyer = {}
    tot_dem_sel = {}
    new_sdr = {t: {seller["building"]: 1 for seller in sell_list[t].values()} for t in time_steps}

    # Get initial shares for each seller
    share_seller = {}

    ### Get initial price signal and available supply amount of sellers
    #price_signal = {t: {seller["building"]: seller["price"] for seller in sell_list[t].values()} for t in time_steps}
    init_price_signal = {t: {seller["building"]: seller["price"] for seller in sell_list[t].values()} for t in time_steps}
    available_supply = {t: {seller["building"]: seller["quantity"] for seller in sell_list[t].values()} for t in time_steps}
    initial_demand_buyer = {t: {buyer["building"]: buyer["quantity"] for buyer in buy_list[t].values()} for t in time_steps}
    sdr = {t: {seller["building"]: 1 for seller in sell_list[t].values()} for t in time_steps}

    last_time = {}
    for t in buy_list:
        for buyer in buy_list[t].values():
            # Update the last time step where this buyer was seen
            last_time[buyer["building"]] = t

    last_time_seller = {}
    for t in sell_list:
        for seller in sell_list[t].values():
            # Update the last time step where this seller was seen
            last_time_seller[seller["building"]] = t




    k = {}
    total_initial_sdd = {}
    for t in time_steps:
        total_initial_sdd[t] = sum(initial_demand_buyer[t].values()) - sum(available_supply[t].values())

        k[t] = 0
        l[t] = 0.05
        sigma[t] = 500

        # if total_initial_sdd[t] <= 8000:
        #     l[t] = 0.05
        #     sigma[t] = 1000
        # elif total_initial_sdd[t] > 8000 and total_initial_sdd[t] <= 12000:
        #     l[t] = 0.033
        #     sigma[t] = 1000
        # elif total_initial_sdd[t] > 12000 and total_initial_sdd[t] <= 16000:
        #     l[t] = 0.025
        #     sigma[t] = 2000
        # elif total_initial_sdd[t] > 16000 and total_initial_sdd[t] <= 20000:
        #     l[t] = 0.02
        #     sigma[t] = 2500
        # elif total_initial_sdd[t] > 20000 and total_initial_sdd[t] <= 24000:
        #     l[t] = 0.017
        #     sigma[t] = 3000
        # elif total_initial_sdd[t] > 24000 and total_initial_sdd[t] <= 28000:
        #     l[t] = 0.014
        #     sigma[t] = 3500
        # elif total_initial_sdd[t] > 28000 and total_initial_sdd[t] <= 32000:
        #     l[t] = 0.012
        #     sigma[t] = 4000
        # elif total_initial_sdd[t] > 32000 and total_initial_sdd[t] <= 36000:
        #     l[t] = 0.011
        #     sigma[t] = 4500

    # Case of price signals initialized with same average value
    price_signal = {t: {seller["building"]: (params["eco"]["pr", "el"] + params["eco"]["sell_pv"]) / 2 for seller in sell_list[t].values()} for t in time_steps}

    ### Start Stackelberg game
    for t in time_steps:
        num_sellers = len(sell_list[t])
        share_seller[t] = {seller["building"]: 1 / num_sellers for seller in sell_list[t].values()}
        opti_stack_res_buyer[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        opti_stack_adj[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        p_transaction[t] = {buyer["building"]: {seller["building"]: 0.0 for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        obj_val_buyer[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        obj_val_adj[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}
        net_cost_value[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        net_cost[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        total_demand_seller[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        actual_trade_seller[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        total_revenue_seller[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        total_trade_buyer[t] = {buyer["building"]: 0.0 for buyer in buy_list[t].values()}
        demand_buyer[t] = {buyer["building"]: 0.0 for buyer in buy_list[t].values()}
        total_cost_buyer[t] = {buyer["building"]: 0.0 for buyer in buy_list[t].values()}
        # power_from_grid[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        # power_to_grid[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        previous_price_signal[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        new_price_signal[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        average_net_cost[t] = {}
        stack_trans_res[t] = {}
        step_cost_buyer[t] = {buyer["building"]: {seller["building"]: {} for seller in sell_list[t].values()} for buyer in buy_list[t].values()}

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

                        # get the optimal transaction amount after the last time_step
                        if t == last_time[buyer["building"]] or t == last_time_seller[seller["building"]]:
                            end_trans = opti_stack_res_buyer[t][buyer["building"]][seller["building"]][-1]
                            end_trans_res[buyer["building"]][seller["building"]] = take(4,end_trans.items())

                        # Get the total objective function value of each buyer with each seller
                        objective_val_buyer = opti_stack_res_buyer[t][buyer["building"]][seller["building"]][11]
                        obj_val_buyer[t][buyer["building"]][seller["building"]] = objective_val_buyer

                        # Get the resulting cost at considered time step for each buyer
                        cost_buyer = opti_stack_res_buyer[t][buyer["building"]][seller["building"]][-2]
                        step_cost_buyer[t][buyer["building"]][seller["building"]] = cost_buyer[t]

                # Calculate total demand of buyers from a seller using shares and update the shares for the next iteration
                for seller in sell_list[t].values():
                    total_demand_seller[t][seller["building"]] = (share_seller[t][seller["building"]] *
                                                                  sum(p_transaction[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values()))

                # Calculate the net cost of buyers from trading with a seller
                    # if available supply is less than total demand, save the supply demand ratio
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
                    # net_cost_value[t][seller["building"]] = sum(obj_val_buyer[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values())
                    net_cost_value[t][seller["building"]] = sum(step_cost_buyer[t][buyer["building"]][seller["building"]] for buyer in buy_list[t].values())

                # Get actual amount traded by the seller at the considered time step
                #for seller in sell_list[t].values():
                    actual_trade_seller[t][seller["building"]] = sum(p_transaction[t][buyer["building"]][seller["building"]] *
                                                                     share_seller[t][seller["building"]] * sdr[t][seller["building"]] for buyer in buy_list[t].values())

                    # total revenue of sellers
                    total_revenue_seller[t][seller["building"]] = price_signal[t][seller["building"]] \
                                                                  * min(available_supply[t][seller["building"]],
                                                                        actual_trade_seller[t][seller["building"]])

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

                # save the result of the transaction amount and price for each buyer and seller
                for buyer in buy_list[t].values():
                    for seller in sell_list[t].values():
                        seller_share = share_seller[t][seller["building"]]
                        price = price_signal[t][seller["building"]]
                        quantity = p_transaction[t][buyer["building"]][seller["building"]] * sdr[t][seller["building"]] * share_seller[t][seller["building"]]


                        transaction_key = (buyer["building"], seller["building"])
                        stack_trans_res[t][transaction_key] = {
                            "buyer": buyer["building"],
                            "seller": seller["building"],
                            "seller_share": seller_share,
                            "price": price,
                            "quantity": quantity
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
                    new_price_signal[t][seller["building"]] = max((params["eco"]["sell_pv"]+0.001),
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
                        or k[t] == 20):
                    for seller in sell_list[t].values():
                        price_signal[t][seller["building"]] = previous_price_signal[t][seller["building"]]

                    # print t and k[t]
                    print("Time step: ", t)
                    print("Number of iterations: ", k[t])
                    break

                # Stopping criteria: price signal
                # if all(abs(price_signal[t][seller["building"]] - previous_price_signal[t][seller["building"]]) <= epsilon
                #        for seller in sell_list[t].values()) or k[t] == 10:
                #     break
    results = []

    for t in time_steps:
        resulting_trade_seller[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        resulting_rev_seller[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}
        resulting_trade_buyer[t] = {buyer["building"]: 0.0 for buyer in buy_list[t].values()}
        resulting_cost_buyer[t] = {buyer["building"]: 0.0 for buyer in buy_list[t].values()}
        tot_dem_sel[t] = {seller["building"]: 0.0 for seller in sell_list[t].values()}

        print("Time step2: ", t)
        if t == 4565:
            print("Stop here")
        if not buy_list[t] or not sell_list[t]:
            pass

        else:

            for seller in sell_list[t].values():
                # tot_dem_sel[t][seller["building"]] = (share_seller[t][seller["building"]] * sum(end_trans_res[buyer["building"]][seller["building"]][t] for buyer in buy_list[t].values()))
                share_sel = share_seller[t][seller["building"]]
                if not isinstance(share_sel, (int, float)):
                    print(f"Share is not a number: {share_sel} (type: {type(share_sel)})")
                    continue

                trade_sum_seller = 0.0
                for buyer in buy_list[t].values():
                    end_val = end_trans_res[buyer["building"]][seller["building"]][t]
                    if isinstance(end_val, (int, float)):
                        trade_sum_seller += end_val

                    else:
                        results.append(f"Unexpected value encountered: {end_val} (type: {type(end_val)})")

                tot_dem_sel[t][seller["building"]] = share_sel * trade_sum_seller

                if available_supply[t][seller["building"]] < tot_dem_sel[t][seller["building"]]:
                    new_sdr[t][seller["building"]] = available_supply[t][seller["building"]] / tot_dem_sel[t][
                        seller["building"]]
                else:
                    new_sdr[t][seller["building"]] = 1

                resulting_trade_seller[t][seller["building"]] = \
                    sum(end_trans_res[buyer["building"]][seller["building"]][t] *
                        share_seller[t][seller["building"]] * new_sdr[t][seller["building"]] for buyer in buy_list[t].values())

                resulting_rev_seller[t][seller["building"]] = (price_signal[t][seller["building"]] *
                                                               min(available_supply[t][seller["building"]],
                                                                   resulting_trade_seller[t][seller["building"]]))

            for buyer in buy_list[t].values():
                resulting_trade_buyer[t][buyer["building"]] = sum(
                    end_trans_res[buyer["building"]][seller["building"]][t] * new_sdr[t][seller["building"]] *
                    share_seller[t][seller["building"]] for seller in sell_list[t].values())

                resulting_cost_buyer[t][buyer["building"]] = sum(
                    end_trans_res[buyer["building"]][seller["building"]][t] *
                    new_sdr[t][seller["building"]] * share_seller[t][seller["building"]] * price_signal[t][
                        seller["building"]] for seller in sell_list[t].values())

    # Calculate SOC and transaction amount with the grid
    opti_last = {}
    power_imported_grid = {}
    power_exported_grid = {}
    res_soc = {}
    res_total_dem = {}
    res_total_sup_chp = {}
    res_total_sup_pv = {}

    for n in nodes:
        opti_last[n] = opti_bes_last.compute_opti_last(node=nodes[n], params=params,par_rh=par_rh, building_param=building_param,
                                                       init_val=init_val["building_" + str(n)], n_opt=n_opt, options=options,
                                                       id=n, price_signal=price_signal, available_supply=available_supply,
                                                       trade_buyer=resulting_trade_buyer, trade_seller=resulting_trade_seller,
                                                       trade_cost_buyer=resulting_cost_buyer, trade_revenue_seller=resulting_rev_seller)

        power_imported_grid[n] = opti_last[n][3]
        power_exported_grid[n] = opti_last[n][9]
        res_soc[n] = opti_last[n][1]
        res_total_dem[n] = opti_last[n][2]
        res_total_sup_chp[n] = opti_last[n][8]["chp"]
        res_total_sup_pv[n] = opti_last[n][8]["pv"]


    buyer_trans_info = {}
    seller_trans_info = {}
    total_market_info = {}
    total_market_demand = {}
    total_market_supply = {}
    for t in time_steps:
        buyer_trans_info[t] = {}
        seller_trans_info[t] = {}
        total_purchase_market = 0
        total_purchase_grid = 0
        total_sold_market = 0
        total_sold_grid = 0

        if not buy_list[t] or not sell_list[t]:
            buyer_trans_info[t] = 0
            seller_trans_info[t] = 0
            total_market_info[t] = 0

        else:

            for buyer in buy_list[t].values():
                total_purchase_market += resulting_trade_buyer[t][buyer["building"]]
                total_purchase_grid += power_imported_grid[buyer["building"]][t]

                total_trans_buyer = resulting_trade_buyer[t][buyer["building"]]
                total_trans_cost_buyer = resulting_cost_buyer[t][buyer["building"]]
                power_from_grid = power_imported_grid[buyer["building"]][t]
                saved_cost= sum(
                            end_trans_res[buyer["building"]][seller["building"]][t] * sdr[t][seller["building"]] * share_seller[t][seller["building"]] *
                            (params["eco"]["pr", "el"] - price_signal[t][seller["building"]]) for seller in sell_list[t].values())
                soc_bat_buyer = res_soc[buyer["building"]]["bat"][t]
                soc_tes_buyer = res_soc[buyer["building"]]["tes"][t]

                init_dem_buyer = initial_demand_buyer[t][buyer["building"]]
                res_dem_buyer = res_total_dem[buyer["building"]][t]

                init_kum_dem += init_dem_buyer
                res_kum_dem += res_dem_buyer

                buyer_trans_info[t][buyer["building"]] = {
                    "total_trade_buyer": total_trans_buyer,
                    "total_cost_trade_buyer": total_trans_cost_buyer,
                    "power_from_grid": power_from_grid,
                    "saved_cost": saved_cost,
                    "soc_bat_buyer": soc_bat_buyer,
                    "soc_tes_buyer": soc_tes_buyer,
                    "init_dem_buyer": init_dem_buyer,
                    "res_dem_buyer": res_dem_buyer
                }

            for seller in sell_list[t].values():
                total_sold_market += resulting_trade_seller[t][seller["building"]]
                total_sold_grid += power_exported_grid[seller["building"]][t]

                seller_price = price_signal[t][seller["building"]]
                seller_share = share_seller[t][seller["building"]]
                available_supply_seller = available_supply[t][seller["building"]]
                possible_demand_seller = total_demand_seller[t][seller["building"]]
                total_trans_seller = resulting_trade_seller[t][seller["building"]]
                total_trans_revenue_seller = resulting_rev_seller[t][seller["building"]]
                power_to_grid = power_exported_grid[seller["building"]][t]
                gained_revenue = resulting_trade_seller[t][seller["building"]] * (price_signal[t][seller["building"]] - params["eco"]["sell_pv"])
                soc_bat_seller = res_soc[seller["building"]]["bat"][t]
                soc_tes_seller = res_soc[seller["building"]]["tes"][t]

                seller_trans_info[t][seller["building"]] = {
                    "seller_price": seller_price,
                    "seller_share": seller_share,
                    "available_supply_seller": available_supply_seller,
                    "possible_demand_seller": possible_demand_seller,
                    "total_demand_seller": total_trans_seller,
                    "total_revenue_trade_seller": total_trans_revenue_seller,
                    "power_to_grid": power_to_grid,
                    "gained_revenue": gained_revenue,
                    "soc_bat_seller": soc_bat_seller,
                    "soc_tes_seller": soc_tes_seller
                }

            total_market_demand[t] = sum(res_total_dem[buyer["building"]][t] for buyer in buy_list[t].values())
            total_market_supply[t] = sum((res_total_sup_pv[seller["building"]][t] + res_total_sup_chp[seller["building"]][t]) for seller in sell_list[t].values())

            total_market_info[t] = {
                "total_purchase_market": total_purchase_market,
                "total_purchase_grid": total_purchase_grid,
                "total_sold_market": total_sold_market,
                "total_sold_grid": total_sold_grid,
                "price_update_step_size": l[t],
                "stopping_crit": sigma[t],
                "num_iter": k[t],
                "init_kum_dem": init_kum_dem,
                "res_kum_dem": res_kum_dem
            }









    return stack_trans_res, buyer_trans_info, seller_trans_info, total_market_info, res_soc

