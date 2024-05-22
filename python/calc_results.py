import pickle

def calculate_results (buyer_info, seller_info, market_info, par_rh, options, opti_res, init_val):
    '''Calculate the results after Stackelberg game

    KPIs:
    1) Gain = Saved cost (buyer_trans_info) + additional revenue (seller_trans_info)
    2) Traded amounts (total_market_info): trade amounts within the neighborhood (total_demand[t]: total_purchase_market[t], total_supply[t]:total_sold_market[t])
     and with the central grid ( total_demand_central[t]: total_purchase_grid[t], total_supply_central[t]: total_sold_grid[t])
    3) SCF, DCF (for each time_step and for the whole month): SCF = min(total_demand[t], total_supply[t])/total_supply[t],
    DCF = min(total_demand[t], total_supply[t])/total_demand[t]'''

    last_n_opt = par_rh["n_opt"]
    # time_steps = []
    # for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + options["block_length"]):
    #     time_steps.append(i)
    time_steps = [i for i in
                  range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt - 1] + options["block_length"])]

    # Separate results for buyers and sellers at each time step
    # --------------------- Buyers ---------------------
    gain = {}
    saved_cost = {t: {} for t in time_steps}  # cost saved by the buyer by trading in the community
    market_trade_buyer = {t: {} for t in time_steps}  # market purchase of each buyer
    grid_trade_buyer = {t: {} for t in time_steps}  # grid purchase of each buyer
    total_trade_buyer = {t: {} for t in time_steps}  # total purchase of each buyer
    soc_bat_buyer = {t: {} for t in time_steps}  # State of charge of the battery of each buyer
    soc_tes_buyer = {t: {} for t in time_steps}  # State of charge of the TES of each buyer
    initial_demand_buyer = {t: {} for t in time_steps}  # Demand of each buyer before Stackelberg game
    for opt in range(par_rh["n_opt"]):
        start_time = par_rh["hour_start"][opt]
        end_time = start_time + options["block_length"]
        for t in range(start_time, end_time):
            # if there is no transaction inside the neighborhood
            if buyer_info[opt][t] == 0:
                # get the results from the optimization
                for n in range(options["nb_bes"]):
                    initial_demand_buyer[t]["bes_"+str(n)] = opti_res[opt][n][4][t]/1000  # convert to kWh
                    soc_bat_buyer[t]["bes_"+str(n)] = opti_res[opt][n][3]["bat"][t] / 1000
                    soc_tes_buyer[t]["bes_"+str(n)] = opti_res[opt][n][3]["tes"][t] / 1000
                    grid_trade_buyer[t]["bes_"+str(n)] = opti_res[opt][n][4][t] / 1000  # convert to kWh
                    # No trades within the community
                    saved_cost[t]["bes_" + str(n)] = 0.0
                    market_trade_buyer[t]["bes_" + str(n)] = 0.0
                    total_trade_buyer[t]["bes_" + str(n)] = 0.0

            else:
                for n in range(options["nb_bes"]):
                    # check if the buyer exists in the current time step
                    if n in buyer_info[opt][t]:
                        saved_cost[t]["bes_"+str(n)] = buyer_info[opt][t][n]["saved_cost"] /1000
                        market_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["total_trade_buyer"] / 1000
                        grid_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["power_from_grid"] / 1000
                        total_trade_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["res_dem_buyer"] / 1000
                        soc_bat_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["soc_bat_buyer"] / 1000
                        soc_tes_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["soc_tes_buyer"] / 1000
                        initial_demand_buyer[t]["bes_"+str(n)] = buyer_info[opt][t][n]["init_dem_buyer"] / 1000
                    else:
                        saved_cost[t]["bes_"+str(n)] = 0.0
                        market_trade_buyer[t]["bes_"+str(n)] = 0.0
                        grid_trade_buyer[t]["bes_"+str(n)] = 0.0
                        total_trade_buyer[t]["bes_"+str(n)] = 0.0
                        soc_bat_buyer[t]["bes_"+str(n)] = 0.0
                        soc_tes_buyer[t]["bes_"+str(n)] = 0.0
                        initial_demand_buyer[t]["bes_"+str(n)] = 0.0

    # --------------------- Sellers ---------------------
    seller_price = {t: {} for t in time_steps}  # price of the seller
    seller_share = {t: {} for t in time_steps}  # share of the seller
    additional_revenue = {t: {} for t in time_steps}  # additional revenue for the seller by trading in the community
    available_supply = {t: {} for t in time_steps}  # available supply of each seller
    market_trade_seller = {t: {} for t in time_steps}  # market sale of each seller
    grid_trade_seller = {t: {} for t in time_steps}  # grid sale of each seller
    soc_bat_seller = {t: {} for t in time_steps}  # State of charge of the battery of each seller
    soc_tes_seller = {t: {} for t in time_steps}  # State of charge of the TES of each seller
    for opt in range(par_rh["n_opt"]):
        start_time = par_rh["hour_start"][opt]
        end_time = start_time + options["block_length"]
        for t in range(start_time, end_time):
            # if there is no transaction inside the neighborhood
            if seller_info[opt][t] == 0:
                # get the results from the optimization
                for n in range(options["nb_bes"]):
                    available_supply[t]["bes_"+str(n)] = (opti_res[opt][n][8]["chp"][t] + opti_res[opt][n][8]["pv"][t]) / 1000
                    grid_trade_seller[t]["bes_"+str(n)] = available_supply[t]["bes_"+str(n)]
                    soc_bat_seller[t]["bes_"+str(n)] = opti_res[opt][n][3]["bat"][t] / 1000
                    soc_tes_seller[t]["bes_"+str(n)] = opti_res[opt][n][3]["tes"][t] / 1000
                    # No trades within the community
                    additional_revenue[t]["bes_"+str(n)] = 0.0
                    market_trade_seller[t]["bes_"+str(n)] = 0.0
                    seller_price[t]["bes_"+str(n)] = 0.0
                    seller_share[t]["bes_"+str(n)] = 0.0
            else:
                for n in range(options["nb_bes"]):
                    # check if the seller exists in the current time step
                    if n in seller_info[opt][t]:
                        seller_price[t]["bes_"+str(n)] = seller_info[opt][t][n]["seller_price"]
                        seller_share[t]["bes_"+str(n)] = seller_info[opt][t][n]["seller_share"]
                        additional_revenue[t]["bes_"+str(n)] = seller_info[opt][t][n]["gained_revenue"] /1000
                        available_supply[t]["bes_"+str(n)] = seller_info[opt][t][n]["available_supply_seller"] / 1000
                        market_trade_seller[t]["bes_"+str(n)] = seller_info[opt][t][n]["total_demand_seller"] / 1000
                        grid_trade_seller[t]["bes_"+str(n)] = seller_info[opt][t][n]["power_to_grid"] / 1000
                        soc_bat_seller[t]["bes_"+str(n)] = seller_info[opt][t][n]["soc_bat_seller"] / 1000
                        soc_tes_seller[t]["bes_"+str(n)] = seller_info[opt][t][n]["soc_tes_seller"] / 1000
                    else:
                        additional_revenue[t]["bes_"+str(n)] = 0.0
                        available_supply[t]["bes_"+str(n)] = 0.0
                        market_trade_seller[t]["bes_"+str(n)] = 0.0
                        grid_trade_seller[t]["bes_"+str(n)] = 0.0
                        seller_price[t]["bes_"+str(n)] = 0.0
                        seller_share[t]["bes_"+str(n)] = 0.0

    # --------------------- Market ---------------------
    # save total market transactions and grid transaction for each time step
    trade_amount_market = {t: 0.0 for t in time_steps}
    purchased_amount_grid = {t: 0.0 for t in time_steps}
    sold_amount_grid = {t: 0.0 for t in time_steps}
    trade_amount_grid = {t: 0.0 for t in time_steps}
    demand_before_stack = {t: 0.0 for t in time_steps}  # initial demand before Stackelberg game
    demand_after_stack = {t: 0.0 for t in time_steps}  # final demand after Stackelberg game
    num_iter = {t: 0 for t in time_steps}  # number of iterations for each time step
    init_dsd = {t: 0.0 for t in time_steps}  # initial demand supply difference for each time step
    for opt in range(par_rh["n_opt"]):
        start_time = par_rh["hour_start"][opt]
        end_time = start_time + options["block_length"]
        for t in range(start_time, end_time):
            if market_info[opt][t] == 0:
                trade_amount_market[t] = 0.0
                purchased_amount_grid[t] = 0.0
                sold_amount_grid[t] = 0.0
                trade_amount_grid[t] = 0.0
                demand_before_stack[t] = 0.0
                demand_after_stack[t] = 0.0
                num_iter[t] = 0
                init_dsd[t] = 0.0
            else:
                trade_amount_market[t] = market_info[opt][t]["total_purchase_market"] / 1000
                purchased_amount_grid[t] = market_info[opt][t]["total_purchase_grid"] / 1000
                sold_amount_grid[t] = market_info[opt][t]["total_sold_grid"] / 1000
                trade_amount_grid[t] = purchased_amount_grid[t] + sold_amount_grid[t]
                demand_before_stack[t] = market_info[opt][t]["init_kum_dem"] / 1000
                demand_after_stack[t] = market_info[opt][t]["res_kum_dem"] / 1000
                num_iter[t] = market_info[opt][t]["num_iter"]
                init_dsd[t] = market_info[opt][t]["total_initial_dsd"] / 1000

    # --------------------- Whole month ---------------------
    # initialize the total saved cost, additional revenue and gain for each time step
    total_saved_cost = {}
    total_additional_revenue = {}
    # initialize the variables for whole month
    cost_saved_month = 0
    revenue_added_month = 0
    market_trade_month = 0
    purchased_from_grid_month = 0
    sold_to_grid_month = 0
    grid_trade_month = 0
    demand_before_stack_month = 0
    demand_after_stack_month = 0

    for t in time_steps:
        # calculate the total saved cost, additional revenue and gain for each time step
        total_saved_cost[t] = sum(saved_cost[t][buyer] for buyer in saved_cost[t])
        total_additional_revenue[t] = sum(additional_revenue[t][seller] for seller in additional_revenue[t])
        gain[t] = total_saved_cost[t] + total_additional_revenue[t]
        # calculate the total saved cost and additional revenue; inter and intra market trading for the whole month
        cost_saved_month += total_saved_cost[t]
        revenue_added_month += total_additional_revenue[t]
        market_trade_month += trade_amount_market[t]
        purchased_from_grid_month += purchased_amount_grid[t]
        sold_to_grid_month += sold_amount_grid[t]
        grid_trade_month += trade_amount_grid[t]
        demand_before_stack_month += demand_before_stack[t]
        demand_after_stack_month += demand_after_stack[t]

    # calculate the total gain for the whole month
    gain_month = cost_saved_month + revenue_added_month

    # save each seller's price and share for each time step
    seller_end_price = {"bes_"+str(n): {} for n in range(options["nb_bes"])}
    seller_end_share = {"bes_"+str(n): {} for n in range(options["nb_bes"])}
    for n in range(options["nb_bes"]):
        for t in time_steps:
            seller_end_price["bes_"+str(n)][t] = seller_price[t]["bes_"+str(n)]
            seller_end_share["bes_"+str(n)][t] = seller_share[t]["bes_"+str(n)]

    # calculate the Supply Cover Factor and Demand Cover Factor for each time step
    markets_total_supply = {t: 0.0 for t in time_steps}
    markets_total_demand = {t: 0.0 for t in time_steps}
    scf = {t: 0.0 for t in time_steps}
    dcf = {t: 0.0 for t in time_steps}
    mscf = {t: 0.0 for t in time_steps}
    mdcf = {t: 0.0 for t in time_steps}
    for t in time_steps:
        markets_total_supply[t] = trade_amount_market[t] + sold_amount_grid[t]  # total available supply in the market at time t
        markets_total_demand[t] = trade_amount_market[t] + purchased_amount_grid[t]  # total demand in the market at time t
        scf[t] = min(markets_total_demand[t], markets_total_supply[t]) / markets_total_supply[t]  if markets_total_supply[t] > 0 else 0  # overall SCF
        dcf[t] = min(markets_total_demand[t], markets_total_supply[t]) / markets_total_demand[t]  if markets_total_demand[t] > 0 else 0  # overall DCF
        mscf[t] = trade_amount_market[t] / markets_total_supply[t] if markets_total_supply[t] > 0 else 0  # market SCF
        mdcf[t] = trade_amount_market[t] / markets_total_demand[t] if markets_total_demand[t] > 0 else 0  # market DCF

    # calculate the Supply Cover Factor and Demand Cover Factor for the whole month
    market_supply_month = market_trade_month + sold_to_grid_month
    market_demand_month = market_trade_month + purchased_from_grid_month
    scf_month = min(market_demand_month, market_supply_month) / market_supply_month
    dcf_month = min(market_demand_month, market_supply_month) / market_demand_month
    mscf_month = market_trade_month / market_supply_month
    mdcf_month = market_trade_month / market_demand_month

    # --------------------- SOC ---------------------
    soc_tes = {}
    for n in range(options["nb_bes"]):
        soc_tes[n] = []
        for opt in range(1, par_rh["n_opt"]):
            soc_tes[n].append(init_val[opt]["building_" + str(n)]["soc"]["tes"] / 1000)

    soc_bat = {}
    for n in range(options["nb_bes"]):
        soc_bat[n] = []
        for opt in range(1, par_rh["n_opt"]):
            soc_bat[n].append(init_val[opt]["building_" + str(n)]["soc"]["bat"] / 1000)

    # --------------------- PV / CHP ---------------------
    pv_gen = {t: {} for t in time_steps}
    chp_gen = {t: {} for t in time_steps}
    for opt in range(par_rh["n_opt"]):
        start_time = par_rh["hour_start"][opt]
        end_time = start_time + options["block_length"]
        for n in range(options["nb_bes"]):
            for t in range(start_time, end_time):
                pv_gen[t][n] = opti_res[opt][n][1]["pv"][t] / 1000
                chp_gen[t][n] = opti_res[opt][n][1]["chp"][t] / 1000

    tot_pv_gen = {t: 0.0 for t in time_steps}
    tot_chp_gen = {t: 0.0 for t in time_steps}
    pv_gen_month = 0
    chp_gen_month = 0
    for t in time_steps:
        tot_pv_gen[t] = sum(pv_gen[t][n] for n in range(options["nb_bes"]))
        tot_chp_gen[t] = sum(chp_gen[t][n] for n in range(options["nb_bes"]))
        pv_gen_month += tot_pv_gen[t]
        chp_gen_month += tot_chp_gen[t]

    results_time_step = {"total_demand": markets_total_demand,
                         "total_supply": markets_total_supply,
                         "traded_power_market": trade_amount_market,
                         "power_from_grid": purchased_amount_grid,
                         "power_to_grid": sold_amount_grid,
                         "seller_price": seller_end_price,
                         "seller_share": seller_end_share,
                         "scf": scf,
                         "dcf": dcf,
                         "mscf": mscf,
                         "mdcf": mdcf,
                         "saved_cost": total_saved_cost,
                         "additional_revenue": total_additional_revenue,
                         "gain": gain,
                         "soc_bat": soc_bat,
                         "soc_tes": soc_tes,
                         "tot_pv_gen": tot_pv_gen,
                         "tot_chp_gen": tot_chp_gen,
                         "initial_demand": demand_before_stack,
                         "final_demand": demand_after_stack,
                         "num_iter": num_iter,
                         "init_dsd": init_dsd
                         }

    results_month = {"total_demand_month": market_demand_month,
                     "total_supply_month": market_supply_month,
                     "traded_power_month": market_trade_month,
                     "power_from_grid_month": purchased_from_grid_month,
                     "power_to_grid_month": sold_to_grid_month,
                     "scf_month": scf_month,
                     "dcf_month": dcf_month,
                     "mscf_month": mscf_month,
                     "mdcf_month": mdcf_month,
                     "pv_gen_month": pv_gen_month,
                     "chp_gen_month": chp_gen_month,
                     "saved_cost_month": cost_saved_month,
                     "additional_revenue_month": revenue_added_month,
                     "gain_month": gain_month,
                     "initial_demand_month": demand_before_stack_month,
                     "final_demand_month": demand_after_stack_month
                        }

    return results_time_step, results_month


