from python import opti_bes_negotiation
from python import characs_single_build
import random
import copy
import numpy as np

from python.last_opti import compute_last_opti

random.seed(42)


def matching(sorted_block_bids):
    """Match the sorted block bids of the buyers to the ones of the sellers.
    Returns:
        matched_bids_info (list): List of all matched block_bids in tuples.
        Each tuple contains a dict (key [O]= buyer, [1]= seller).
        Buyer and seller each have a dict (time steps t as key) which contains a
        list [price, quantity, buying:True/False/None, building_id]"""

    # Create a list of tuples where each tuple contains matched buy and sell bids (1st buy bid matches with 1st
    # sell bid, 2nd buy bid matches with 2nd sell bid, etc.)
    if len(sorted_block_bids["buy_blocks"]) != 0 and len(sorted_block_bids["sell_blocks"]) != 0:
        matched_bids_info = list(zip(sorted_block_bids["buy_blocks"], sorted_block_bids["sell_blocks"]))

    else:
        matched_bids_info = []
        print("No matched bids for this optimization period.")

    return matched_bids_info


def negotiation(nodes, params, par_rh, init_val, n_opt, options, matched_bids_info, sorted_bids, block_length,
                opti_res):
    """Run the optimization problem for the negotiation phase (taking into account
    bid quantities and prices of matched peer).

    Returns:
        nego_transactions (dict): Dictionary containing the results of the negotiation phase for each match.
        total_market_info (dict): Dictionary containing the results of the total market (all matched and unmatched peers).
        last_time_step (int): Last time step of the optimization horizon.

        nego_transactions, participating_buyers, participating_sellers, sorted_bids_nego, last_time_step, matched_bids_info_nego
        """

    # Get the time steps of the block bid
    block_bid_time_steps = par_rh["time_steps"][n_opt][0:block_length]
    last_time_step = block_bid_time_steps[-1]

    # Initialize variables for the negotiation phase
    r = 0  # trading rounds
    max_rounds = 10  # maximum number of trading rounds

    # Dicts to store results
    sorted_bids_nego = {r: sorted_bids}
    matched_bids_info_nego = {r: matched_bids_info}
    nego_transactions = {r: {}}

    # Initialize a set to keep track of buildings that participated in negotiations
    participating_buildings = set()
    participating_buyers = set()
    participating_sellers = set()

    # --------------------- START NEGOTIATION ---------------------

    # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
    while len(sorted_bids_nego[r]["sell_blocks"]) > 0 and len(sorted_bids_nego[r]["buy_blocks"]) > 0 and r < max_rounds:

        # create new variables for the next trading round
        sorted_bids_nego[r + 1] = {"buy_blocks": [], "sell_blocks": []}
        matched_bids_info_nego[r + 1] = []
        nego_transactions[r + 1] = {}

        # buyer and seller of each match run their optimization model
        # until their price_trade difference to average price is less than 0.005
        for match in range(len(matched_bids_info_nego[r])):
            nego_transactions[r][match] = {}
            add_buy_bid = False
            add_sell_bid = False
            new_remaining_demand = {}
            new_remaining_supply = {}
            trade_power = {}
            trade_price = {}
            buyer_bid_prices = {}
            seller_bid_prices = {}
            saved_costs = {}
            additional_revenue = {}
            remaining_demand = {}
            remaining_supply = {}
            diff_buyer_seller = {}
            opti_bes_res_buyer = {}
            opti_bes_res_seller = {}
            buyer_id = matched_bids_info_nego[r][match][0]["bes_id"]
            seller_id = matched_bids_info_nego[r][match][1]["bes_id"]
            participating_buyers.add(buyer_id)
            participating_sellers.add(seller_id)
            participating_buildings.add(buyer_id)
            participating_buildings.add(seller_id)

            """
                # get the price and quantity of the matched bids for flex price delta
                price_bid_buyer = matched_bids_info_nego[r][match][0][t][0]
                price_bid_seller = matched_bids_info_nego[r][match][1][t][0]
                flex_buyer_forced = matched_bids_info_nego[r][match][0]["flex_energy_forced"]
                flex_seller_forced = matched_bids_info_nego[r][match][1]["flex_energy_forced"]
                flex_buyer_delayed = matched_bids_info_nego[r][match][0]["flex_energy_delayed"]
                flex_seller_delayed = matched_bids_info_nego[r][match][1]["flex_energy_delayed"]
                
                diff_buyer_seller_price = abs(price_bid_buyer - price_bid_seller)
                # step_scale = s in MA-Text?!
                step_scale = 1
                # step size = k_step
                k_step = step_scale * diff_buyer_seller_price
                #
                x_top = 1
                x_bottom = -1
                if max(flex_buyer_delayed, flex_seller_delayed) > 0:
                    norm_flex_b = scaling_bottom + (scaling_top - scaling_bottom) * (
                                (flex_buyer_delayed - min(flex_buyer_delayed, flex_seller_delayed)) / (
                                    max(flex_buyer_delayed, flex_seller_delayed) - min(flex_buyer_delayed,
                                                                                       flex_seller_delayed)))
                else:
                    norm_flex_b = 0

                sigmoid_b = 1 / (1 + np.exp(-norm_flex_b))

                delta_price_buyer  = k_step * (1 - sigmoid_b)
                delta_price_seller = k_step * sigmoid_b

                if diff_buyer_seller[t] <= 0.05:
                    diff_buyer_seller[t] = 0.06

                if options["flex_price_delta"]:
                    while diff_buyer_seller[t] > 0.001:
                        opti_bes_res_buyer \
                            = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                                                init_val=init_val["building_" + str(buyer_id)],
                                                                n_opt=n_opt, options=options,
                                                                matched_bids_info=matched_bids_info_nego[r][match],
                                                                is_buying=True,
                                                                delta_price=buyer_delta, block_length=block_length,
                                                                delta_price_seller=seller_delta)
                        opti_bes_res_seller \
                            = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                                init_val=init_val["building_" + str(seller_id)],
                                                                n_opt=n_opt, options=options,
                                                                matched_bids_info=matched_bids_info_nego[r][match],
                                                                is_buying=False,
                                                                delta_price=buyer_delta, block_length=block_length,
                                                                delta_price_seller=seller_delta)

                        buyer_trade_price[t] = opti_bes_res_buyer["res_price_trade"][t]
                        seller_trade_price[t] = opti_bes_res_seller["res_price_trade"][t]
                        diff_buyer_seller[t] = abs(buyer_trade_price[t] - seller_trade_price[t])
                        # update delta price
                        seller_delta += seller_delta
                        buyer_delta += buyer_delta

                elif not options["flex_price_delta"]:
                """
            #### run the optimization model for buyer and seller ###
            # price adjustment for negotiation with x% of price range
            delta_price = (params["eco"]["pr", "el"] - params["eco"]["sell_pv"]) * 0.1
            # set fake price differences of buyers and sellers bids to ensure at least one negotiation/optimization
            diff_bid_prices = [-1] * len(block_bid_time_steps)
            # number of negotiation between two traders
            i = 0
            # negotiation ends when all buyer bid prices > seller bid prices
            # todo: delta_prices in abh. der Gebotsmengen und deren Differenzen
            while min(diff_bid_prices) < 0:
                opti_bes_res_buyer \
                    = opti_bes_negotiation.compute_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                                        init_val=init_val["building_" + str(buyer_id)],
                                                        n_opt=n_opt, options=options,
                                                        matched_bids_info=matched_bids_info_nego[r][match],
                                                        is_buying=True, delta_price=delta_price,
                                                        block_length=block_length)
                opti_bes_res_seller \
                    = opti_bes_negotiation.compute_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                                        init_val=init_val["building_" + str(seller_id)],
                                                        n_opt=n_opt, options=options,
                                                        matched_bids_info=matched_bids_info_nego[r][match],
                                                        is_buying=False, delta_price=delta_price,
                                                        block_length=block_length)

                diff_bid_prices = {}
                for t in block_bid_time_steps:
                    # update difference of buyers und sellers bid prices for loop check
                    diff_bid_prices[t] = opti_bes_res_buyer["res_price_trade"][t] - opti_bes_res_seller["res_price_trade"][t]
                    # update delta price

                # += since in the opti are always taken the bid prices as input
                delta_price = delta_price + (params["eco"]["pr", "el"] - params["eco"]["sell_pv"]) * 0.1

                i = i + 1

            # ---------- RESULTS OF NEGOTIATION FOR THIS MATCH AND THIS ROUND ---------- #
            # todo: in while Schleife oder danach? Gedanke: danach damit Berechnungen nur für den Fall durchgeführt
            # werden, dass prices buy > prices sell
            for t in block_bid_time_steps:
                    # initialize variables
                    trade_power[t] = {}
                    saved_costs[t] = 0
                    additional_revenue[t] = 0
                    saved_costs_sum = 0
                    additional_rev_sum = 0
                    #trade_price_sum = 0

                    # Set trade power and trade price of this match

                    # if there is more supply than demand, the buyer can buy more than he initially wanted
                    #
                    buyer_bid = matched_bids_info_nego[r][match][0][t][1] # bid quantity of buyer
                    seller_bid = matched_bids_info_nego[r][match][1][t][1] # bid quantity of seller
                    if (seller_bid >= buyer_bid and
                            buyer_bid <= opti_bes_res_buyer["res_power_trade"][t] <= seller_bid):
                        if isinstance(matched_bids_info_nego[r][match][0][t], list) and isinstance(
                                matched_bids_info_nego[r][match][1][t], list):
                            trade_power[t] = max(opti_bes_res_buyer["res_power_trade"][t],
                                                opti_bes_res_seller["res_power_trade"][t])
                    # also if there is more demand than supply, the seller can sell more than he initially wanted
                    # todo: wegen flexi?
                    elif (buyer_bid >= seller_bid and
                        seller_bid <= opti_bes_res_seller["res_power_trade"][t] <= buyer_bid):
                        if isinstance(matched_bids_info_nego[r][match][0][t], list) and isinstance(
                                matched_bids_info_nego[r][match][1][t], list):
                            trade_power[t] = max(opti_bes_res_buyer["res_power_trade"][t],
                                                opti_bes_res_seller["res_power_trade"][t])
                    else:
                        trade_power[t] = min(opti_bes_res_buyer["res_power_trade"][t],
                                            opti_bes_res_seller["res_power_trade"][t])

                    # trade_price[t] = (buyer_trade_price[t] + seller_trade_price[t]) / 2
                    trade_price[t] = (opti_bes_res_buyer["res_price_trade"][t]
                                    + opti_bes_res_seller["res_price_trade"][t])/2

                    #trade_price_sum += trade_price[t]

                    # calculate the saved costs for this match compared to trading with grid
                    saved_costs[t] = trade_power[t] * abs(params["eco"]["pr", "el"] - trade_price[t])
                    saved_costs_sum += saved_costs[t]

                    # calculate the additional revenue for this match compared to trading with grid
                    # todo: gibt nur ein p_min
                    if opti_res[seller_id][8]["pv"][t] > 1e-4:
                        additional_revenue[t] = trade_power[t] * abs(trade_price[t] - params["eco"]["sell" + "_" + "pv"])
                    elif opti_res[seller_id][8]["chp"][t] > 1e-4:
                        additional_revenue[t] = trade_power[t] * abs(trade_price[t] - params["eco"]["sell" + "_" + "chp"])
                    additional_rev_sum += additional_revenue[t]

                    # calculate demand & supply that haven't been fulfilled
                    remaining_demand[t] = abs(buyer_bid - trade_power[t])
                    remaining_supply[t] = abs(seller_bid - trade_power[t])

                    if remaining_demand[t] > 1e-3 and not add_buy_bid:
                        add_buy_bid = True

                    if remaining_supply[t] > 1e-3 and not add_sell_bid:
                        add_sell_bid = True

            # todo: wird diese Opti überhaupt noch benötigt? Preise sind ja zuvor fest ( == in Opti)
            # run the last optimization with agreed power and price for trade to receive storage soc
            opti_bes_res_buyer \
                = compute_last_opti(node=nodes[buyer_id], params=params, par_rh=par_rh,
                                    init_val=init_val["building_" + str(buyer_id)],
                                    n_opt=n_opt, options=options,
                                    # todo: wofür wird das noch gebracht, wenn trade power und price input sind?
                                    matched_bids_info=matched_bids_info_nego[r][match],
                                    is_buying=True,
                                    block_length=block_length,
                                    power_trade_final=trade_power,
                                    price_trade_final=trade_price)
            opti_bes_res_seller \
                = compute_last_opti(node=nodes[seller_id], params=params, par_rh=par_rh,
                                    init_val=init_val["building_" + str(seller_id)],
                                    n_opt=n_opt, options=options,
                                    matched_bids_info=matched_bids_info_nego[r][match],
                                    is_buying=False,
                                    block_length=block_length,
                                    power_trade_final=trade_power,
                                    price_trade_final=trade_price)

            new_total_price = 0
            count = 0
            new_sum_energy = 0
            res_soc_buyer = opti_bes_res_buyer["res_soc"]["tes"]
            res_soc_seller = opti_bes_res_seller["res_soc"]["tes"]

            # add unsatisfied buyers and sellers to next trading round with remaining demand/supply
            if add_buy_bid:
                copy_of_buy_bid = copy.deepcopy(matched_bids_info_nego[r][match][0])
                for t in block_bid_time_steps:
                    # Subtract the traded power from the original demand to get the new remaining demand
                    new_remaining_demand[t] = max(0, copy_of_buy_bid[t][1] - trade_power[t])
                    copy_of_buy_bid[t][1] = new_remaining_demand[t]
                    new_total_price += copy_of_buy_bid[t][0]
                    count += 1
                    new_sum_energy += copy_of_buy_bid[t][1]

                new_mean_quantity = new_sum_energy / count if count > 0 else 0
                copy_of_buy_bid["mean_quantity"] = new_mean_quantity
                copy_of_buy_bid["sum_energy"] = new_sum_energy
                copy_of_buy_bid["total_price"] = new_total_price
                new_flex_delayed, new_flex_forced = characs_single_build.calc_characs_single(nodes=nodes,
                                                                                             block_length=block_length,
                                                                                             bes_id=buyer_id,
                                                                                             soc_state=res_soc_buyer)
                copy_of_buy_bid["flex_energy_delayed"] = new_flex_delayed
                copy_of_buy_bid["flex_energy_forced"] = new_flex_forced
                sorted_bids_nego[r + 1]["buy_blocks"].append(copy_of_buy_bid)

            if add_sell_bid:
                copy_of_sell_bid = copy.deepcopy(matched_bids_info_nego[r][match][1])
                for t in block_bid_time_steps:
                    # Subtract the traded power from the original supply to get the new remaining supply
                    new_remaining_supply[t] = max(0, copy_of_sell_bid[t][1] - trade_power[t])
                    copy_of_sell_bid[t][1] = new_remaining_supply[t]
                    new_total_price += copy_of_sell_bid[t][0]
                    count += 1
                    new_sum_energy += copy_of_sell_bid[t][1]

                new_mean_quantity = new_sum_energy / count if count > 0 else 0
                copy_of_sell_bid["mean_quantity"] = new_mean_quantity
                copy_of_sell_bid["sum_energy"] = new_sum_energy
                copy_of_sell_bid["total_price"] = new_total_price
                new_flex_delayed, new_flex_forced = characs_single_build.calc_characs_single(nodes=nodes,
                                                                                             block_length=block_length,
                                                                                             bes_id=seller_id,
                                                                                             soc_state=res_soc_seller)
                copy_of_sell_bid["flex_energy_delayed"] = new_flex_delayed
                copy_of_sell_bid["flex_energy_forced"] = new_flex_forced
                sorted_bids_nego[r + 1]["sell_blocks"].append(copy_of_sell_bid)

            # store the results of the negotiation for this match and this round
            # todo: inlcude traded quantity of each trader into the opti for next trading round r
            # todo: --> store negotiation results for each trader
            nego_transactions[r][match] = {
                "buyer": matched_bids_info_nego[r][match][0]["bes_id"],
                "seller": matched_bids_info_nego[r][match][1]["bes_id"],
                "price": trade_price,
                "quantity": trade_power,
                "saved_costs": saved_costs,
                "additional_revenue": additional_revenue,
                "remaining_demand": remaining_demand,
                "remaining_supply": remaining_supply,
                "opti_bes_res_buyer": opti_bes_res_buyer,
                "opti_bes_res_seller": opti_bes_res_seller,
            }

        # Add all buyers/sellers that weren't matched (but were in sorted bids list) to the new sorted_bids_nego lists
        if len(sorted_bids_nego[r]["buy_blocks"]) > len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining buy blocks
            remaining_buy_blocks = sorted_bids_nego[r]["buy_blocks"][len(sorted_bids_nego[r]["sell_blocks"]):]
            for buy_block in remaining_buy_blocks:
                sorted_bids_nego[r + 1]["buy_blocks"].append(buy_block)

        elif len(sorted_bids_nego[r]["buy_blocks"]) < len(sorted_bids_nego[r]["sell_blocks"]):
            # Retrieve the remaining sell blocks
            remaining_sell_blocks = sorted_bids_nego[r]["sell_blocks"][len(sorted_bids_nego[r]["buy_blocks"]):]
            for sell_block in remaining_sell_blocks:
                sorted_bids_nego[r + 1]["sell_blocks"].append(sell_block)

        # --------------------- SORT BUYERS AND SELLERS FOR NEXT TRADING ROUND ---------------------
        buy_list = sorted_bids_nego[r + 1]["buy_blocks"]
        sell_list = sorted_bids_nego[r + 1]["sell_blocks"]

        if options["crit_prio"] == "mean_price":
            # highest paying and lowest asking first if descending has been set True in options
            if options["descending"]:
                sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_price"], reverse=True)
                sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_price"], reverse=True)
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
            # otherwise lowest mean price first
            else:
                sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_price"])
                sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_price"])
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        elif options["crit_prio"] == "mean_quantity":
            if options["descending"]:
                sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_quantity"], reverse=True)
                sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_quantity"], reverse=True)
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
            else:
                sorted_buy_list = sorted(buy_list, key=lambda x: x["mean_quantity"])
                sorted_sell_list = sorted(sell_list, key=lambda x: x["mean_quantity"])
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        elif options["crit_prio"] == "flex_energy":
            # highest (lowest) energy flexibility of seller (buyer) first if descending has been set True in options
            if options["descending"]:
                sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"], reverse=True)
                sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_delayed"])
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)
            # otherwise lowest energy flexibility first
            else:
                sorted_sell_list = sorted(sell_list, key=lambda x: x[options["crit_prio"] + "_delayed"])
                sorted_buy_list = sorted(buy_list, key=lambda x: x[options["crit_prio"] + "_delayed"], reverse=True)
                sorted_bids_nego[r + 1]["sell_blocks"].clear()
                sorted_bids_nego[r + 1]["buy_blocks"].clear()
                for e in sorted_sell_list:
                    sorted_bids_nego[r + 1]["sell_blocks"].append(e)
                for e in sorted_buy_list:
                    sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        # randomly sort buy_list and sell_list if it has been specified as criteria in options
        elif options["crit_prio"] == "random":
            sorted_buy_list = buy_list
            if not sorted_buy_list:
                random.shuffle(sorted_buy_list)
            sorted_sell_list = sell_list
            if not sorted_sell_list:
                random.shuffle(sorted_sell_list)

            sorted_bids_nego[r + 1]["sell_blocks"].clear()
            sorted_bids_nego[r + 1]["buy_blocks"].clear()
            for e in sorted_sell_list:
                sorted_bids_nego[r + 1]["sell_blocks"].append(e)
            for e in sorted_buy_list:
                sorted_bids_nego[r + 1]["buy_blocks"].append(e)

        # match all buyers and sellers for the next trading round
        matched_bids_info_nego[r + 1] = matching(sorted_bids_nego[r + 1])

        # if exactly the same buyers and sellers are matched for the next round, stop the negotiation
        # and remove the last matched_bids_info_nego from r+1 round
        # todo: why?
        if matched_bids_info_nego[r] == matched_bids_info_nego[r + 1]:
            matched_bids_info_nego.pop(r)
            matched_bids_info_nego.pop(r + 1)
            sorted_bids_nego.pop(r)
            sorted_bids_nego.pop(r + 1)
            nego_transactions.pop(r)
            nego_transactions.pop(r + 1)
            break

        # go to next negotiation trading round
        r += 1

    print("Finished all negotiations for time steps " + str(block_bid_time_steps[0]) + " to " + str(block_bid_time_steps[-1]) + ".")

    return (nego_transactions, participating_buyers, participating_sellers, sorted_bids_nego, last_time_step,
            matched_bids_info_nego)


