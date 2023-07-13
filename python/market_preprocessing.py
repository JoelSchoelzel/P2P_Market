import pymarket as pm
import numpy as np


def dict_for_market_data(pars_rh):

    mar_dict = {
        "transactions": {},
        "bid": {},
        "sorted_bids": {}
        }

    #mar_dict["markets"] = {}
    #mar_dict["dem_total"] = np.zeros(8760)
    #mar_dict["sup_total"] = np.zeros(8760)
    #mar_dict["clearing_price"] = np.zeros(8760)
    #mar_dict["stats"] = {}
    #mar_dict["tra_vol"] = {}         # total volume of each transaction for each participant / divided in bought and sold
    #mar_dict["adj_op"] = {}          # adjusted operation
    #mar_dict["tra_dem"] = {}         # traded demand
    #mar_dict["tra_dem_unflex"] = {}  # traded unflexible demand (--> p_max)
    #mar_dict["tra_gen"] = {}         # traded generation
    #mar_dict["plus_gen"] = {}        # surplus generation after trading
    #mar_dict["grid_dem"] = {}        # demand covered by superordinate grid
    #mar_dict["grid_gen"] = {}        # feed in superordinate grid
    #mar_dict["hp_dem"] = {}f
    #mar_dict["mar_op"] = {}          # operation after market clearing
    #mar_dict["unflex"] = {}          #Milena: safe unflexible demand or generation to calculate demand or generation that has to be covered by the grid
    #mar_dict["propensities"] = {}    # Milena: propensities for learning intelligence agent
    #mar_dict["auction"]["buy"] = {}
    #mar_dict["auction"]["sell"] = {}


    #for n_opt in range(pars_rh["n_opt"]):
        #for t in range(pars_rh["time_steps"][n_opt][0], pars_rh["time_steps"][n_opt][0] + pars_rh["n_hours_ch"], pars_rh["dt"]):
        #mar_dict["clearing_price"][pars_rh["time_steps"][n_opt][0]] = 0
        #mar_dict["stats"][n_opt] = {}
        #mar_dict["tra_vol"][n_opt] = {}
        #mar_dict["adj_op"][n_opt] = {}
        #mar_dict["tra_dem"][n_opt] = {}
        #mar_dict["tra_dem_unflex"][n_opt] = {}
        #mar_dict["grid_dem"][n_opt] = {}
        #mar_dict["tra_gen"][n_opt] = {}
        #mar_dict["plus_gen"][n_opt] = {}
        #mar_dict["grid_gen"][n_opt] = {}
        #mar_dict["mar_op"][n_opt] = {} # operation after market clearing
        #mar_dict["propensities"][n_opt] = {}

    return mar_dict


def bes(pars_rh, numb_bes):

    bes = {}
    for n in range(numb_bes):
        bes[n] = dict(adj_op = np.zeros(pars_rh["n_opt"]),
        tra_dem = np.zeros(pars_rh["n_opt"]),
        tra_dem_unflex = np.zeros(pars_rh["n_opt"]),
        tra_gen = np.zeros(pars_rh["n_opt"]),
        plus_gen = np.zeros(pars_rh["n_opt"]),
        grid_dem = np.zeros(pars_rh["n_opt"]),
        grid_gen = np.zeros(pars_rh["n_opt"]),
        hp_dem = np.zeros(pars_rh["n_opt"]),
        unflex = np.zeros(pars_rh["n_opt"]))

    return bes


def compute_bids(bes, opti_res, pars_rh, mar_agent_prosumer, n_opt, options, nodes, init_val):


    bid = {}

    for n in range(len(opti_res)):
        # get parameters for bidding
        t = pars_rh["time_steps"][n_opt][0]
        p_imp = opti_res[n][4][t]
        chp_sell = opti_res[n][8]["chp"][t]
        bid_strategy = options["bid_strategy"]

        dem_heat = nodes[n]["heat"][n_opt]
        dem_dhw = nodes[n]["dhw"][n_opt]
        if n_opt == 0:
            soc = opti_res[n][3]["tes"][t]
        else:
            soc = init_val[n_opt]["building_" + str(n)]["soc"]["tes"]

        power_hp = max(opti_res[n][1]["hp35"][t], opti_res[n][1]["hp55"][t])

        # compute bids
        if p_imp > 0.0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_hp_bids(p_imp, n, bid_strategy, dem_heat, dem_dhw, soc, power_hp, options)
            #bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = bid["bes_" + str(n)][1]

        elif chp_sell > 0:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_chp_bids(chp_sell, n, bid_strategy, dem_heat, dem_dhw, soc, options)
            #bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = 0

        else:
            bid["bes_" + str(n)], bes[n]["unflex"][n_opt] = mar_agent_prosumer[n].compute_empty_bids(n)
            #bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = 0

    return bid, bes