def mock_data():
    # Mock data for buyer_info, seller_info, market_info, par_rh, options, opti_res, init_val
    buyer_info = {0:{4344: 0, 4345: 0, 4346: 0, 4347: 0},
                  1:{4348: 0, 4349: {0: {'total_trade_buyer': 8.07784987897724, 'total_cost_trade_buyer': 1.658786472647976,
                                         'power_from_grid': 38.08215012102276, 'saved_cost': 0.9964027825718424, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9250.826763208172, 'init_dem_buyer': 46.16, 'res_dem_buyer': 46.16},
                                     1: {'total_trade_buyer': 11.388788347570165, 'total_cost_trade_buyer': 2.3386876871735334,
                                         'power_from_grid': 53.691211652429836, 'saved_cost': 1.40480704267278, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9816.155130609288, 'init_dem_buyer': 65.08, 'res_dem_buyer': 65.08},
                                     2: {'total_trade_buyer': 6.14063588070432, 'total_cost_trade_buyer': 1.260979578102632,
                                         'power_from_grid': 28.949364119295684, 'saved_cost': 0.7574474358848778, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9322.157108678133, 'init_dem_buyer': 35.09, 'res_dem_buyer': 35.09},
                                     3: {'total_trade_buyer': 5.753893068040981, 'total_cost_trade_buyer': 1.1815619415222156,
                                         'power_from_grid': 27.126106931959022, 'saved_cost': 0.709742709942855, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9615.680394226356, 'init_dem_buyer': 32.88, 'res_dem_buyer': 32.88},
                                     4: {'total_trade_buyer': 9.991439316295615, 'total_cost_trade_buyer': 2.051742063601304,
                                         'power_from_grid': 47.10356068370439, 'saved_cost': 1.232444039665064, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9287.878131733858, 'init_dem_buyer': 57.095, 'res_dem_buyer': 57.095},
                                     5: {'total_trade_buyer': 7.24661532687278, 'total_cost_trade_buyer': 1.4880924573733252,
                                         'power_from_grid': 34.16338467312722, 'saved_cost': 0.8938700005697574, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 9817.820219659077, 'init_dem_buyer': 41.41, 'res_dem_buyer': 41.41},
                                     6: {'total_trade_buyer': 3.6696818016064285, 'total_cost_trade_buyer': 0.7535691579598801,
                                         'power_from_grid': 17.30031819839357, 'saved_cost': 0.45265525022815295, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 10167.062147549022, 'init_dem_buyer': 20.97, 'res_dem_buyer': 20.97},
                                     7: {'total_trade_buyer': 22.500206849859154, 'total_cost_trade_buyer': 4.620417476618577,
                                         'power_from_grid': 106.07479315014083, 'saved_cost': 2.7754005149301273, 'soc_bat_buyer': 0.0,
                                         'soc_tes_buyer': 8810.055487374906, 'init_dem_buyer': 128.575, 'res_dem_buyer': 128.575},
                                     16: {'total_trade_buyer': 71.79854067582706, 'total_cost_trade_buyer': 14.743830327781087,
                                          'power_from_grid': 338.4864593241729, 'saved_cost': 8.856349992363267, 'soc_bat_buyer': 0.0,
                                          'soc_tes_buyer': 57620.778815505044, 'init_dem_buyer': 410.28499999999997, 'res_dem_buyer': 410.28499999999997},
                                     17: {'total_trade_buyer': 79.1300294253884, 'total_cost_trade_buyer': 16.249351542503508,
                                          'power_from_grid': 373.0499705746116, 'saved_cost': 9.76068912962166, 'soc_bat_buyer': 0.0,
                                          'soc_tes_buyer': 54160.86574543075, 'init_dem_buyer': 452.18, 'res_dem_buyer': 452.18},
                                     18: {'total_trade_buyer': 85.99340187455407, 'total_cost_trade_buyer': 17.65874507493968,
                                          'power_from_grid': 405.4065981254459, 'saved_cost': 10.607286121226245, 'soc_bat_buyer': 0.0,
                                          'soc_tes_buyer': 59982.208219697335, 'init_dem_buyer': 491.4, 'res_dem_buyer': 491.4},
                                     19: {'total_trade_buyer': 61.51748174190347, 'total_cost_trade_buyer': 12.632614875699876,
                                          'power_from_grid': 290.0175182580965, 'saved_cost': 7.588181372863793, 'soc_bat_buyer': 0.0,
                                          'soc_tes_buyer': 53869.428870207805, 'init_dem_buyer': 351.53499999999997, 'res_dem_buyer': 351.53499999999997}},
                     4350: {0: {'total_trade_buyer': 82.35953303062303, 'total_cost_trade_buyer': 16.91253010783844, 'power_from_grid': 10.490466969376968,
                                'saved_cost': 10.15904839932735, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7468.514534274032, 'init_dem_buyer': 92.85,
                                'res_dem_buyer': 92.85}, 1: {'total_trade_buyer': 57.727069570629475, 'total_cost_trade_buyer': 11.854253736328763, 'power_from_grid': 7.352930429370524, 'saved_cost': 7.120634031537146, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 8560.458647727479, 'init_dem_buyer': 65.08, 'res_dem_buyer': 65.08}, 2: {'total_trade_buyer': 31.125428261115378, 'total_cost_trade_buyer': 6.391606693420043, 'power_from_grid': 3.9645717388846258, 'saved_cost': 3.8393215760085826, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7871.031379255665, 'init_dem_buyer': 35.09, 'res_dem_buyer': 35.09}, 3: {'total_trade_buyer': 66.90769603123206, 'total_cost_trade_buyer': 13.739495380013503, 'power_from_grid': 8.522303968767943, 'saved_cost': 8.253064305452476, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 8363.83596585703, 'init_dem_buyer': 75.43, 'res_dem_buyer': 75.43}, 4: {'total_trade_buyer': 38.23930499677069, 'total_cost_trade_buyer': 7.852441281086863, 'power_from_grid': 4.870695003229308, 'saved_cost': 4.7168182713516655, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7482.212711464316, 'init_dem_buyer': 43.11, 'res_dem_buyer': 43.11}, 5: {'total_trade_buyer': 110.57554536992426, 'total_cost_trade_buyer': 22.706688241713948, 'power_from_grid': 14.08445463007574, 'saved_cost': 13.639493521380158, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 8301.129311894569, 'init_dem_buyer': 124.66, 'res_dem_buyer': 124.66}, 6: {'total_trade_buyer': 18.600747524525204, 'total_cost_trade_buyer': 3.8196635041612508, 'power_from_grid': 2.369252475474795, 'saved_cost': 2.294402207150184, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 8451.271728680967, 'init_dem_buyer': 20.97, 'res_dem_buyer': 20.97}, 7: {'total_trade_buyer': 39.392427160904354, 'total_cost_trade_buyer': 8.089234917491709, 'power_from_grid': 5.017572839095642, 'saved_cost': 4.859055890297553, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7239.957003790105, 'init_dem_buyer': 44.41, 'res_dem_buyer': 44.41}, 16: {'total_trade_buyer': 637.3838411396317, 'total_cost_trade_buyer': 130.88677177802336, 'power_from_grid': 81.18615886036832, 'saved_cost': 78.62129680457357, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 49580.76010433518, 'init_dem_buyer': 718.57, 'res_dem_buyer': 718.57}, 17: {'total_trade_buyer': 402.3775440891926, 'total_cost_trade_buyer': 82.62822867871569, 'power_from_grid': 51.252455910807384, 'saved_cost': 49.63327006340191, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 47883.17275727748, 'init_dem_buyer': 453.63, 'res_dem_buyer': 453.63}, 18: {'total_trade_buyer': 944.1586876516509, 'total_cost_trade_buyer': 193.88298650926652, 'power_from_grid': 120.26131234834918, 'saved_cost': 116.46197412183115, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 53487.61796390279, 'init_dem_buyer': 1064.42, 'res_dem_buyer': 1064.42}, 19: {'total_trade_buyer': 266.0164130951411, 'total_cost_trade_buyer': 54.62647042908722, 'power_from_grid': 33.88358690485887, 'saved_cost': 32.813124555285654, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 46714.84809790539, 'init_dem_buyer': 299.9, 'res_dem_buyer': 299.9}}, 4351: {0: {'total_trade_buyer': 169.7165652068497, 'total_cost_trade_buyer': 34.85129666522659, 'power_from_grid': 13.553434793150274, 'saved_cost': 20.93453831826491, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 5589.280301524305, 'init_dem_buyer': 183.26999999999998, 'res_dem_buyer': 183.26999999999998}, 1: {'total_trade_buyer': 60.2671144413258, 'total_cost_trade_buyer': 12.375851950526258, 'power_from_grid': 4.812885558674196, 'saved_cost': 7.433948566337537, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7409.511230910101, 'init_dem_buyer': 65.08, 'res_dem_buyer': 65.08}, 2: {'total_trade_buyer': 32.49497611779537, 'total_cost_trade_buyer': 6.672843345789279, 'power_from_grid': 2.595023882204636, 'saved_cost': 4.008255304130059, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 6536.409237505694, 'init_dem_buyer': 35.09, 'res_dem_buyer': 35.09}, 3: {'total_trade_buyer': 69.85169702380463, 'total_cost_trade_buyer': 14.344045983838285, 'power_from_grid': 5.578302976195374, 'saved_cost': 8.616206827886302, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7217.085872453508, 'init_dem_buyer': 75.43, 'res_dem_buyer': 75.43}, 4: {'total_trade_buyer': 18.335723201263846, 'total_cost_trade_buyer': 3.7652407593795303, 'power_from_grid': 1.4642767987361545, 'saved_cost': 2.261711456875895, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 5808.719086142226, 'init_dem_buyer': 19.8, 'res_dem_buyer': 19.8}, 5: {'total_trade_buyer': 115.44097243785608, 'total_cost_trade_buyer': 23.705803690113747, 'power_from_grid': 9.219027562143921, 'saved_cost': 14.239643950209546, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 6906.676066399842, 'init_dem_buyer': 124.66, 'res_dem_buyer': 124.66}, 6: {'total_trade_buyer': 635.8050927032186, 'total_cost_trade_buyer': 130.56257578660598, 'power_from_grid': 50.77490729678141, 'saved_cost': 78.42655818494202, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 6990.837454376908, 'init_dem_buyer': 686.58, 'res_dem_buyer': 686.58}, 7: {'total_trade_buyer': 987.8278270018261, 'total_cost_trade_buyer': 202.850444274825, 'power_from_grid': 78.88717299817381, 'saved_cost': 121.84856246067527, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 5685.533548663935, 'init_dem_buyer': 1066.715, 'res_dem_buyer': 1066.715}, 13: {'total_trade_buyer': 892.4918496221235, 'total_cost_trade_buyer': 183.27320131990305, 'power_from_grid': 71.27371492893712, 'saved_cost': 110.08886965088894, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 7934.097599717862, 'init_dem_buyer': 963.7655645510606, 'res_dem_buyer': 963.7655645510606}, 16: {'total_trade_buyer': 594.850680653931, 'total_cost_trade_buyer': 122.15258727228473, 'power_from_grid': 47.504319346068996, 'saved_cost': 73.3748314586624, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 42034.724228971456, 'init_dem_buyer': 642.355, 'res_dem_buyer': 642.355}, 17: {'total_trade_buyer': 336.46978120945477, 'total_cost_trade_buyer': 69.09406957136154, 'power_from_grid': 26.870218790545266, 'saved_cost': 41.50354751218625, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 42231.95986349719, 'init_dem_buyer': 363.34000000000003, 'res_dem_buyer': 363.34000000000003}, 18: {'total_trade_buyer': 1557.230746364306, 'total_cost_trade_buyer': 319.7773337659103, 'power_from_grid': 124.3592536356939, 'saved_cost': 192.0844125640372, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 47218.90611359594, 'init_dem_buyer': 1681.59, 'res_dem_buyer': 1681.59}, 19: {'total_trade_buyer': 693.2153533023272, 'total_cost_trade_buyer': 142.35177280063292, 'power_from_grid': 55.3596466976727, 'saved_cost': 85.50811382984205, 'soc_bat_buyer': 0.0, 'soc_tes_buyer': 40537.006117889294, 'init_dem_buyer': 748.5749999999999, 'res_dem_buyer': 748.5749999999999}}}}

    seller_info = {
        0: {
            4344: 0,
            4345: 0,
            4346: 0,
            4347: 0
        },
        1: {
            4348: 0,
            4349: {
                10: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 73.01171039825051,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 73.01171039825053,
                    'total_revenue_trade_seller': 14.992954730280744,
                    'power_to_grid': -1.4210854715202004e-14,
                    'gained_revenue': 9.005994477624203,
                    'soc_bat_seller': 4645.026022268066,
                    'soc_tes_seller': 9797.321452512875,
                    'seller_share': 0.5  # Added seller_share
                },
                11: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 70.97851540211298,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 70.97851540211298,
                    'total_revenue_trade_seller': 14.5754381378239,
                    'power_to_grid': 0.0,
                    'gained_revenue': 8.755199874850636,
                    'soc_bat_seller': 5035.629380618563,
                    'soc_tes_seller': 10219.957335932057,
                    'seller_share': 0.6  # Added seller_share
                },
                12: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 76.79851540210439,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 76.79851540210439,
                    'total_revenue_trade_seller': 15.770575137822135,
                    'power_to_grid': 8.58335624798201e-12,
                    'gained_revenue': 9.473096874849576,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 10305.734417375585,
                    'seller_share': 0.7  # Added seller_share
                },
                13: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 51.801710398241994,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 51.801710398241994,
                    'total_revenue_trade_seller': 10.637481230278993,
                    'power_to_grid': 0.0,
                    'gained_revenue': 6.38974097762315,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 10534.912138848606,
                    'seller_share': 0.4  # Added seller_share
                },
                14: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 41.60645254054907,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 41.60645254054908,
                    'total_revenue_trade_seller': 8.543885029201752,
                    'power_to_grid': 6.785683126508957e-12,
                    'gained_revenue': 5.132155920876729,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 9185.565313047282,
                    'seller_share': 0.3  # Added seller_share
                },
                15: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 59.011660046340694,
                    'possible_demand_seller': 355.44333333333327,
                    'total_demand_seller': 59.0116600463407,
                    'total_revenue_trade_seller': 12.118044390516062,
                    'power_to_grid': 8.86046791492845e-12,
                    'gained_revenue': 7.279088266716125,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 9685.021089813776,
                    'seller_share': 0.2  # Added seller_share
                }
            },
            4350: {
                9: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 469.67928697467283,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 469.6792869746728,
                    'total_revenue_trade_seller': 96.44864158024906,
                    'power_to_grid': 5.684341886080802e-14,
                    'gained_revenue': 57.934940048325885,
                    'soc_bat_seller': 2594.4214745327445,
                    'soc_tes_seller': 7605.08917507347,
                    'seller_share': 0.55  # Added seller_share
                },
                11: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 479.8770341826727,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 479.8770341826726,
                    'total_revenue_trade_seller': 98.54274896941182,
                    'power_to_grid': 5.684341886080802e-14,
                    'gained_revenue': 59.192832166432666,
                    'soc_bat_seller': 5035.629380618563,
                    'soc_tes_seller': 8528.219699282681,
                    'seller_share': 0.65  # Added seller_share
                },
                12: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 428.9070341826664,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 428.90703418266634,
                    'total_revenue_trade_seller': 88.07605946941054,
                    'power_to_grid': 5.684341886080802e-14,
                    'gained_revenue': 52.90568266643189,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 8710.486009352713,
                    'seller_share': 0.75  # Added seller_share
                },
                13: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 425.5801110013308,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 425.58011100133075,
                    'total_revenue_trade_seller': 87.39287579412327,
                    'power_to_grid': 5.684341886080802e-14,
                    'gained_revenue': 52.49530669201415,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 8867.008673354314,
                    'seller_share': 0.85  # Added seller_share
                },
                14: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 410.3676934039977,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 410.36769340399763,
                    'total_revenue_trade_seller': 84.26900584051091,
                    'power_to_grid': 5.684341886080802e-14,
                    'gained_revenue': 50.61885498138311,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 7639.786107760423,
                    'seller_share': 0.45  # Added seller_share
                },
                15: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 480.4530781760004,
                    'possible_demand_seller': 506.35333333333335,
                    'total_demand_seller': 480.4530781760005,
                    'total_revenue_trade_seller': 98.6610396034417,
                    'power_to_grid': -5.684341886080802e-14,
                    'gained_revenue': 59.26388719300966,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 7909.149643768877,
                    'seller_share': 0.35  # Added seller_share
                }
            },
            4351: {
                8: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 1099.8381489143544,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 950.8929377930089,
                    'total_revenue_trade_seller': 195.26586477579437,
                    'power_to_grid': 148.94521112134555,
                    'gained_revenue': 117.29264387676764,
                    'soc_bat_seller': 2650.8002432044623,
                    'soc_tes_seller': 5710.3058453305175,
                    'seller_share': 0.5  # Added seller_share
                },
                9: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 851.1842548720994,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 851.1842548720992,
                    'total_revenue_trade_seller': 174.7906867379856,
                    'power_to_grid': 1.1368683772161603e-13,
                    'gained_revenue': 104.99357783847344,
                    'soc_bat_seller': 2968.6086134352954,
                    'soc_tes_seller': 5933.785597926528,
                    'seller_share': 0.6  # Added seller_share
                },
                10: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 558.3494354489394,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 558.3494354489394,
                    'total_revenue_trade_seller': 114.6570565694397,
                    'power_to_grid': 0.0,
                    'gained_revenue': 68.87240286262667,
                    'soc_bat_seller': 4517.247786186972,
                    'soc_tes_seller': 6085.05612180454,
                    'seller_share': 0.7  # Added seller_share
                },
                11: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 1212.1017649542089,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 950.8929377930089,
                    'total_revenue_trade_seller': 195.26586477579437,
                    'power_to_grid': 261.2088271612,
                    'gained_revenue': 117.29264387676764,
                    'soc_bat_seller': 5035.629380618563,
                    'soc_tes_seller': 6274.323914688441,
                    'seller_share': 0.8  # Added seller_share
                },
                12: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 1147.0867649542088,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 950.8929377930089,
                    'total_revenue_trade_seller': 195.26586477579437,
                    'power_to_grid': 196.19382716119992,
                    'gained_revenue': 117.29264387676764,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 7249.739415480164,
                    'seller_share': 0.75  # Added seller_share
                },
                14: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 1070.7619598053207,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 950.8929377930089,
                    'total_revenue_trade_seller': 195.26586477579437,
                    'power_to_grid': 119.8690220123118,
                    'gained_revenue': 117.29264387676764,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 6215.993964498402,
                    'seller_share': 0.65  # Added seller_share
                },
                15: {
                    'seller_price': 0.20535,
                    'available_supply_seller': 1243.177954063227,
                    'possible_demand_seller': 950.8929377930086,
                    'total_demand_seller': 950.8929377930089,
                    'total_revenue_trade_seller': 195.26586477579437,
                    'power_to_grid': 292.2850162702181,
                    'gained_revenue': 117.29264387676764,
                    'soc_bat_seller': 0.0,
                    'soc_tes_seller': 6093.017592724131,
                    'seller_share': 0.7  # Added seller_share
                }
            }
        }
    }
    market_info = {0: {4344: 0, 4345: 0, 4346: 0, 4347: 0}, 1:{4348: 0, 4349: {'total_purchase_market': 373.2085641875997, 'total_purchase_grid': 1759.4514358124004, 'total_sold_market': 373.2085641875997, 'total_sold_grid': 2.4215296434704214e-11, 'price_update_step_size': 0.05, 'stopping_crit': 500, 'num_iter': 1, 'init_kum_dem': 2132.66, 'res_kum_dem': 2132.66, 'total_initial_dsd':1000}, 4350: {'total_purchase_market': 2694.8642379213406, 'total_purchase_grid': 343.2557620786593, 'total_sold_market': 2694.8642379213406, 'total_sold_grid': 2.2737367544323206e-13, 'price_update_step_size': 0.05, 'stopping_crit': 500, 'num_iter': 1, 'init_kum_dem': 5170.779999999999, 'res_kum_dem': 5170.779999999999, 'total_initial_dsd':1000}, 4351: {'total_purchase_market': 6163.998379286083, 'total_purchase_grid': 492.25218526497775, 'total_sold_market': 6163.998379286083, 'total_sold_grid': 1018.5019037262755, 'price_update_step_size': 0.05, 'stopping_crit': 500, 'num_iter': 1, 'init_kum_dem': 11827.030564551062, 'res_kum_dem': 11827.030564551062, 'total_initial_dsd':1000}}}

    par_rh = {
        "n_opt": 2,
        "hour_start": {
            0: 4344, 1: 4348
        }
    }

    options = {
        "block_length": 4,
        "nb_bes": 2
    }

    opti_res = {
        0: {
            0: {1: {"chp": {4344: 3000, 4345: 3000, 4346: 3000, 4347: 3000},
                    "pv": {4344: 4000, 4345: 4000, 4346: 4000, 4347: 4000}},
                4: {4344: 5000, 4345: 5000, 4346: 5000, 4347: 5000},
                3: {"bat": {4344: 1000, 4345: 1000, 4346: 1000, 4347: 1000},
                    "tes": {4344: 2000, 4345: 2000, 4346: 2000, 4347: 2000}},
                8: {"chp": {4344: 3000, 4345: 3000, 4346: 3000, 4347: 3000},
                    "pv": {4344: 4000, 4345: 4000, 4346: 4000, 4347: 4000}}},
            1: {1: {"chp": {4344: 3000, 4345: 3000, 4346: 3000, 4347: 3000},
                    "pv": {4344: 4000, 4345: 4000, 4346: 4000, 4347: 4000}},
                4: {4344: 5000, 4345: 5000, 4346: 5000, 4347: 5000},
                3: {"bat": {4344: 1000, 4345: 1000, 4346: 1000, 4347: 1000},
                    "tes": {4344: 2000, 4345: 2000, 4346: 2000, 4347: 2000}},
                8: {"chp": {4344: 3000, 4345: 3000, 4346: 3000, 4347: 3000},
                    "pv": {4344: 4000, 4345: 4000, 4346: 4000, 4347: 4000}}}
        },
        1: {
            0: {1: {"chp": {4348: 3000, 4349: 3000, 4350: 3000, 4351: 3000},
                    "pv": {4348: 4000, 4349: 4000, 4350: 4000, 4351: 4000}},
                4: {4348: 5000, 4349: 5000, 4350: 5000, 4351: 5000},
                3: {"bat": {4348: 1000, 4349: 1000, 4350: 1000, 4351: 1000},
                    "tes": {4348: 2000, 4349: 2000, 4350: 2000, 4351: 2000}},
                8: {"chp": {4348: 3000, 4349: 3000, 4350: 3000, 4351: 3000},
                    "pv": {4348: 4000, 4349: 4000, 4350: 4000, 4351: 4000}}},
            1: {1: {"chp": {4348: 3000, 4349: 3000, 4350: 3000, 4351: 3000},
                    "pv": {4348: 4000, 4349: 4000, 4350: 4000, 4351: 4000}},
                4: {4348: 5000, 4349: 5000, 4350: 5000, 4351: 5000},
                3: {"bat": {4348: 1000, 4349: 1000, 4350: 1000, 4351: 1000},
                    "tes": {4348: 2000, 4349: 2000, 4350: 2000, 4351: 2000}},
                8: {"chp": {4348: 3000, 4349: 3000, 4350: 3000, 4351: 3000},
                    "pv": {4348: 4000, 4349: 4000, 4350: 4000, 4351: 4000}}}
        }
    }
    init_val = {
        1: {"building_0": {"soc": {"tes": 1000, "bat": 500}}, "building_1": {"soc": {"tes": 1000, "bat": 500}}}
    }
    return buyer_info, seller_info, market_info, par_rh, options, opti_res, init_val
def test_calculate_results():
    buyer_info, seller_info, market_info, par_rh, options, opti_res, init_val = mock_data()
    results_time_step, results_month = calculate_results(buyer_info, seller_info, market_info, par_rh, options,
                                                         opti_res, init_val)

    # Inspect results
    print("Results Time Step:")
    for key, value in results_time_step.items():
        print(f"{key}: {value}")

    print("\nResults Month:")
    for key, value in results_month.items():
        print(f"{key}: {value}")


test_calculate_results()



