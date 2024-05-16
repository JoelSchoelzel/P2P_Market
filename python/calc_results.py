def calc_results (buyer_info, seller_info, market_info, par_rh, options, opti_res):
    '''Calculate the results after Stackelberg game

    KPIs:
    1) Gain = Saved cost (buyer_trans_info) + additional revenue (seller_trans_info)
    2) Traded amounts (total_market_info): trade amounts within the neighborhood (total_demand[t]: total_purchase_market[t], total_supply[t]:total_sold_market[t])
     and with the central grid ( total_demand_central[t]: total_purchase_grid[t], total_supply_central[t]: total_sold_grid[t])
    3) SCF, DCF (for each time_step and for the whole month): SCF = min(total_demand[t], total_supply[t])/total_supply[t],
    DCF = min(total_demand[t], total_supply[t])/total_demand[t]'''

    last_n_opt = par_rh["n_opt"]
    time_steps = []
    for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + options["block_length"]):
        time_steps.append(i)

    # Calculate KPIs for each time step
    gain = {}
    saved_cost = {t: {} for t in time_steps}  # cost saved by the buyer by trading in the community
    market_trade_buyer = {t: {} for t in time_steps}  # market purchase of each buyer
    grid_trade_buyer = {t: {} for t in time_steps}  # grid purchase of each buyer
    total_trade_buyer = {t: {} for t in time_steps}  # total purchase of each buyer
    soc_bat_buyer = {t: {} for t in time_steps}  # State of charge of the battery of each buyer
    soc_tes_buyer = {t: {} for t in time_steps}  # State of charge of the TES of each buyer
    initial_demand_buyer = {t: {} for t in time_steps}  # Demand of each buyer before Stackelberg game
    for opt in range(par_rh["n_opt"]):
        for t in time_steps:
            # if there is no transaction inside the neighborhood
            if buyer_info[opt][t] == 0:
                # there is no saved cost
                saved_cost[t] = {}
                market_trade_buyer[t] = {}
                total_trade_buyer[t] = {}
                for n in range(options["nb_bes"]):
                    initial_demand_buyer[t]["bes_"+str(n)] = opti_res[opt][n][4][t]
                    soc_bat_buyer[t]["bes_"+str(n)] = opti_res[opt][n][3]["bat"][t]
                    soc_tes_buyer[t]["bes_"+str(n)] = opti_res[opt][n][3]["tes"][t]
                    grid_trade_buyer[t]["bes_"+str(n)] = opti_res[opt][n][4][t]

            else:
                for n in range(options["nb_bes"]):
                    # check if the buyer exists in the current time step
                    if n in buyer_info[opt][t]:
                        saved_cost[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["saved_cost"]
                        market_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["total_trade_buyer"]
                        grid_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["power_from_grid"]
                        total_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["res_dem_buyer"]
                        soc_bat_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["soc_bat_buyer"]
                        soc_tes_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["soc_tes_buyer"]
                        initial_demand_buyer[t]["bes_"+str(n)] = buyer_info[opt][t]["bes_"+str(n)]["init_dem_buyer"]
                    else:
                        saved_cost[t]["bes_"+str(n)] = 0.0
                        market_trade_buyer[t]["bes_"+str(n)] = 0.0
                        grid_trade_buyer[t]["bes_"+str(n)] = 0.0
                        total_trade_buyer[t]["bes_"+str(n)] = 0.0
                        soc_bat_buyer[t]["bes_"+str(n)] = 0.0
                        soc_tes_buyer[t]["bes_"+str(n)] = 0.0
                        initial_demand_buyer[t]["bes_"+str(n)] = 0.0

    additional_revenue = {t: {} for t in time_steps}  # additional revenue for the seller by trading in the community
    available_supply = {t: {} for t in time_steps}  # available supply of each seller
    market_trade_seller = {t: {} for t in time_steps}  # market sale of each seller
    grid_trade_seller = {t: {} for t in time_steps}  # grid sale of each seller
    for opt in range(par_rh["n_opt"]):
        for t in time_steps:
            # if there is no transaction inside the neighborhood
            if seller_info[opt][t] == 0:
                # there is no additional revenue
                additional_revenue[t] = {}
                market_trade_seller[t] = {}
                for n in range(options["nb_bes"]):
                    available_supply[t]["bes_"+str(n)] = opti_res[opt][n][8]["chp"][t] + opti_res[opt][n][8]["pv"][t]
                    grid_trade_seller[t]["bes_"+str(n)] = available_supply[t]["bes_"+str(n)]
            else:
                for n in range(options["nb_bes"]):
                    # check if the seller exists in the current time step
                    if n in seller_info[opt][t]:
                        additional_revenue[t]["bes_"+str(n)] = seller_info[opt][t]["bes_"+str(n)]["gained_revenue"]
                        available_supply[t]["bes_"+str(n)] = seller_info[opt][t]["bes_"+str(n)]["available_supply_seller"]
                        market_trade_seller[t]["bes_"+str(n)] = seller_info[opt][t]["bes_"+str(n)]["total_demand_seller"]
                        grid_trade_seller[t]["bes_"+str(n)] = seller_info[opt][t]["bes_"+str(n)]["power_to_grid"]
                    else:
                        additional_revenue[t]["bes_"+str(n)] = 0.0
                        available_supply[t]["bes_"+str(n)] = 0.0
                        market_trade_seller[t]["bes_"+str(n)] = 0.0
                        grid_trade_seller[t]["bes_"+str(n)] = 0.0


    # save total market transactions and grid transaction for each time step
    trade_amount_market = {t: 0.0 for t in time_steps}
    purchased_amount_grid = {t: 0.0 for t in time_steps}
    sold_amount_grid = {t: 0.0 for t in time_steps}
    trade_amount_grid = {t: 0.0 for t in time_steps}
    for opt in range(par_rh["n_opt"]):
        for t in time_steps:
            if market_info[opt][t] == 0:
                trade_amount_market[t] = 0.0
                purchased_amount_grid[t] = 0.0
                sold_amount_grid[t] = 0.0
                trade_amount_grid[t] = 0.0
            else:
                trade_amount_market[t] = market_info[opt][t]["total_purchase_market"]
                purchased_amount_grid[t] = market_info[opt][t]["total_purchase_grid"]
                sold_amount_grid[t] = market_info[opt][t]["total_sold_grid"]
                trade_amount_grid[t] = purchased_amount_grid[t] + sold_amount_grid[t]

    # initialize the total saved cost, additional revenue and gain for each time step
    total_saved_cost = {}
    total_additional_revenue = {}
    # initialize the total saved cost, additional revenue, market trade,
    # purchased from grid, sold to grid and grid trade for the whole month
    cost_saved_month = 0
    revenue_added_month = 0
    market_trade_month = 0
    purchased_from_grid_month = 0
    sold_to_grid_month = 0
    grid_trade_month = 0

    for t in time_steps:
        # calculate the total saved cost, additional revenue and gain for each time step
        total_saved_cost[t] = sum(saved_cost[t][buyer] for buyer in saved_cost[t].values())
        total_additional_revenue[t] = sum(additional_revenue[t][seller] for seller in additional_revenue[t].values())
        gain[t] = total_saved_cost[t] + total_additional_revenue[t]
        # calculate the total saved cost and additional revenue; inter and intra market trading for the whole month
        cost_saved_month += total_saved_cost[t]
        revenue_added_month += total_additional_revenue[t]
        market_trade_month += trade_amount_market[t]
        purchased_from_grid_month += purchased_amount_grid[t]
        sold_to_grid_month += sold_amount_grid[t]
        grid_trade_month += trade_amount_grid[t]

    # calculate the total gain for the whole month
    gain_month = cost_saved_month + revenue_added_month

    # calculate the SCF and DCF for each time step
    market_supply = {t: 0.0 for t in time_steps}
    market_demand = {t: 0.0 for t in time_steps}
    scf = {t: 0.0 for t in time_steps}
    dcf = {t: 0.0 for t in time_steps}
    for t in time_steps:
        market_supply[t] = trade_amount_market[t] + sold_amount_grid[t]
        market_demand[t] = trade_amount_market[t] + purchased_amount_grid[t]
        scf[t] = min(market_demand[t], market_supply[t]) / market_supply[t]
        dcf[t] = min(market_demand[t], market_supply[t]) / market_demand[t]

    market_supply_month = market_trade_month + sold_to_grid_month
    market_demand_month = market_trade_month + purchased_from_grid_month
    scf_month = min(market_demand_month, market_supply_month) / market_supply_month
    dcf_month = min(market_demand_month, market_supply_month) / market_demand_month











'''
    for t in time_steps:
        resulting_trade_seller[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        resulting_rev_seller[t] = {seller["building"]: {} for seller in sell_list[t].values()}
        resulting_trade_buyer[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        resulting_cost_buyer[t] = {buyer["building"]: {} for buyer in buy_list[t].values()}
        tot_dem_sel[t] = {seller["building"]: {} for seller in sell_list[t].values()}

        print("Time step2: ", t)
        if t == 4565:
            print("Stop here")
        if not buy_list[t] or not sell_list[t]:
            pass

        else:
            for seller in sell_list[t].values():
                tot_dem_sel[t][seller["building"]] = (share_seller[t][seller["building"]] * sum(end_trans_res[buyer["building"]][seller["building"]][t] for buyer in buy_list[t].values()))
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
'''