def sort_bids(bid, options, characs, n_opt):

    buy_list = {}
    sell_list = {}

    # sort by buy or sell
    for n in range(len(bid)):

        # don't consider bids with zero quantity
        if float(bid["bes_" + str(n)][1]) != 0.0:

            # add buying bids to buy_list
            if bid["bes_" + str(n)][2] == "True":
                i = len(buy_list)
                buy_list[i] = {
                    "price": bid["bes_" + str(n)][0],
                    "quantity": bid["bes_" + str(n)][1],
                    "building": bid["bes_" + str(n)][3]
                }

            # add selling bids to sell_list
            if bid["bes_" + str(n)][2] == "False":
                i = len(sell_list)
                sell_list[i] = {
                    "price": bid["bes_" + str(n)][0],
                    "quantity": bid["bes_" + str(n)][1],
                    "building": bid["bes_" + str(n)][3]
                }

    if options["crit_prio"] == "price":
        # sort lists by price
        if options["descending"]:
            # highest paying and lowest asking first
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"])
        else:
            # lowest paying and highest asking first
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"], reverse=True)

    else:
        for i in range(len(buy_list)):
            buy_list[i]["crit"] = characs[buy_list[i]["building"]][options["crit_prio"]][n_opt]
        for i in range(len(sell_list)):
            sell_list[i]["crit"] = characs[sell_list[i]["building"]][options["crit_prio"]][n_opt]

        if options["descending"]:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"], reverse=True)
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"], reverse=True)
        else:
            sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"])
            sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"])
    bids = {
        "buy": {},
        "sell": {}
    }

    for i in range(len(sorted_buy_list)):
        bids["buy"][i] = sorted_buy_list[i][1]
    for i in range(len(sorted_sell_list)):
        bids["sell"][i] = sorted_sell_list[i][1]

    return bids


def cost_and_rev_trans(trans, res):

    # calculate revenue and cost by adding quantity*price of each transaction
    for i in range(len(trans)):
        res["revenue"][trans[i]["seller"]] += (trans[i]["quantity"] * trans[i]["price"])
        res["cost"][trans[i]["buyer"]] += (trans[i]["quantity"] * trans[i]["price"])

    # calculate average trade price and total cost of all trades made in this n_opt
    if len(trans) > 0:
        res["average_trade_price"] = sum(res["cost"].values()) / sum(res["el_from_distr"].values())
        res["total_cost_trades"] = sum(res["cost"].values())

    return res


def clear_book(res, bids, params):

    for i in range(len(bids["buy"])):
        res["cost"][bids["buy"][i]["building"]] += (bids["buy"][i]["quantity"] * params["eco"]["pr","el"])
        res["el_from_grid"][bids["buy"][i]["building"]] += bids["buy"][i]["quantity"]
        bids["buy"][i]["quantity"] = 0

    for i in range(len(bids["sell"])):
        res["revenue"][bids["sell"][i]["building"]] += (bids["sell"][i]["quantity"] * params["eco"]["sell_chp"])
        res["el_to_grid"][bids["sell"][i]["building"]] += bids["sell"][i]["quantity"]
        bids["sell"][i]["quantity"] = 0

    return res, bids


def traded_volume(transaction, res):

    # add volumes traded within the district
    for i in range(len(transaction)):
        res["el_from_distr"][transaction[i]["buyer"]] += transaction[i]["quantity"]
        res["el_to_distr"][transaction[i]["seller"]] += transaction[i]["quantity"]

    return res


def grid_demands(bes, trade_res, options, bids, n_opt):

    for n in range(options["nb_bes"]):
        # only buying bids
        if bids["bes_" + str(n)][2] == "True":
            # check whether unflexible demand has been fulfilled, otherwise add remaining unflexible demand to grid_dem
            if bes[n]["unflex"][n_opt] > trade_res["el_from_distr"][n]:
                bes[n]["grid_dem"][n_opt] = bes[n]["unflex"][n_opt] - trade_res["el_from_distr"][n]

        # only selling bids
        if bids["bes_" + str(n)][2] == "False":
            # check whether unflexible surplus has been sold, otherwise add remaining unflexible surplus to grid_dem
            if bes[n]["unflex"][n_opt] > trade_res["el_to_distr"][n]:
                bes[n]["grid_gen"][n_opt] = bes[n]["unflex"][n_opt] - trade_res["el_to_distr"][n]
    return bes


def cost_and_rev_grid(bes, trade_res, options, n_opt, eco):

    for n in range(options["nb_bes"]):
        # add volume and revenue of elec sold to grid
        if bes[n]["grid_gen"][n_opt] > 0:
            trade_res["el_to_grid"][n] = bes[n]["grid_gen"][n_opt]
            trade_res["revenue"][n] += bes[n]["grid_gen"][n_opt] * eco["sell_chp"]

        # add volume and cost of elec bought from grid
        elif bes[n]["grid_dem"][n_opt] > 0:
            trade_res["el_from_grid"][n] = bes[n]["grid_dem"][n_opt]
            trade_res["cost"][n] += bes[n]["grid_dem"][n_opt] * eco["pr", "el"]

    return trade_res
