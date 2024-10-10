import pickle
import os
import numpy as np
import matplotlib.pyplot as plt
import parse_inputs
plt.rcParams["font.family"] = ["Latin Modern Roman"] 
plt.rcParams.update({'font.size': 16})

def load_results():
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\3_Mar\nB=3"
    
    init_val_path = os.path.join(directory, 'init_val_P2P.p')
    rows_path = os.path.join(directory, 'rows_P2P.p')
    opti_res_path = os.path.join(directory, 'opti_res_P2P.p')
    par_rh_path = os.path.join(directory, 'par_rh_P2P.p')
    mar_dict_path = os.path.join(directory, 'mar_dict_P2P.p')

    with open(init_val_path, "rb") as f:
        init_val = pickle.load(f)
    with open(rows_path, "rb") as f:
        rows = pickle.load(f)
    with open(opti_res_path, "rb") as f:
        opti_res = pickle.load(f)
    with open(par_rh_path, "rb") as f:
        par_rh = pickle.load(f)
    with open(mar_dict_path, "rb") as f:
        mar_dict = pickle.load(f)

    return init_val, rows, opti_res, par_rh, mar_dict

def simulation_plots_hp(rows, par_rh, opti_res, block_length, no_house): #plots for heat pump buildings
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\3_Mar\nB=3"
    
    grid_gen = []
    grid_load = []
    trade_sold = []
    trade_bought = []
    hp_elec = []
    elec_dem = []
    T_set_hp = []
    n_set_hp = []
    m_flow = []
    T_return = []
    T_sto_top = []
    T_sto_bot = []
    total_elec = []
    bat_fmu = []
    feed_in_share = []
    hp_elec = []
    hp_elec_opti = []
    soc_bat_opti = []
    t_tes_opti = []
    T_avg = []

    start = 16 # n_opt for the start time of evaluation
    #length = par_rh["n_opt"] - int(36/block_length)-1
    length = 24 # n_opt for the end time of evaluation
    step_size = 60
    no_house1 = 5

    #Optimierungsgrößen:
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            for i in range(60):
                hp_elec_opti.append(opti_res[l][no_house][1]["hp55"][block_step]/1000)
                soc_bat_opti.append((opti_res[l][no_house1][3]["bat"][block_step]/opti_res[l][no_house1][12]["bat"]) * 100)
                t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
    #Simulationsgrößen:
    for i in range(start*int((block_length * 3600)/step_size), length * int((block_length * 3600)/step_size)):
        bat_fmu.append(100 * rows[i][8][0])
        grid_gen.append(rows[i][1]/1000) # change from Wh to kWh
        grid_load.append(rows[i][2]/1000) # change from Wh to kWh
        T_sto_top.append(rows[i][3] - 273.15)
        T_sto_bot.append(rows[i][13] - 273.15)
        if rows[i][4] > 0:
            trade_sold.append(0)
            trade_bought.append(rows[i][4]/1000)
            if rows[i][6] >= rows[i][4]:
                feed_in_share.append(0)
            else:
                feed_in_share.append(100 * ((rows[i][4] - rows[i][6])/rows[i][4]))
        else:
            trade_sold.append(rows[i][4]/1000)
            trade_bought.append(0)
            feed_in_share.append(None)
        hp_elec.append(rows[i][6]/1000)
        elec_dem.append(rows[i][7]/1000)
        total_elec.append((rows[i][6]+rows[i][7])/1000)
        #trade_check.append(rows[i][4]/1000) # change from Wh to kWh
        T_set_hp.append(rows[i][9] - 273.15)
        n_set_hp.append(rows[i][10])
        m_flow.append(rows[i][11])
        T_return.append(rows[i][12] - 273.15)
        T_avg.append(rows[i][14] - 273.15)
    t = [par_rh["month_start"][par_rh["month"]] + i for i in range(start*block_length, length*block_length)]
    t_filtered = [t[i] for i in range(0, len(t), 10)]
    xtick_positions = np.arange(0, (length* block_length - start*block_length) * (3600 / step_size), int(3600 / step_size) * 10)
    
    plt.clf()
    plt.plot(T_set_hp, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.savefig(directory + '/plots_simu/T_set_hp', dpi = 600)
    plt.grid(True, linewidth = 0.5)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(T_return, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('return temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/T_return', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(T_avg, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Average TES temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/T_avg', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(m_flow, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('mass flow in kg/s', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/m_flow', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(T_sto_bot, label = 'Bottom Layer', color = 'tab:blue')
    plt.plot(T_sto_top, label = 'Top Layer', color = 'tab:red')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Top and Bottom Layer Temperatures', dpi = 600)
    #plt.show()
    print("HI")


    plt.clf()
    plt.plot(n_set_hp, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('relative heatpump speed', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/n_set_hp', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(bat_fmu, label = 'BAT-SOC after simulation', color = 'tab:blue')
    plt.plot(soc_bat_opti, label = 'BAT-SOC after optimization', color = 'tab:orange')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('SOC in %', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/SOC BAT Simulation vs Optimization', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(T_avg, label = 'After simulation', color = 'tab:blue')
    plt.plot(t_tes_opti, label = 'After optimization', color = 'tab:orange')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Average storage temperature  in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Storage temperature Simulation vs Optimization', dpi = 600)
    #plt.show()
    print("HI")


    plt.clf()
    plt.plot(feed_in_share, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.ylim(0, 100)
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Feed-in of the bought electricity in %', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    #plt.show()
    #print("HI")

    plt.clf()
    plt.plot(trade_bought, label = 'bought electricity', color = 'tab:green')
    plt.plot(hp_elec, label = 'HP electricity simulation', color = 'tab:blue')
    plt.plot(hp_elec_opti, label = 'HP electricity optimization', color = 'tab:red')
    #plt.plot(elec_dem, label = 'electric load profile', color = 'tab:red')
    plt.legend()
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.xlabel('time in h')
    plt.ylabel('electricity in kWh')
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('electricity in kWh', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Stromausnutzung Wärmepumpe', dpi = 600)
    #plt.show()
    print("HI")

    
    bat_opti = []
    soc_bat_fmu = []
    t_tes_opti = []
    t_tes_fmu = []
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            bat_opti.append(100 * (opti_res[l][no_house1][3]["bat"][block_step]/opti_res[l][5][12]["bat"]))
            t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
    for i in range(start * block_length, length * block_length):
        soc_bat_fmu.append(rows[i * step_size + step_size][8][0] * 100) #TODO Index noch nicht perfekt
        t_tes_fmu.append(rows[i * step_size + step_size][14] - 273.15) #TODO Index noch nicht perfekt
    
    plt.clf()
    plt.plot(soc_bat_fmu, label = 'BAT-SOC after simulation', color = 'tab:blue')
    plt.plot(bat_opti, label = 'BAT-SOC after optimization', color = 'tab:orange')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('SOC in %', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Init Val Vergleich SOC', dpi = 600)
    #plt.show()
    print("HI")
   
    #TODO dieser Plot nur so halb sinvoll bei blockBids, sind ja keine stündlihen Werte
    plt.clf()
    plt.plot(t_tes_fmu, label = 'After simulation', marker = 'o', color = 'tab:blue')
    plt.plot(t_tes_opti, label = 'After optimization', marker = 'x', color = 'tab:orange')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Average storage temperature  in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Init Val Vergleich Ttes', dpi = 600)
    #plt.show()
    print("HI")

    return 

def calc_results_p2p(par_rh, block_length, nego_results, opti_res, grid_transaction, params):

    last_n_opt = par_rh["n_opt"]
    time_steps = []
    for i in range(par_rh["hour_start"][0], par_rh["hour_start"][last_n_opt-1] + block_length):
        time_steps.append(i)

    # --------------------- DGOC --------------------- #

    total_p_purchase = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    total_feed_in = np.zeros(par_rh["time_steps"][par_rh["n_opt"]-1][-1] - par_rh["hour_start"][0])
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_p_purchase[t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000 # kW
                total_feed_in[t - par_rh["hour_start"][0]] += (opti_res[n_opt][n][8]["chp"][t] \
                                                              + opti_res[n_opt][n][8]["pv"][t]) / 1000 # kW

    denominator_dgoc = []
    numerator_dgoc = []
    for t in range(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]):
        numerator_dgoc.append(2 * min(total_p_purchase[t], total_feed_in[t]))
        denominator_dgoc.append(total_p_purchase[t] + total_feed_in[t])
    DGOC = sum(numerator_dgoc) / sum(denominator_dgoc)

    # --------------------- peak loads --------------------- #

    residual_load = total_p_purchase - total_feed_in
    peak_feed_in = -1*min(residual_load)  # kW
    if peak_feed_in < 0:
        peak_feed_in=0
    peak_purchase = max(residual_load)  # kW

    # --------------------- storage losses  --------------------- #

    bat_losses = []
    tes_losses = []
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                bat_losses.append(0.03 * (opti_res[n_opt][n][3]["bat"][t]
                                          + opti_res[n_opt][n][5]["bat"][t]
                                          + opti_res[n_opt][n][6]["bat"][t]))
                tes_losses.append(0.03 * opti_res[n_opt][n][3]["tes"][t])
    bat_losses = sum(bat_losses) /1000 # kWh
    tes_losses = sum(tes_losses) /1000 # kWh

    # --------------------- energy exchange with higher grid --------------------- #

    district_import = []
    district_export = []
    for t in range(len(residual_load)):
        if residual_load[t] > 0:
            district_import.append(residual_load[t])
        else:
            district_export.append(residual_load[t])
    district_import = sum(district_import)     # kWh
    district_export = sum(district_export) *-1 # kWh


    # --------------------- trade price, revenue, costs, gain  ---------------------

    traded_power = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    additional_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    saved_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    gain = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    for opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for round_nb in nego_results[opt]:
            for match in nego_results[opt][round_nb]:
                # valid_time_steps = {k: v for k, v in nego_results[opt][round_nb][match]["quantity"].items() if isinstance(k, int)}
                for t in range(par_rh["hour_start"][opt], par_rh["hour_start"][opt] + block_length):
                    if "quantity" in nego_results[opt][round_nb][match]:
                        if isinstance(nego_results[opt][round_nb][match]["quantity"][t], float):  # valid_time_steps
                            #price[t][match] = nego_results[opt][round_nb][match]["price"][t]  # €/kWh
                            traded_power[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["quantity"][t]/1000  # kWh
                            traded_power[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] +=  \
                                nego_results[opt][round_nb][match]["quantity"][t] / 1000  # kWh
                            additional_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["additional_revenue"][t]  # €/kWh
                            saved_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["saved_costs"][t]  # €/kWh
                            trading_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["trading_revenue"][t]  # €/kWh
                            trading_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] += \
                                nego_results[opt][round_nb][match]["trading_cost"][t]  # €/kWh
                            gain[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]] = \
                                saved_costs[nego_results[opt][round_nb][match]["buyer"], t- par_rh["hour_start"][0]]
                            gain[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]] = \
                                additional_revenue[nego_results[opt][round_nb][match]["seller"], t- par_rh["hour_start"][0]]

    traded_power_per_building = np.zeros(len(opti_res[0]))
    trading_costs_per_building  = np.zeros(len(opti_res[0]))
    saved_costs_per_building = np.zeros(len(opti_res[0]))
    trading_revenue_per_building  = np.zeros(len(opti_res[0]))
    additional_revenue_per_building = np.zeros(len(opti_res[0]))
    gain_per_building = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        traded_power_per_building[n] = np.sum(traded_power[n,:])
        trading_costs_per_building[n] = np.sum(trading_costs[n,:])
        saved_costs_per_building[n] = np.sum(saved_costs[n,:])
        trading_revenue_per_building[n] = np.sum(trading_revenue[n,:])
        additional_revenue_per_building[n] = np.sum(additional_revenue[n,:])
        gain_per_building[n] = np.sum(gain[n,:])

    traded_power_total = np.sum(traded_power_per_building)
    additional_revenue_total = np.sum(additional_revenue_per_building)
    saved_costs_total = np.sum(saved_costs_per_building)
    gain_total = np.sum(gain_per_building)
    trading_costs_total = np.sum(trading_costs_per_building)
    trading_revenue_total = np.sum(trading_revenue_per_building)

    av_prices_buy = trading_costs_total / traded_power_total
    av_prices_sell = trading_revenue_total / traded_power_total

    gain_total_over_time = np.zeros(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0])
    for t in range(par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]):
        gain_total_over_time[t] = np.sum(gain[:,t])

    # --------------------- absolute_energy_cost  --------------------- #

    total_cost = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    total_cost = total_cost + trading_costs - trading_revenue
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["costs_power_from_grid"][n][t] \
                                                        - grid_transaction[n_opt]["revenue_power_to_grid"][n][t] \
                                                        + opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"]
    total_cost_per_building = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        total_cost_per_building[n] = np.sum(total_cost[n,:])

    total_cost_without_LEM = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                total_cost_without_LEM[n,t - par_rh["hour_start"][0]] += opti_res[n_opt][n][16][t]/1000 * params["eco"]["gas"] \
                                                                        + opti_res[n_opt][n][4]["p_imp"]["p_imp"][t] / 1000* params["eco"]["pr", "el"] \
                                                                        - (opti_res[n_opt][n][8]["chp"][t] + opti_res[n_opt][n][8]["pv"][t]) / 1000*params["eco"]["sell_pv"] # kW
    total_cost_without_LEM_per_building = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):
        total_cost_without_LEM_per_building[n] = np.sum(total_cost_without_LEM[n,:])

    # ----------- traded supply and demand quantities   ---------------------

    denominator_total_demand = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    denominator_total_supply = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_demand = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    nominator_total_supply = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                denominator_total_demand[n, t - par_rh["hour_start"][0]] += opti_res[n_opt][n][4]["p_imp"]["p_imp"][t]/1000
                denominator_total_supply[n, t - par_rh["hour_start"][0]] += opti_res[n_opt][n][8]["chp"][t]/1000 \
                                                            + opti_res[n_opt][n][8]["pv"][t]/1000
                if denominator_total_demand[n, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_demand[n, t - par_rh["hour_start"][0]] = traded_power[n, t - par_rh["hour_start"][0]]
                if denominator_total_supply[n, t - par_rh["hour_start"][0]] > 0:
                    nominator_total_supply[n, t - par_rh["hour_start"][0]] = traded_power[n, t - par_rh["hour_start"][0]]

    mSCF_bd = {}
    mDCF_bd = {}
    for n in range(len(opti_res[0])):
        if sum(denominator_total_supply[n,:]) != 0:
            mSCF_bd[n] = sum(nominator_total_supply[n,:]) / sum(denominator_total_supply[n,:])
        if sum(denominator_total_demand[n, :]) != 0:
            mDCF_bd[n] =  sum(nominator_total_demand[n,:]) / sum(denominator_total_demand[n,:])

    mSCF = sum(sum(nominator_total_supply)) / sum(sum(denominator_total_supply))
    mDCF =  sum(sum(nominator_total_demand)) / sum(sum(denominator_total_demand))

    # --------------------- STORE THE RESULTS ---------------------

    results = {

        "DGOC": DGOC,
        "peak_feed_in": peak_feed_in,
        "peak_purchase": peak_purchase,
        "district_import": district_import,
        "district_export": district_export,

        "traded_power": traded_power,
        "additional_revenue": additional_revenue,
        "saved_costs": saved_costs,
        "gain": gain,
        "gain_total_over_time": gain_total_over_time,

        "traded_power_per_building": traded_power_per_building,
        "trading_costs_per_building": trading_costs_per_building,
        "saved_costs_per_building": saved_costs_per_building,
        "trading_revenue_per_building": trading_revenue_per_building,
        "additional_revenue_per_building": additional_revenue_per_building,
        "gain_per_building": gain_per_building,

        "traded_power_total" : traded_power_total,
        "additional_revenue_total": additional_revenue_total,
        "saved_costs_total": saved_costs_total,
        "gain_total": gain_total,
        "trading_costs_total": trading_costs_total,
        "trading_revenue_total": trading_revenue_total,
        "av_prices_buy": av_prices_buy,
        "av_prices_sell": av_prices_sell,

        "total_cost": total_cost,
        "total_cost_per_building": total_cost_per_building,
        "total_cost_without_LEM_per_building": total_cost_without_LEM_per_building,

        "traded_supply_bids_per_building": mSCF_bd,
        "traded_demands_bids_per_building": mDCF_bd,
        "traded_supply_bids": mSCF,
        "traded_demand_bids": mDCF,

        "bat_losses": bat_losses,
        "tes_losses": tes_losses,

        "residual_load":residual_load,
        "total_p_purchase":total_p_purchase,
        "total_feed_in": total_feed_in,
        }
    return results

def p2p_plots(results, par_rh, opti_res, block_length):
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\3_Mar\nB=3"

    plt.clf()
    plt.bar(0-0.2, results["total_cost_per_building"][1], width = 0.4, color="darkcyan", zorder = 2, label = "With LEM")
    plt.bar(0+0.2, results["total_cost_without_LEM_per_building"][1], width = 0.4, color="lightblue", zorder = 2, label = "Without LEM")
    pos = 1
    for i in [6, 8, 11]:
        plt.bar(pos-0.2, results["total_cost_per_building"][i], width = 0.4, color="darkcyan", zorder = 2)
        plt.bar(pos+0.2, results["total_cost_without_LEM_per_building"][i], width = 0.4, color="lightblue", zorder = 2)
        pos +=1
    plt.ylabel('Total costs in €')
    plt.xticks(np.arange(4), ['SFH\nPV+BOI','SFH\nHP+BAT','SFH\nHP','MFH\nCHP'], fontsize = "14")
    plt.xlabel('LEM house types')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "14", ncol = 2)
    plt.yticks([200, 400, 600, 800], fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Total costs per building', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0, 100*results["traded_supply_bids"], color="darkcyan", label = "SCF", width = 0.5, zorder = 2)
    plt.bar(1, 100*results["traded_demand_bids"], color="lightblue", label = "DCF", width = 0.5, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(2), ['mSCF','mDCF'])
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/plots_p2p/mSCF mDCF', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.plot(results["total_p_purchase"], color = 'tab:green', label = "Import")
    plt.plot(results["total_feed_in"], color = 'tab:red', label = "Feed-in")
    plt.ylabel('Electricity in kWh')
    plt.xlabel('Time in h')
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Electricity imports vs feed-in', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    #plt.plot(results["traded_power"][6][:96], color = 'tab:red', label = "SFH HP+BAT")
    #plt.plot(results["traded_power"][1][:96], color = 'tab:green', label = "SFH PV+Boi")
    plt.step(range(96), results["traded_power"][6][:96], color = 'tab:orange', label = "SFH HP+BAT")
    plt.step(range(96), results["traded_power"][1][:96], color = 'tab:blue', label = "SFH PV+Boi")
    plt.ylabel('Electricity in kWh')
    plt.xlabel('Time in h')
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Traded power over time', dpi = 600)
    plt.show()
    print("Hi")

    plt.clf()
    for i in range(len(results["gain_per_building"])):
        plt.bar(i, results["gain_per_building"][i], color="darkcyan", zorder = 2)
    plt.ylabel('Gain in €')
    plt.xticks(np.arange(12), ['1','2','3','4','5','6','7','8','9','10','11','12'])
    plt.xlabel('LEM houses')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.yticks([40, 80, 120, 160, 200, 240, 280, 320])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Gain per building', dpi = 600)
    plt.show()
    print("Hi")


    return

block_length = 3
init_val, rows, opti_res, par_rh, mar_dict = load_results()
params = parse_inputs.read_economics()
results = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
p2p_plots(results=results, par_rh=par_rh, opti_res=opti_res, block_length=block_length)
#simulation_plots_hp(rows=rows, par_rh=par_rh, opti_res=opti_res, block_length=block_length, no_house=8)
print("HI")