def trade_with_grid(sorted_bids, sorted_bids_nego, participating_buyers, participating_sellers, params,
                    par_rh, n_opt, block_length, opti_res):
    # Get the time steps of the block bid
    time_steps = par_rh["time_steps"][n_opt][0:block_length]
    nb_bes = len(sorted_bids["buy_blocks"] + sorted_bids["sell_blocks"])

    # Initialize all necessary variables
    power_from_grid = {}
    power_to_grid = {}
    costs_power_from_grid = {}
    revenue_power_to_grid = {}
    for bes_id in range(nb_bes):
        power_from_grid[bes_id] = {}
        power_to_grid[bes_id] = {}
        costs_power_from_grid[bes_id] = {}
        revenue_power_to_grid[bes_id] = {}

    # --------------------- BUYERS IMPORT FROM GRID ---------------------
    for buyer in sorted_bids["buy_blocks"]:
        buyer_id = buyer["bes_id"]

        # if buyer didn't participate in negotiation, his initial bid quantity is traded with the grid
        if buyer_id not in participating_buyers:
            for t in time_steps:
                power_from_grid[buyer_id][t] = buyer[t][1]
                costs_power_from_grid[buyer_id][t] = buyer[t][1] * params["eco"]["pr", "el"]

        # if buyer participated in negotiation, his remaining demand (after last negotiation round) is traded with grid
        else:
            remaining_demand = {}
            # Iterate backwards to find the last occurrence of the bes_id
            for round_num in sorted(sorted_bids_nego.keys(), reverse=True):
                buyer_found = False
                for buy_bid in sorted_bids_nego[round_num]["buy_blocks"]:
                    if buy_bid.get("bes_id") == buyer_id:
                        for t in buy_bid:
                            if isinstance(t, int):  # Ensure it's a time step key
                                remaining_demand[t] = buy_bid[t][1]
                        buyer_found = True
                        break
                if buyer_found:
                    break  # Stop searching through rounds once the bes_id is found

            for t in time_steps:
                power_from_grid[buyer_id][t] = remaining_demand[t]
                costs_power_from_grid[buyer_id][t] = remaining_demand[t] * params["eco"]["pr", "el"]

    # --------------------- SELLERS INJECT INTO GRID ---------------------
    for seller in sorted_bids["sell_blocks"]:
        seller_id = seller["bes_id"]

        # if seller didn't participate in negotiation, his initial bid quantity is traded with the grid
        if seller_id not in participating_sellers:
            for t in time_steps:
                power_to_grid[seller_id][t] = seller[t][1]
                revenue_power_to_grid[seller_id][t] = seller[t][1] * params["eco"]["pr", "el"]

        # if seller participated in negotiation, his remaining supply (after last negotiation round) is traded with grid
        else:
            remaining_supply = {}
            # Iterate backwards to find the last occurrence of the bes_id
            for round_num in sorted(sorted_bids_nego.keys(), reverse=True):
                seller_found = False
                for sell_bid in sorted_bids_nego[round_num]["sell_blocks"]:
                    if sell_bid.get("bes_id") == seller_id:
                        for t in sell_bid:
                            if isinstance(t, int):  # Ensure it's a time step key
                                remaining_supply[t] = sell_bid[t][1]
                        seller_found = True
                        break
                if seller_found:
                    break  # Stop searching through rounds once the bes_id is found

            for t in time_steps:
                power_to_grid[seller_id][t] = remaining_supply[t]
                if opti_res[seller_id][8]["pv"][t] > 1e-4:
                    revenue_power_to_grid[seller_id][t] = remaining_supply[t] * params["eco"]["sell" + "_" + "pv"]
                elif opti_res[seller_id][8]["chp"][t] > 1e-4:
                    revenue_power_to_grid[seller_id][t] = remaining_supply[t] * params["eco"]["sell" + "_" + "chp"]

        ignored_demand = {}
        # trade ignored demand of sellers with grid
        for t in time_steps:
            ignored_demand = seller.get("ignored_demand")
            power_from_grid[seller_id][t] = ignored_demand[t]
            costs_power_from_grid[seller_id][t] = (power_from_grid[seller_id][t] * params["eco"]["pr", "el"])

    # --------------------- STORE THE RESULTS OF TRANSACTIONS WITH THE GRID ---------------------

    grid_transactions = {
        "power_from_grid": power_from_grid,
        "power_to_grid": power_to_grid,
        "costs_power_from_grid": costs_power_from_grid,
        "revenue_power_to_grid": revenue_power_to_grid
    }

    return grid_transactions
