import pickle
import os
import numpy as np
import matplotlib.pyplot as plt
import parse_inputs
#plt.rcParams["font.family"] = ["Latin Modern Roman"] 
plt.rcParams.update({'font.size': 14})

import matplotlib.font_manager as fm
font_path = 'font/lmroman10-regular.otf'
lm_font = fm.FontProperties(fname=font_path)
fm.fontManager.addfont(font_path) 
plt.rcParams["font.family"] = ["Latin Modern Roman"] 


def load_results(scenario, block_length, monthly):
    if monthly:
        directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario) + "\\results_month"
    else:
        directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario)

    init_val_path = os.path.join(directory, 'init_val_P2P.p')
    rows6_path = os.path.join(directory, 'rows6_P2P.p')
    rows8_path = os.path.join(directory, 'rows8_P2P.p')
    rows11_path = os.path.join(directory, 'rows11_P2P.p')
    rows_all_path = os.path.join(directory, 'rows_all_P2P.p')
    nodes_path = os.path.join(directory, 'nodes_P2P.p')
    opti_res_path = os.path.join(directory, 'opti_res_P2P.p')
    par_rh_path = os.path.join(directory, 'par_rh_P2P.p')
    mar_dict_path = os.path.join(directory, 'mar_dict_P2P.p')

    with open(init_val_path, "rb") as f:
        init_val = pickle.load(f)
    with open(nodes_path, "rb") as f:
        nodes = pickle.load(f)
    with open(rows6_path, "rb") as f:
        rows6 = pickle.load(f)
    with open(rows8_path, "rb") as f:
        rows8 = pickle.load(f)
    with open(rows11_path, "rb") as f:
        rows11 = pickle.load(f)
    with open(rows_all_path, "rb") as f:
        rows_all = pickle.load(f)
    with open(opti_res_path, "rb") as f:
        opti_res = pickle.load(f)
    with open(par_rh_path, "rb") as f:
        par_rh = pickle.load(f)
    with open(mar_dict_path, "rb") as f:
        mar_dict = pickle.load(f)

    rows = {}
    rows["6"] = rows6
    rows["8"] = rows8
    rows["11"] = rows11
    rows["all"] = rows_all

    #return init_val, rows6, rows8, rows11, rows_all, nodes, opti_res, par_rh, mar_dict
    return init_val, rows, nodes, opti_res, par_rh, mar_dict

def simulation_plots_hp(rows, rows_all, par_rh, opti_res, scenario, block_length, no_house, nodes): #plots for heat pump buildings
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario)
    
    #length = par_rh["n_opt"] - int(36/block_length)-1
    if block_length == 3:
        start = 8 # n_opt for the start time of evaluation
        length = 24 # n_opt for the end time of evaluation
    elif block_length == 6:
        start = 4 # n_opt for the start time of evaluation
        length = 12 # n_opt for the end time of evaluation
    step_size = 60
    no_house1 = 5


    grid_gen = []
    grid_load = []
    trade_sold = []
    trade_bought = []
    hp_elec = []
    hp_heat = []
    elec_dem = []
    heat_dem = []
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
    T_avg_dhw = []
    T_top_dhw = []
    T_bot_dhw = []
    Q_tra_gain = []
    grid_buy_opti = []
    grid_sell_opti = []
    pv_gen = []
    chp_gen = []
    dhw_dem = []
    T_room = []
    T_room_set = []
    solar_irrad = []
    not_used_elec = []

    #Optimierungsgrößen:
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            for i in range(60):
                hp_elec_opti.append(opti_res[l][no_house][1]["hp55"][block_step]/1000)
                dhw_dem.append(nodes[no_house]["dhw"][block_step]/1000)
                if no_house == 6:
                    soc_bat_opti.append((opti_res[l][no_house][3]["bat"][block_step]/opti_res[l][no_house][12]["bat"]) * 100)
                t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
                grid_buy_opti.append(opti_res[l][no_house][17][block_step]/1000)
                grid_sell_opti.append(opti_res[l][no_house][18][block_step]/1000)
    #Simulationsgrößen:
    for i in range(start*int((block_length * 3600)/step_size), length * int((block_length * 3600)/step_size)):
        grid_gen.append(rows[i][1]/1000) # change from Wh to kWh
        grid_load.append(rows[i][2]/1000) # change from Wh to kWh
        T_sto_top.append(rows[i][6] - 273.15)
        T_sto_bot.append(rows[i][8] - 273.15)
        if rows[i][3] > 0:
            trade_sold.append(0)
            trade_bought.append(rows[i][3]/1000)
        else:
            trade_sold.append(rows[i][3]/1000)
            trade_bought.append(0)
        heat_dem.append(rows[i][4]/1000)
        hp_elec.append(rows[i][5]/1000)
        hp_heat.append(rows[i][15]/1000)
        #trade_check.append(rows[i][4]/1000) # change from Wh to kWh
        T_set_hp.append(rows[i][7] - 273.15)
        n_set_hp.append(rows[i][12])
        m_flow.append(rows[i][13])
        T_return.append(rows[i][9] - 273.15)
        T_avg.append(rows[i][10] - 273.15)
        T_avg_dhw.append(rows[i][11] - 273.15)
        Q_tra_gain.append(rows[i][14]/1000)
        T_room_set.append(20)
        if scenario == "\\ROM_2Sto":
            if no_house == 6:
                T_room.append(rows[i][19] - 273.15)
            elif no_house == 8:
                T_room.append(rows[i][16] - 273.15)
        if no_house == 6:
                solar_irrad.append(rows[i][20])
        elif no_house == 8:
            solar_irrad.append(rows[i][17])
            print("hi")
        
        if no_house == 6:
            bat_fmu.append(100 * rows[i][16])
            T_top_dhw.append(rows[i][17] - 273.15)
            T_bot_dhw.append(rows[i][18] - 273.15)
        pv_gen.append(rows_all[i][2]/1000)
        chp_gen.append(rows_all[i][11]/1000)

    for i in range((length - start) * step_size * block_length):
        diff = trade_bought[i] - hp_elec[i]
        if diff >= 0:
            not_used_elec.append(diff/60)
        else:
            not_used_elec.append(0)
    feed_in_share = sum(not_used_elec)/(sum(trade_bought)/60)   

    t = [par_rh["month_start"][par_rh["month"]] + i for i in range(start*block_length, length*block_length)]
    t_filtered = [t[i] for i in range(0, len(t), 10)]
    xtick_positions = np.arange(0, (length* block_length - start*block_length) * (3600 / step_size), int(3600 / step_size) * 10)
    """
    # Multiple Plot 1
    fig, axs = plt.subplots(5, 1, figsize=(10, 8), sharex=True)
    axs[0].plot(T_sto_top, 'r-', label='Oben')
    axs[0].plot(T_sto_bot, 'b', label='Unten')
    axs[0].set_ylabel('T$_{TES}$ in °C')
    axs[0].set_title('Obere und untere Temperatur im Heizungsspeicher')
    axs[0].legend(fontsize=14)

    axs[1].plot(trade_bought, 'g-')
    axs[1].set_ylabel('P$_{el}$ in kW')
    axs[1].set_title('Gekaufte elektrische Leistung')

    axs[2].plot(dhw_dem, 'b', label = 'TWW')
    axs[2].plot(heat_dem, 'r--', label='Heizung')
    axs[2].set_ylabel(r'$\dot{Q}' + '_{th}$ in kW')
    axs[2].set_title('Wärmebedarf für Heizung und TWW')

    axs[3].plot(T_avg_dhw, color = "lightcoral")
    axs[3].set_ylabel('T$_{avg,TWW}$ in °C')
    axs[3].set_title('Durchschnittliche Temperatur im TWW-Speicher')

    axs[4].plot(pv_gen, color = "orange")
    axs[4].set_ylabel('P$_{el}$ in kW')
    axs[4].set_title('PV- Stromerzeugung')
    axs[4].legend(fontsize=14)
    axs[4].set_xlabel('Zeit in h')
    for ax in axs:
        plt.xticks(xtick_positions, t_filtered, fontsize=16)
        #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
        ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
    plt.tight_layout()
    plt.savefig(directory + '/plots_simu/MultiplePlots1', dpi = 600)
    #plt.show()

    # Multiple Plot 2
    fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    axs[0].plot(T_avg, 'b-', label='Simulation')
    axs[0].plot(t_tes_opti, color = "orange", label='Optimierung')
    axs[0].set_ylabel('T$_{avg,TES}$ in °C')
    axs[0].set_title('Durchschnittliche Temperatur im Heizungsspeicher')
    axs[0].legend(fontsize=14)

    axs[1].plot(trade_bought, 'r--', label = 'Handelsstrom')
    axs[1].plot(hp_elec, 'g-', label='Wärmepumpe')
    axs[1].set_ylabel('P$_{el}$ in kW')
    axs[1].set_title('Kompressorleistung der WP und gekaufte Leistung')
    axs[1].legend(fontsize=14)

    axs[2].plot(n_set_hp, color = "black")
    axs[2].set_ylabel('n$_{rel}$')
    axs[2].set_title('Wärmepumpendrehzahl')

    axs[3].plot(heat_dem, 'r--')
    axs[3].set_ylabel(r'$\dot{Q}' + '_{th}$ in kW')
    axs[3].set_title('Wärmebedarf')
    for ax in axs:
        plt.xticks(xtick_positions, t_filtered, fontsize=16)
        #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
        ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
    plt.tight_layout()
    plt.savefig(directory + '/plots_simu/MultiplePlots2', dpi = 600)
    #plt.show()
    """

    
    if scenario == "\\ROM_2Sto":
        # Multiple Plot 9
        fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axs[0].plot(trade_bought, 'r--', label = 'Handelsstrom')
        axs[0].plot(hp_elec, 'g-', label='Wärmepumpe')
        axs[0].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
        axs[0].set_title('Kompressorleistung der WP und gekaufter Strom')
        axs[0].legend(fontsize=14, loc = 'upper right')

        axs[1].plot(n_set_hp, color = "black")
        axs[1].set_ylabel('$\mathregular{n_{rel}}$', fontsize = 16)
        axs[1].set_title('Wärmepumpendrehzahl')

        axs[2].plot(T_sto_top, 'r-', label='Oben')
        axs[2].plot(T_sto_bot, 'b', label='Unten')
        axs[2].set_ylabel('$\mathregular{T_{TES}}$ in °C', fontsize = 16)
        axs[2].set_title('Obere und untere Temperatur im Heizungsspeicher')
        axs[2].legend(fontsize=14)
        axs[2].set_xlabel('Zeit in h', fontsize = 16)
        for ax in axs:
            plt.xticks(xtick_positions, t_filtered, fontsize=16)
            #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
            ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
        plt.tight_layout()
        #plt.show()
        plt.savefig(directory + '/plots_simu/MultiplePlots9', dpi = 600)
 
        
        # Multiple Plot 4
        fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
        axs[0].plot(T_avg, 'b-', label='Simulation')
        axs[0].plot(t_tes_opti, color = "orange", label='Optimierung')
        axs[0].set_ylabel('$\mathregular{T_{avg,TES}}$ in °C', fontsize = 16)
        axs[0].set_title('Durchschnittliche Temperatur im Heizungsspeicher')
        axs[0].legend(fontsize=14, loc = 'lower left')

        axs[1].plot(heat_dem, 'r--', label = '5R1C')
        axs[1].plot(Q_tra_gain, 'b-', label = '23R4C')
        axs[1].set_ylabel(r'$\mathregular{\dot{Q}}$' + '$\mathregular{_{Bedarf}}$ in kW', fontsize = 16)
        axs[1].set_title('Wärmebedarf 23R4C vs. 5R1C')
        axs[1].legend(fontsize=14, loc = 'upper right')

        axs[2].plot(T_room, 'r', label = '$\mathregular{T_{Raum}}$', zorder = 2)
        axs[2].plot(T_room_set, color = 'lightsalmon', label = '$\mathregular{T_{Raum,soll}}$', zorder = 1)
        axs[2].set_ylabel('$\mathregular{T_{Raum}}$ in °C', fontsize = 16)
        axs[2].set_title('Raumtemperatur')
        axs[2].legend(fontsize=14,loc = 'lower right')

        axs[3].plot(solar_irrad, color = "orange")
        axs[3].set_ylabel('GHI in W/m$^{2}$', fontsize = 16)
        axs[3].set_title('Globale horizontale Strahlung')
        axs[3].set_xlabel('Zeit in h', fontsize = 16)
        for ax in axs:
            plt.xticks(xtick_positions, t_filtered, fontsize=16)
            #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
            ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
        plt.tight_layout()
        plt.savefig(directory + '/plots_simu/MultiplePlots4', dpi = 600)
        #plt.show()

    if scenario == "\\HeatDem_2Sto":
        if no_house == 8:
            # Multiple Plot 5
            fig, axs = plt.subplots(5, 1, figsize=(10, 8), sharex=True)
            axs[0].plot(trade_bought, 'r--', label = 'Handelsstrom')
            axs[0].plot(hp_elec, 'g-', label='Wärmepumpe')
            axs[0].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
            axs[0].set_title('Kompressorleistung der WP und gekaufter Strom')
            axs[0].legend(fontsize=14, loc = 'upper left')

            axs[1].plot(n_set_hp, color = "black")
            axs[1].set_ylabel('$\mathregular{n_{rel}}$', fontsize = 16)
            axs[1].set_title('Wärmepumpendrehzahl')

            axs[2].plot(T_set_hp, color = 'chocolate')
            axs[2].set_ylabel('$\mathregular{T_{soll}}$ in °C', fontsize = 16)
            axs[2].set_title('Sollvorlauftemperatur')

            axs[3].plot(T_sto_top, 'r-', label='Oben')
            axs[3].plot(T_sto_bot, 'b', label='Unten')
            axs[3].set_ylabel('$\mathregular{T_{TES}}$ in °C', fontsize = 16)
            axs[3].set_title('Obere und untere Temperatur im Heizungsspeicher')
            axs[3].legend(fontsize=14, loc = 'upper left')

            #axs[4].plot(T_top_dhw, 'r-', label='Oben')
            #axs[4].plot(T_bot_dhw, 'b', label='Unten')
            axs[4].plot(T_avg_dhw, color = 'lightcoral')
            axs[4].set_ylabel('$\mathregular{T_{TES}}$ in °C', fontsize = 16)
            axs[4].set_title('Durchschnittliche Temperatur im TWW-Speicher')
            #axs[4].set_title('Obere und untere Temperatur im TWW-Speicher')
            #axs[4].legend(fontsize=14)
            axs[4].set_xlabel('Zeit in h', fontsize = 16)
            for ax in axs:
                plt.xticks(xtick_positions, t_filtered, fontsize=16)
                #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
                ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
            plt.tight_layout()
            plt.savefig(directory + '/plots_simu/MultiplePlots5', dpi = 600)
            #plt.show()

        # Multiple Plot 7
        fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axs[0].plot(T_avg, 'b-', label='Simulation')
        axs[0].plot(t_tes_opti, color = "orange", label='Optimierung')
        axs[0].set_ylabel('$\mathregular{T_{avg,TES}}$ in °C', fontsize = 16)
        axs[0].set_title('Durchschnittliche Temperatur im Heizungsspeicher')
        axs[0].legend(fontsize=14, loc = 'upper left')

        axs[1].plot(hp_heat, 'g-')
        axs[1].set_ylabel(r'$\mathregular{\dot{Q}}$' + '$\mathregular{_{th}}$ in kW', fontsize = 16)
        axs[1].set_title('Wärmeerzeugung der WP')

        axs[2].plot(dhw_dem, 'b', label = 'TWW')
        axs[2].plot(heat_dem, 'r--', label='Heizung')
        axs[2].set_ylabel(r'$\mathregular{\dot{Q}}$' + '$\mathregular{_{Bedarf}}$ in kW', fontsize = 16) 
        axs[2].set_title('Wärmebedarf für Heizung und TWW')
        axs[2].legend(fontsize=14)
        axs[2].set_xlabel('Zeit in h', fontsize = 16)
        for ax in axs:
            plt.xticks(xtick_positions, t_filtered, fontsize=16)
            #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
            ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
        plt.tight_layout()
        plt.savefig(directory + '/plots_simu/MultiplePlots7', dpi = 600)
        #plt.show()

        
        if no_house == 6:
            # Multiple Plot 3
            fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
            axs[0].plot(bat_fmu, 'b-', label='Simulation')
            axs[0].plot(soc_bat_opti, color = "orange", label='Optimierung')
            axs[0].set_ylabel('SOC in %', fontsize = 16)
            axs[0].set_title('SOC der BAT')
            axs[0].legend(fontsize=14, loc = 'upper left')

            axs[1].plot(trade_bought, 'r--', label = 'Handelsstrom')
            axs[1].plot(hp_elec, 'g-', label='Wärmepumpe')
            axs[1].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
            axs[1].set_title('Kompressorleistung der WP und gekaufter Strom')
            axs[1].legend(fontsize=14, loc = 'upper left')
            axs[1].set_xlabel('Zeit in h', fontsize = 16)
            for ax in axs:
                plt.xticks(xtick_positions, t_filtered, fontsize=16)
                #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
                ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
            plt.tight_layout()
            plt.savefig(directory + '/plots_simu/MultiplePlots3', dpi = 600)
            #plt.show()

            # Multiple Plot 5
            fig, axs = plt.subplots(5, 1, figsize=(10, 8), sharex=True)
            axs[0].plot(trade_bought, 'r--', label = 'Handelsstrom')
            axs[0].plot(hp_elec, 'g-', label='Wärmepumpe')
            axs[0].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
            axs[0].set_title('Kompressorleistung der WP und gekaufter Strom')
            axs[0].legend(fontsize=14, loc = 'upper left')

            axs[1].plot(n_set_hp, color = "black")
            axs[1].set_ylabel('$\mathregular{n_{rel}}$', fontsize = 16)
            axs[1].set_title('Wärmepumpendrehzahl')

            axs[2].plot(T_set_hp, color = 'chocolate')
            axs[2].set_ylabel('$\mathregular{T_{soll}}$ in °C', fontsize = 16)
            axs[2].set_title('Sollvorlauftemperatur')

            axs[3].plot(T_sto_top, 'r-', label='Oben')
            axs[3].plot(T_sto_bot, 'b', label='Unten')
            axs[3].set_ylabel('$\mathregular{T_{TES}}$ in °C', fontsize = 16)
            axs[3].set_title('Obere und untere Temperatur im Heizungsspeicher')
            axs[3].legend(fontsize=14, loc = 'upper left')

            axs[4].plot(bat_fmu, color = 'firebrick')
            axs[4].set_ylabel('$\mathregular{SOC_{BAT}}$ in %', fontsize = 16)
            axs[4].set_title('SOC der BAT')
            axs[4].set_xlabel('Zeit in h', fontsize = 16)
 

            #axs[4].plot(T_top_dhw, 'r-', label='Oben')
            #axs[4].plot(T_bot_dhw, 'b', label='Unten')
            #axs[4].plot(T_avg_dhw, color = 'lightcoral')
            #axs[4].set_ylabel('T$_{TES}$ in °C')
            #axs[4].set_title('Durchschnittliche Temperatur im TWW-Speicher')
            #axs[4].set_title('Obere und untere Temperatur im TWW-Speicher')
            #axs[4].legend(fontsize=14)
            for ax in axs:
                plt.xticks(xtick_positions, t_filtered, fontsize=16)
                #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
                ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
            plt.tight_layout()
            plt.savefig(directory + '/plots_simu/MultiplePlots5', dpi = 600)
            #plt.show()


    # Multiple Plot 6
    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axs[0].plot(trade_bought, 'g-')
    axs[0].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
    axs[0].set_title('Gekaufte elektrische Leistung')

    axs[1].plot(pv_gen, color = "orange")
    axs[1].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
    axs[1].set_title('PV- Stromerzeugung')

    axs[2].plot(chp_gen, color = "maroon")
    axs[2].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
    axs[2].set_title('BHKW- Stromerzeugung')
    axs[2].set_xlabel('Zeit in h', fontsize = 16)
    for ax in axs:
        plt.xticks(xtick_positions, t_filtered, fontsize=16)
        #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
        ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
    plt.tight_layout()
    plt.savefig(directory + '/plots_simu/MultiplePlots6', dpi = 600)
    #plt.show()

    

    
    if scenario == "\\HeatDem_CombiSto":
    # Multiple Plot 8
        fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axs[0].plot(T_avg, 'b-', label='Simulation')
        axs[0].plot(t_tes_opti, color = "orange", label='Optimierung')
        axs[0].set_ylabel('$\mathregular{T_{avg,TES}}$ in °C', fontsize = 16)
        axs[0].set_title('Durchschnittliche Temperatur im Heizungsspeicher')
        axs[0].legend(fontsize=14, loc = 'lower left')

        axs[1].plot(trade_bought, 'r--', label = 'Handelsstrom')
        axs[1].plot(hp_elec, 'g-', label='Wärmepumpe')
        axs[1].set_ylabel('$\mathregular{P_{el}}$ in kW', fontsize = 16)
        axs[1].set_title('Kompressorleistung der WP und gekaufter Strom')
        axs[1].legend(fontsize=14, loc = 'lower left')

        axs[2].plot(heat_dem, 'r--')
        axs[2].set_ylabel(r'$\mathregular{\dot{Q}}$' + '$\mathregular{_{Bedarf}}$ in kW', fontsize = 16)
        axs[2].set_title('Wärmebedarf')
        axs[2].set_xlabel('Zeit in h', fontsize = 16)


        for ax in axs:
            plt.xticks(xtick_positions, t_filtered, fontsize=16)
            #ax.set_xticks(np.arange(0, 49, 6))  # Ticks alle 6 Stunden
            ax.grid(True, which='both', axis='x', linestyle='-', color='lightgray', linewidth=0.5)  # Vertikale Linien
        plt.tight_layout()
        plt.savefig(directory + '/plots_simu/MultiplePlots8', dpi = 600)
        #plt.show()

    # Einzelplots

    plt.clf()
    plt.plot(T_set_hp, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Set temperature in °C', fontsize=18)
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

    if no_house == 6:
        plt.clf()
        plt.plot(T_bot_dhw, label = 'Bottom Layer', color = 'tab:blue')
        plt.plot(T_top_dhw, label = 'Top Layer', color = 'tab:red')
        plt.xticks(xtick_positions, t_filtered, fontsize=16)
        plt.legend(fontsize=16, loc = 'upper right')
        plt.xlabel('time in h', fontsize=18)
        plt.ylabel('Temperature in °C', fontsize=18)
        plt.tight_layout()
        plt.grid(True, linewidth = 0.5)
        plt.savefig(directory + '/plots_simu/DHW Top and Bottom Layer Temperatures', dpi = 600)
        #plt.show()
        print("HI")

    plt.clf()
    plt.plot(T_avg_dhw, color = 'tab:red')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Average TES temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Average DHW TES temperature', dpi = 600)
    #plt.show()
    print("HI")

    
    plt.clf()
    plt.plot(heat_dem, label = "Heat Demand DG", color = 'tab:red')
    plt.plot(Q_tra_gain, label = "Heat Transfer ROM", color = 'tab:blue')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Heat in kW', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Comparison room heat power', dpi = 600)
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

    if no_house == 6:
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
    plt.plot(trade_bought, label = 'bought electricity', color = 'tab:red')
    plt.plot(hp_elec, label = 'HP electricity simulation', color = 'tab:green')
    plt.plot(hp_elec_opti, label = 'HP electricity optimization', color = 'tab:blue')
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
    plt.savefig(directory + '/plots_simu/Stromausnutzung Wärmepumpe 1', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(trade_bought, label = 'bought electricity', color = 'tab:red')
    plt.plot(hp_elec, label = 'HP electricity simulation', color = 'tab:green')
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
    plt.savefig(directory + '/plots_simu/Stromausnutzung Wärmepumpe 2', dpi = 600)
    #plt.show()
    print("HI")

    
    bat_opti = []
    soc_bat_fmu = []
    t_tes_opti = []
    t_tes_fmu = []
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            if no_house == 6:
                bat_opti.append(100 * (opti_res[l][no_house][3]["bat"][block_step]/opti_res[l][no_house][12]["bat"]))
            t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
    for i in range(start * block_length, length * block_length):
        if no_house == 6:
            soc_bat_fmu.append(rows[i * step_size + step_size][16] * 100) #TODO Index noch nicht perfekt
        t_tes_fmu.append(rows[i * step_size + step_size][10] - 273.15) #TODO Index noch nicht perfekt
    
    if no_house == 6:
        plt.clf()
        plt.plot(soc_bat_fmu, label = 'BAT-SOC after simulation', marker = 'o', color = 'tab:blue')
        plt.plot(bat_opti, label = 'BAT-SOC after optimization', marker = 'x', color = 'tab:orange')
        #plt.xticks(xtick_positions, t_filtered, fontsize=16)
        #xticks = np.arange(block_length*start, block_length*length, 10)
        xticks = np.arange(0, block_length*(length-start), 10)
        xtick_labels = np.arange(1416+block_length*start, 1416+block_length*length, 10)
        plt.xticks(xticks, xtick_labels)
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
    #plt.xticks(xtick_positions, t_filtered, fontsize=16)
    #xticks = np.arange(block_length*start, block_length*length, 10)
    xticks = np.arange(0, block_length*(length-start), 10)
    xtick_labels = np.arange(1416+block_length*start, 1416+block_length*length, 10)
    plt.xticks(xticks, xtick_labels)
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Average storage temperature  in °C', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Init Val Vergleich Ttes', dpi = 600)
    #plt.show()
    print("HI")

    return 

def simulation_plots_chp(rows, no_house, par_rh, opti_res, scenario, block_length): #plots for chp buildings
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario)
    
    #length = par_rh["n_opt"] - int(36/block_length)-1
    if block_length == 3:
        start = 0 # n_opt for the start time of evaluation
        length = 24 # n_opt for the end time of evaluation
    elif block_length == 6:
        start = 0 # n_opt for the start time of evaluation
        length = 4 # n_opt for the end time of evaluation
    step_size = 60


    trade_sold = []
    trade_bought = []
    heat_dem = []
    T_set_chp = []
    n_set_chp = []
    T_sto_top = []
    T_sto_bot = []
    chp_elec = []
    chp_heat = []
    chp_elec_opti = []
    t_tes_opti = []
    T_avg = []
    Q_tra_gain = []

    #Optimierungsgrößen:
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            for i in range(60):
                chp_elec_opti.append(opti_res[l][no_house][1]["chp"][block_step]/1000)
                t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
    #Simulationsgrößen:
    for i in range(start*int((block_length * 3600)/step_size), length * int((block_length * 3600)/step_size)):
        T_sto_top.append(rows[i][5] - 273.15)
        T_sto_bot.append(rows[i][7] - 273.15)
        if rows[i][3] > 0:
            trade_sold.append(0)
            trade_bought.append(rows[i][3]/1000)
        else:
            trade_sold.append(-1*rows[i][3]/1000)
            trade_bought.append(0)
        heat_dem.append(rows[i][4]/1000)
        chp_heat.append(rows[i][10]/1000)
        chp_elec.append(rows[i][11]/1000)
        #trade_check.append(rows[i][4]/1000) # change from Wh to kWh
        T_set_chp.append(rows[i][6] - 273.15)
        n_set_chp.append(rows[i][9])
        T_avg.append(rows[i][8] - 273.15)
        Q_tra_gain.append(rows[i][12]/1000)

    t = [par_rh["month_start"][par_rh["month"]] + i for i in range(start*block_length, length*block_length)]
    t_filtered = [t[i] for i in range(0, len(t), 10)]
    xtick_positions = np.arange(0, (length* block_length - start*block_length) * (3600 / step_size), int(3600 / step_size) * 10)
    
    plt.clf()
    plt.plot(T_set_chp, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Set temperature in °C', fontsize=18)
    plt.tight_layout()
    plt.savefig(directory + '/plots_simu/T_set_chp', dpi = 600)
    plt.grid(True, linewidth = 0.5)
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
    plt.plot(heat_dem, label = "Heat Demand DG", color = 'tab:red')
    plt.plot(Q_tra_gain, label = "Heat Transfer ROM", color = 'tab:blue')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    #plt.ylim(0, 8)
    #plt.yticks(np.arange(0, 9, 1))
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('Heat in kW', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/Comparison room heat power', dpi = 600)
    #plt.show()
    print("HI")

    plt.clf()
    plt.plot(n_set_chp, color = 'tab:green')
    plt.xticks(xtick_positions, t_filtered, fontsize=16)
    plt.legend(fontsize=16, loc = 'upper right')
    plt.xlabel('time in h', fontsize=18)
    plt.ylabel('relative heatpump speed', fontsize=18)
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5)
    plt.savefig(directory + '/plots_simu/n_set_chp', dpi = 600)
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
    plt.plot(trade_sold, label = 'Sold electricity', color = 'tab:red')
    plt.plot(chp_elec, label = 'CHP electricity simulation', color = 'tab:green')
    plt.plot(chp_elec_opti, label = 'CHP electricity optimization', color = 'tab:blue')
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
    plt.savefig(directory + '/plots_simu/Stromerzeugung CHP', dpi = 600)
    #plt.show()
    print("HI")

    t_tes_opti = []
    t_tes_fmu = []
    for l in range(start, length):
        for block_step in par_rh["time_steps"][l][0:block_length]:
            t_tes_opti.append(opti_res[l][no_house][21][block_step] - 273.15)
    for i in range(start * block_length, length * block_length):
        t_tes_fmu.append(rows[i * step_size + step_size][8] - 273.15) #TODO Index noch nicht perfekt

   
    #TODO dieser Plot nur so halb sinvoll bei blockBids, sind ja keine stündlihen Werte
    plt.clf()
    plt.plot(t_tes_fmu, label = 'After simulation', marker = 'o', color = 'tab:blue')
    plt.plot(t_tes_opti, label = 'After optimization', marker = 'x', color = 'tab:orange')
    #plt.xticks(xtick_positions, t_filtered, fontsize=16)
    #xticks = np.arange(block_length*start, block_length*length, 10)
    xticks = np.arange(0, block_length*(length-start), 10)
    xtick_labels = np.arange(1416+block_length*start, 1416+block_length*length, 10)
    plt.xticks(xticks, xtick_labels)
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
    #for n_opt in range(int(168/block_length)):
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
    #for n_opt in range(int(168/block_length)):
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

    # --------------------- costs from grid transactions ---------------------------

    grid_elec_buy = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0])) #bezeichnet im gegensatz zu p_total_purchase nur die aus dem netz bezogene Strommenge
    grid_elec_sell = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    grid_costs_buy = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    grid_revenue_sell = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    total_grid_purchase_per_building = np.zeros(len(opti_res[0]))
    total_grid_feedin_per_building = np.zeros(len(opti_res[0]))
    for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
    #for n_opt in range(int(168/block_length)):
        for n in range(len(opti_res[0])):
            for t in range(par_rh["hour_start"][n_opt], par_rh["hour_start"][n_opt] + block_length):
                grid_elec_buy[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["power_from_grid"][n][t]/1000
                grid_elec_sell[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["power_to_grid"][n][t]/1000
                grid_costs_buy[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["costs_power_from_grid"][n][t]
                grid_revenue_sell[n,t - par_rh["hour_start"][0]] += grid_transaction[n_opt]["revenue_power_to_grid"][n][t]
            total_grid_purchase_per_building[n] = sum(grid_elec_buy[n, :])
            total_grid_feedin_per_building[n] = sum(grid_elec_sell[n, :])
    total_grid_purchase = sum(sum(grid_elec_buy))
    total_grid_feedin = sum(sum(grid_elec_sell))
    total_grid_costs = sum(sum(grid_costs_buy))
    total_grid_rev = sum(sum(grid_revenue_sell))
    print("HI")

    # --------------------- trade price, revenue, costs, gain  ---------------------

    traded_power = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    additional_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    saved_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_revenue = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    trading_costs = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))
    gain = np.zeros((len(opti_res[0]), par_rh["time_steps"][par_rh["n_opt"] - 1][-1] - par_rh["hour_start"][0]))

    for opt in range(par_rh["n_opt"] - int(36/block_length)-1):
    #for opt in range(int(168/block_length)):
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

    traded_power_total = np.sum(traded_power_per_building)/2 # durch 2, da sonst doppelte Handelsmengen enthalten, TODO Joel sagen
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
    #for n_opt in range(int(168/block_length)):
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
    #for n_opt in range(int(168/block_length)):
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
    #for n_opt in range(int(168/block_length)):
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

    # SCF DCF
    minimum = np.zeros(len(nominator_total_demand[0]))
    for t in range(len(nominator_total_demand[0])):
        a = sum(nominator_total_supply[:,t])
        b = sum(nominator_total_demand[:,t])
        minimum[t] = np.min([a, b])
        if round(a,3) != round(b, 3):
            print("HI")
    scf = sum(minimum)/sum(sum(denominator_total_supply))
    dcf = sum(minimum)/sum(sum(denominator_total_demand))


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
        "mSCF": mSCF,
        "mDCF": mDCF,
        "scf": scf,
        "dcf": dcf,

        "bat_losses": bat_losses,
        "tes_losses": tes_losses,

        "residual_load":residual_load,
        "total_grid_purchase_per_building": total_grid_purchase_per_building,
        "total_grid_feedin_per_building": total_grid_feedin_per_building,
        "total_p_purchase":total_p_purchase,
        "total_feed_in": total_feed_in,

        "total_grid_purchase":total_grid_purchase,
        "total_grid_feedin":total_grid_feedin,        
        "total_grid_costs":total_grid_costs,
        "total_grid_rev":total_grid_rev
        }
    return results

def simulation_KPIs_per_building_p2p(rows, params, opti_res, results, nego_results):

    # SCF and DCF
    #timesteps = 56*60*3
    timesteps = len(opti_res)*60*3 
    minimum = np.zeros(timesteps)
    P_sell = np.zeros((len(opti_res[0]), timesteps))
    P_demand = np.zeros((len(opti_res[0]), timesteps))
    #for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
    for n in range(len(opti_res[0])):
        for t in range(timesteps):
            P_sell[n, t] = rows["all"][t][n]/1000
            P_demand[n, t] = rows["all"][t][n + len(opti_res[0])]/1000 #Indexverschiebung
    for t in range(timesteps):
        a = sum(P_sell[:,t])
        b = sum(P_demand[:,t])
        minimum[t] = np.min([a, b])
    
    denominator_sell = sum(sum(P_sell))
    denominator_demand = sum(sum(P_demand))
    scf = sum(minimum)/denominator_sell
    dcf = sum(minimum)/denominator_demand


    tra_vol = np.zeros((len(opti_res[0]), timesteps))
    for n in range(5,11): # only look at the demand bids of heat pump buildings (only demand)
        for t in range(timesteps):
            if rows["all"][t][n + 2 * len(opti_res[0])] > 0:
                if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > P_demand[n, t]:
                    tra_vol[n, t] = P_demand[n, t]
                elif rows["all"][t][n + 2 * len(opti_res[0])]/1000 < P_demand[n, t]:
                    tra_vol[n, t] = rows["all"][t][n + 2 * len(opti_res[0])]/1000

    difference = []
    real_tra_vol = np.zeros(timesteps)
    desired_trade_demand = np.zeros(timesteps)
    P_grid_sell = np.zeros(timesteps)
    for t in range(timesteps):
        total_supply = 0
        total_trade_amount = 0
        for n in ([0, 1, 2, 3, 4, 11]):
            total_supply += P_sell[n, t] # im Zeitschritt insgesamt tatsächlich erzeugte und angebotene Leistung
        for n in range(5, 11):
            total_trade_amount += tra_vol[n, t] # im Zeitschritt insgesamt wirklich benötigte Handelsleistung
        diff = total_trade_amount - total_supply
        if diff <= 0: #Wenn die Leistung ausgreicht, kann der geamte Bedarf gedeckt werden
            real_tra_vol[t] = total_trade_amount
            P_grid_sell[t] = -diff # der Überschuss an Leistung muss dann ins Netz gespeist werden
        else: # Wenn die nachgefragte Handelsleistung nicht durch das Angebot gedeckt werden kann, wird nur gehandelt, was möglich ist
            real_tra_vol[t] = total_supply
            difference.append((t, diff))
        desired_trade_demand[t] = total_trade_amount
    

    # Total Costs from grid interactions 
    P_grid_buy = np.zeros(timesteps) 
    gas_import = np.zeros(timesteps)
    for t in range(timesteps):
        P_grid_buy[t] = sum(P_demand[:, t]) - real_tra_vol[t]
    for t in range(timesteps):
        for n in ([0, 1, 2, 3, 4, 11]): # alle Häuser mit GK und BHKW
            gas_import[t] += rows["all"][t][n + 3 * len(opti_res[0])]/1000
    """
    # Trading per building
    real_tra_vol_per_building = np.zeros((len(opti_res[0]), timesteps))
    tra_costs_per_building = np.zeros((len(opti_res[0]), timesteps))
    tra_rev_per_building = np.zeros((len(opti_res[0]), timesteps))
    chp_supply = np.zeros(timesteps) 
    P_grid_buy = np.zeros((len(opti_res[0]), timesteps))
    P_grid_sell = np.zeros((len(opti_res[0]), timesteps))
    for t in range(timesteps):
        n_opt = int(t/(3*60))
        block_step = 1416 + n_opt*3 + int((t - n_opt*3*60)/60)
        chp_supply[t] = P_sell[11, t]
        chp_dummy = 0
        if real_tra_vol[t] >= desired_trade_demand[t]: # vorher ausgerechnete Gesamthandelsmenge, die theoretisch zur Verfügung steht TODO lässt den Fall aus, dass nur beim BHKW Strom fehlt. Halt die Frage, ob ander gebäude für fehlende Strommengen aufkommen können
            for n in range(len(opti_res[0])):
                real_tra_vol_per_building[n, t] = tra_vol[n, t]
                for round_nb in nego_results[n_opt]:
                    for match in nego_results[n_opt][round_nb]:
                        if n == nego_results[n_opt][round_nb][match]["buyer"]:
                            tra_costs_per_building = (real_tra_vol_per_building[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                            tra_rev_per_building = 0
                        elif n == nego_results[n_opt][round_nb][match]["seller"]:
                            tra_costs_per_building = 0
                            # Der Prosumer handelt die Strommenge, die sein Partner aus dem Match bekommt:
                            real_tra_vol_per_building[n, t] = real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["buyer"], t]
                            tra_rev_per_building = (real_tra_vol_per_building[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                            # TODO hier muss noch BHKW Einspeisung hin, also leider eigenbtlich auch die volle Fallunterscheidung
                            # hängt halt auch davon ab, ob die Gesamterzeugungsleistung immer betrachtet werden soll oder nicht
        else:
            for round_nb in nego_results[n_opt]:
                for match in nego_results[n_opt][round_nb]:
                    for n in range(len(opti_res[0])):
                        if nego_results[n_opt][round_nb][match]["seller"] != 11:
                            if n == nego_results[n_opt][round_nb][match]["buyer"]:
                                real_tra_vol_per_building[n, t] = tra_vol[n, t]
                                tra_costs_per_building[n, t] = (real_tra_vol_per_building[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                                tra_rev_per_building[n, t] = 0
                            elif n == nego_results[n_opt][round_nb][match]["seller"]:
                                tra_costs_per_building[n, t] = 0
                                # Der Prosumer handelt die Strommenge, die sein Partner aus dem Match bekommt:
                                tra_rev_per_building[n, t] = (real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["buyer"], t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                        elif nego_results[n_opt][round_nb][match]["seller"] == 11:
                            if chp_dummy < chp_supply[t]:
                                diff = chp_supply[t] - chp_dummy
                                #if nego_results[n_opt][round_nb][match]["seller"] == 11:
                                if n == nego_results[n_opt][round_nb][match]["buyer"]:
                                        real_tra_vol_per_building[n, t] = tra_vol[n, t] # Annahme, dass gewünschte Menge noch vom CHP bereitgestellt werden kann
                                        chp_dummy += tra_vol[n, t] # Langsames Aufbrauchen für CHP Strom
                                        if chp_dummy >= chp_supply[t]: # Falls in diesem Match der CHP Strom aufgebraucht wird, kann nur noch der Rest gehandelt werden
                                            real_tra_vol_per_building[n, t] = diff
                                        tra_costs_per_building[n, t] = (real_tra_vol_per_building[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                            else: # Kauf nicht mehr möglich und Haus muss aus Netz beziehen
                                if n == nego_results[n_opt][round_nb][match]["buyer"]:
                                    real_tra_vol_per_building[n, t] = 0
                                    P_grid_buy[n, t] = tra_vol[n, t] 
    """                               


    # ALternativ: für jedes Match einfach einzeln schauen, ob Handelspartner komplett liefern kann. Falls ja wird der Rest der Erzugung ins Netz gepackt, 
    # Falls nicht, muss Gebäude die Differenz aus dem Netz kaufen. Es kann also kein Restüberschuss aus einem match das Defizit eines anderen Matches decken
    P_sell = np.zeros((len(opti_res[0]), timesteps))
    P_demand = np.zeros((len(opti_res[0]), timesteps))
    for n in range(len(opti_res[0])):
        for t in range(timesteps):
            P_sell[n, t] = round(rows["all"][t][n]/1000, 2)
            P_demand[n, t] = round(rows["all"][t][n + len(opti_res[0])]/1000, 2) #Indexverschiebung

    real_tra_vol_per_building = np.zeros((len(opti_res[0]), timesteps))
    tra_costs_per_building = np.zeros((len(opti_res[0]), timesteps))
    tra_rev_per_building = np.zeros((len(opti_res[0]), timesteps))
    for t in range(timesteps):
        n_opt = int(t/(3*60))
        block_step = 1416 + n_opt*3 + int((t - n_opt*3*60)/60)
        for n in range(len(opti_res[0])):
            for round_nb in nego_results[n_opt]:
                for match in nego_results[n_opt][round_nb]:
                    if "quantity" in nego_results[n_opt][round_nb][match]:
                        if isinstance(nego_results[n_opt][round_nb][match]["quantity"][block_step], float):  # valid_time_steps
                            if n == nego_results[n_opt][round_nb][match]["buyer"]:
                                if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > 0:
                                    if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > P_demand[n, t]: 
                                        if P_sell[nego_results[n_opt][round_nb][match]["seller"], t] >= P_demand[n, t]:
                                            real_tra_vol_per_building[n, t] += P_demand[n, t] 
                                            real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += P_demand[n, t] 
                                            tra_costs_per_building[n, t] += (P_demand[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                                            tra_rev_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += (P_demand[n, t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step] 
                                            P_sell[nego_results[n_opt][round_nb][match]["seller"], t] -= P_demand[n, t] # Sellerleistung wird um den im Match verkauften Teil reduziert                                    
                                            # TODO evtl Pdemand auf 0 setzen
                                            P_demand[n, t] = 0
                                        else:
                                            real_tra_vol_per_building[n, t] += P_sell[nego_results[n_opt][round_nb][match]["seller"], t] # +=, da Demand noch nicht abgedeckt und weiterer Kauf möglich
                                            real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += P_sell[nego_results[n_opt][round_nb][match]["seller"], t]
                                            tra_costs_per_building[n, t] += (P_sell[nego_results[n_opt][round_nb][match]["seller"], t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step] # kein +=, da real_tra_vol ja schon erhöht wurde, sonst doppelt 
                                            tra_rev_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += (P_sell[nego_results[n_opt][round_nb][match]["seller"], t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step] # kein +=, da Supply voll aufgebraucht
                                            P_demand[n, t] -= P_sell[nego_results[n_opt][round_nb][match]["seller"], t] #Demand wird reduziert, da ein Teil jetzt abgedeckt
                                            # TODO evtl Psell auf 0 setzen
                                            P_sell[nego_results[n_opt][round_nb][match]["seller"], t] = 0
                                    else: # Wenn Demand größer als die Handelsmenge der Opti, wird maximal die Opti Handelsmenge gehandelt, da Stellgröße
                                        if P_sell[nego_results[n_opt][round_nb][match]["seller"], t] >= rows["all"][t][n + 2 * len(opti_res[0])]/1000:
                                            real_tra_vol_per_building[n, t] += rows["all"][t][n + 2 * len(opti_res[0])]/1000
                                            real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += rows["all"][t][n + 2 * len(opti_res[0])]/1000
                                            tra_costs_per_building[n, t] += ((rows["all"][t][n + 2 * len(opti_res[0])]/1000)/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                                            tra_rev_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += ((rows["all"][t][n + 2 * len(opti_res[0])]/1000)/60) * nego_results[n_opt][round_nb][match]["price"][block_step] 
                                            P_sell[nego_results[n_opt][round_nb][match]["seller"], t] -= ((rows["all"][t][n + 2 * len(opti_res[0])]/1000)/60) # Sellerleistung wird um den im Match verkauften Teil reduziert        
                                            P_demand[n, t] -= rows["all"][t][n + 2 * len(opti_res[0])]/1000 # Rest von P_demand muss dann aus dem netz kommen
                                            rows["all"][t][n + 2 * len(opti_res[0])] = 0 # wird auf 0 gesetzt, da tra_check jetzt voll ausgenutzt und kein weiterere Handel mehr stattfinden soll
                                        else:
                                            real_tra_vol_per_building[n, t] += P_sell[nego_results[n_opt][round_nb][match]["seller"], t] # +=, da tra_check noch nicht abgedeckt und weiterer Kauf möglich
                                            real_tra_vol_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += P_sell[nego_results[n_opt][round_nb][match]["seller"], t]
                                            tra_costs_per_building[n, t] += (P_sell[nego_results[n_opt][round_nb][match]["seller"], t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]
                                            tra_rev_per_building[nego_results[n_opt][round_nb][match]["seller"], t] += (P_sell[nego_results[n_opt][round_nb][match]["seller"], t]/60) * nego_results[n_opt][round_nb][match]["price"][block_step]  
                                            P_demand[n, t] -= P_sell[nego_results[n_opt][round_nb][match]["seller"], t] #Demand wird reduziert, da ein Teil jetzt abgedeckt
                                            rows["all"][t][n + 2 * len(opti_res[0])] -= P_sell[nego_results[n_opt][round_nb][match]["seller"], t] * 1000 # tra_check wird reuziert um den bereits gehandelten teil
                                            P_sell[nego_results[n_opt][round_nb][match]["seller"], t] = 0
    # Nach und nach wird so alles angepasst und über alle Matches hinweg der Bedarf und das Angebot reduziert.  
    # die P-grid_sell und buy Analyse kann erst nach der Betrachtung aller Matches erfolgen. Alles was dann noch übrig ist, muss übers Netz ge- /verkauft werden
    P_grid_buy = np.zeros((len(opti_res[0]), timesteps))
    P_grid_sell = np.zeros((len(opti_res[0]), timesteps))
    gas_import = np.zeros((len(opti_res[0]), timesteps))
    total_tra_costs_per_building = np.zeros(len(opti_res[0]))
    total_tra_rev_per_building = np.zeros(len(opti_res[0]))
    total_trade_per_building = np.zeros(len(opti_res[0]))
    total_grid_costs_per_building = np.zeros(len(opti_res[0]))
    total_grid_rev_per_building = np.zeros(len(opti_res[0]))
    total_gas_costs_per_building = np.zeros(len(opti_res[0]))
    total_costs_per_building = np.zeros(len(opti_res[0]))
    for n in range(len(opti_res[0])):    
        for t in range(timesteps):
            P_grid_buy[n, t] = P_demand[n, t]
            P_grid_sell[n, t] = P_sell[n, t]
            gas_import[n, t] = rows["all"][t][n + 3 * len(opti_res[0])]/1000
        total_tra_costs_per_building[n] = sum(tra_costs_per_building[n, :])
        total_tra_rev_per_building[n] = sum(tra_rev_per_building[n, :])
        total_trade_per_building[n] = sum(real_tra_vol_per_building[n, :]/60)
        total_grid_costs_per_building[n] = sum(P_grid_buy[n, :]/60 * params["eco"]["pr", "el"]) 
        total_grid_rev_per_building[n] = sum(P_grid_sell[n, :]/60 * params["eco"]["sell_pv"]) 
        total_gas_costs_per_building[n] = sum((gas_import[n, :]/60) * params["eco"]["gas"]) 
        total_costs_per_building[n] = total_tra_costs_per_building[n] + total_gas_costs_per_building[n] + total_grid_costs_per_building[n] - total_grid_rev_per_building[n] - total_tra_rev_per_building[n]
    
    # Total Costs
    trade_costs = sum(total_tra_costs_per_building)
    trade_rev = sum(total_tra_rev_per_building)
    grid_costs = sum(total_grid_costs_per_building)
    grid_rev = sum(total_grid_rev_per_building)
    gas_costs = sum(total_gas_costs_per_building)
    total_costs = trade_costs + gas_costs + grid_costs - trade_rev - grid_rev
    

    # Gain
    gain_per_building = np.zeros(len(opti_res[0]))
    for n in range(5, 11):
        gain_per_building[n] = total_trade_per_building[n] * params["eco"]["pr", "el"] - total_tra_costs_per_building[n]
    for n in (0, 1, 2, 3, 4, 11):
        gain_per_building[n] = total_tra_rev_per_building[n] - total_trade_per_building[n] * params["eco"]["sell_pv"]
       

    # TODO evtl als Differenz von tra_costs zu real_tra_vol * pr_el?

    # mscf and mdcf
    mscf = (sum(sum(real_tra_vol_per_building))/2)/denominator_sell  # durch 2 teilen, da in real_tra_vol_per_building aufsummiert jede Handelsmenge zweimal vorkommt (Kauf und Verkauf)
    mdcf = (sum(sum(real_tra_vol_per_building))/2)/denominator_demand

    # Total traded electricity
    total_traded_elec = sum(total_trade_per_building)/2

    # Final Dict
    simulation_KPI_dict = {
        "scf": scf,
        "dcf": dcf,
        "mscf": mscf,
        "mdcf": mdcf,
        "gain_per_building": gain_per_building,
        "total_costs_per_building": total_costs_per_building,
        "total_tra_costs_per_building": total_tra_costs_per_building,
        "total_tra_rev_per_building": total_tra_rev_per_building,
        "total_grid_costs_per_building": total_grid_costs_per_building,
        "total_grid_rev_per_building": total_grid_rev_per_building,
        "total_gas_costs_per_building": total_gas_costs_per_building,
        "total_costs": total_costs,
        "total_traded_elec": total_traded_elec,
        "total_trade_per_building": total_trade_per_building        
    }

    return simulation_KPI_dict
        
def p2p_plots(results, par_rh, opti_res, scenario, block_length):
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario)

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
    plt.yticks(np.arange(0, 1400, 200), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Total costs per building type', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0-0.2, results["gain_per_building"][1], width = 0.4, color="darkcyan", zorder = 2, label = "With LEM")
    pos = 1
    for i in [6, 8, 11]:
        plt.bar(pos, results["gain_per_building"][i], width = 0.4, color="darkcyan", zorder = 2)
        pos +=1
    plt.ylabel('Gain in €')
    plt.xticks(np.arange(4), ['SFH\nPV+BOI','SFH\nHP+BAT','SFH\nHP','MFH\nCHP'], fontsize = "14")
    plt.xlabel('LEM house types')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "14", ncol = 2)
    plt.yticks(np.arange(0, 1400, 200), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Gain per building type', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0, 100* results["gain_per_building"][1]/results["total_cost_per_building"][1], width = 0.4, color="darkcyan", zorder = 2, label = "With LEM")
    pos = 1
    for i in [6, 8, 11]:
        plt.bar(pos, 100* results["gain_per_building"][i]/results["total_cost_per_building"][i], width = 0.4, color="darkcyan", zorder = 2)
        pos +=1
    plt.ylabel('Relative gain in %')
    plt.xticks(np.arange(4), ['SFH\nPV+BOI','SFH\nHP+BAT','SFH\nHP','MFH\nCHP'], fontsize = "14")
    plt.xlabel('LEM house types')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "14", ncol = 2)
    plt.yticks(np.arange(0, 120, 20), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Relative gain per building type', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    for i in range(len(results["gain_per_building"])):
        plt.bar(i, results["gain_per_building"][i], color="darkcyan", zorder = 2)
    plt.ylabel('Gain in €')
    plt.xticks(np.arange(12), ['1','2','3','4','5','6','7','8','9','10','11','12'])
    plt.xlabel('LEM houses')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.yticks(np.arange(0, 600, 100))
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/plots_p2p/Gain per building', dpi = 600)
    #plt.show()
    print("Hi")

    return

def simulation_KPIs_p2p(rows, params, opti_res, results):

    # SCF and DCF
    #timesteps = 56*60*3 
    timesteps = len(opti_res)*60*3 
    minimum = np.zeros(timesteps)
    P_sell = np.zeros((len(opti_res[0]), timesteps))
    P_demand = np.zeros((len(opti_res[0]), timesteps))
    #for n_opt in range(par_rh["n_opt"] - int(36/block_length)-1 ):
    for n in range(len(opti_res[0])):
        for t in range(timesteps):
            P_sell[n, t] = rows["all"][t][n]/1000
            P_demand[n, t] = rows["all"][t][n + len(opti_res[0])]/1000 #Indexverschiebung
    for t in range(timesteps):
        a = sum(P_sell[:,t])
        b = sum(P_demand[:,t])
        minimum[t] = np.min([a, b])
 
    scf = sum(minimum)/sum(sum(P_sell))
    dcf = sum(minimum)/sum(sum(P_demand))

    # Gain
    # 2 Alternativen: 
    #   1. Für Gesamtgain reicht Betrachtung der WP-Demands, da die Summe der Handelsmenge der WP-Gebäude der Summe der 
    #      Handelsmenge der Prosumer entsprechen muss. Berechnung dann mit kompletter Preisdifferenz ohne Handelspreis
    #   2. Für weitere Aufschlüsselung und Gain pro gebäude auch PV und CHP Bids mit reinnehmen. Berechnung dann einzeln mit Handelspreis

    # Alternative 1

    # TODO Problem auch hier, dass tra_vol ja von Opti vorgegeben wird und nicht sicher ist, ob diese Strommenge auch verfügbar ist
    # es MUSS also die Seller Seite betrachtet werden um zu gucken, ob die Gesamtkaufmenge der WP überhaupt wirklich zur Verfügung steht.
    #Problem dabei: Wenn nicht der Fall, welches Haus bekommt dann wieviel Strom?
    # Bei nur PV wäre das einfacher, der Strom steht unabhängig von einer Wärmeregelung zur Verfügung: 
    # Aktuell sagt Opti, dass BHKW mehr handeln müsste, als es Stromproduktion hat. Daher die Differenz
    """
    difference = []
    for t in range(timesteps):
        total_supply = 0
        total_trade_amount = 0
        for n in ([0, 1, 2, 3, 4, 11]):
            total_supply += P_sell[n, t]
        for n in range(5, 11):
            total_trade_amount += rows["all"][t][n + 2 * len(opti_res[0])]/1000
        diff = total_trade_amount - total_supply
        if diff > 0:
            difference.append((t, diff))           
    """

    tra_vol = np.zeros((len(opti_res[0]), timesteps))
    for n in range(5,11): # only look at the demand bids of heat pump buildings (only demand)
        for t in range(timesteps):
            if rows["all"][t][n + 2 * len(opti_res[0])] > 0:
                if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > P_demand[n, t]:
                    tra_vol[n, t] = P_demand[n, t]
                elif rows["all"][t][n + 2 * len(opti_res[0])]/1000 < P_demand[n, t]:
                    tra_vol[n, t] = rows["all"][t][n + 2 * len(opti_res[0])]/1000

    difference = []
    real_tra_vol = np.zeros(timesteps)
    P_grid_sell = np.zeros(timesteps)
    for t in range(timesteps):
        total_supply = 0
        total_trade_amount = 0
        for n in ([0, 1, 2, 3, 4, 11]):
            total_supply += P_sell[n, t] # im Zeitschritt insgesamt tatsächlich erzeugte und angebotene Leistung
        for n in range(5, 11):
            total_trade_amount += tra_vol[n, t] # im Zeitschritt insgesamt wirklich benötigte Handelsleistung
        diff = total_trade_amount - total_supply
        if diff <= 0: #Wenn die Leistung ausgreicht, kann der geamte Bedarf gedeckt werden
            real_tra_vol[t] = total_trade_amount
            P_grid_sell[t] = -diff # der Überschuss an Leistung muss dann ins Netz gespeist werden
        else: # Wenn die nachgefragte Handelsleistung nicht durch das Angebot gedeckt werden kann, wird nur gehandelt, was möglich ist
            real_tra_vol[t] = total_supply
            difference.append((t, diff))
    # Umrechnung auf kWh
    total_gain = sum((real_tra_vol/60) * (params["eco"]["pr", "el"] - params["eco"]["sell_pv"]))


    # Alternative 2
    """
    real_tra_vol = np.zeros((len(opti_res[0]), timesteps))
    for n in range(len(opti_res[0])): # only look at the demand bids of  
        for t in range(timesteps):
            if rows["all"][t][n + 2 * len(opti_res[0])] > 0:
                if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > P_demand[n, t]:
                    real_tra_vol[n, t] = P_demand[n, t]
                elif rows["all"][t][n + 2 * len(opti_res[0])]/1000 < P_demand[n, t]:
                    real_tra_vol[n, t] = rows["all"][t][n + 2 * len(opti_res[0])]/1000
            elif rows["all"][t][n + 2 * len(opti_res[0])] < 0: TODO hier checken, dennauch die Verkaufshandelsmengen sind ja von den tatsächlichen Bedarfen der WP-Häuser abhängig
                if rows["all"][t][n + 2 * len(opti_res[0])]/1000 > P_demand[n, t]:
                    real_tra_vol[n, t] = P_demand[n, t]
                elif rows["all"][t][n + 2 * len(opti_res[0])]/1000 < P_demand[n, t]:
                    real_tra_vol[n, t] = rows["all"][t][n + 2 * len(opti_res[0])]/1000
    # Umrechnung auf kWh
    total_gain = 
    """                                
    # mSCF, mDCF

    mscf = sum(real_tra_vol)/sum(sum(P_sell))
    mdcf = sum(real_tra_vol)/sum(sum(P_demand))


    # Total Costs from grid interactions 

    # Problem hier, dass man real_tra_vol verwenden muss, dafür aber keine Werte für einzelne Häuser hat
    # Also auch hier nur Gesamtkostenbetrachtung möglich
    P_grid_buy = np.zeros(timesteps) 
    gas_import = np.zeros(timesteps)
    for t in range(timesteps):
        P_grid_buy[t] = sum(P_demand[:, t]) - real_tra_vol[t]
    for t in range(timesteps):
        for n in ([0, 1, 2, 3, 4, 11]): # alle Häuser mit GK und BHKW
            gas_import[t] += rows["all"][t][n + 3 * len(opti_res[0])]/1000 
    
    
    # Umrechnung auf kWh
    total_grid_costs = sum((P_grid_buy/60) * params["eco"]["pr", "el"])
    total_grid_revenue = sum((P_grid_sell/60) * params["eco"]["sell_pv"])
    total_gas_costs = sum((gas_import/60) * params["eco"]["gas"])

    total_costs = total_grid_costs - total_grid_revenue + total_gas_costs



    return scf, dcf, mscf, mdcf, total_gain, total_costs, real_tra_vol
        



def p2p_plots_compared(params):
    #Quartiersvergleiche:
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar"

    plt.rcParams.update({'font.size': 20}) #größere Schriftgröße für Plots nebeneinander

    init_val, rows, nodes, opti_res, par_rh, mar_dict = load_results(scenario= "\WithoutMPC", block_length=3, monthly=True)
    resultsWoMPC3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
    
    init_val, rowsHD2Sto3, nodes, opti_resHD2Sto3, par_rh, mar_dict = load_results(scenario="\HeatDem_2Sto", block_length=3, monthly=True)
    resultsHD2Sto3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
    
    init_val, rowsHDCombiSto3, nodes, opti_resHDCombiSto3, par_rh, mar_dict = load_results(scenario="\HeatDem_CombiSto", block_length=3, monthly=True)
    resultsHDCombiSto3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
    init_val, rowsROM2Sto3, nodes, opti_resrowsROM2Sto3, par_rh, mar_dict = load_results(scenario="\ROM_2Sto", block_length=3, monthly=True)
    resultsROM2Sto3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
    """
    #plt.clf()
    plt.bar(0-0.2, 100*resultsWoMPC3["mSCF"], color="darkcyan", label = "mSCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*resultsWoMPC3["mDCF"], color="lightblue", label = "mDCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*resultsHD2Sto3["mSCF"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*resultsHD2Sto3["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsHDCombiSto3["mSCF"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsHDCombiSto3["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(3-0.2, 100*resultsROM2Sto3["mSCF"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(3+0.2, 100*resultsROM2Sto3["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(4), ['No MPC','HDM\nTwo Sto','HDM\nCombi Sto','ROM\nTwo Sto'])
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/mSCF mDCF compared', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0-0.2, 100*resultsWoMPC3["scf"], color="darkcyan", label = "SCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*resultsWoMPC3["dcf"], color="lightblue", label = "DCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*resultsHD2Sto3["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*resultsHD2Sto3["dcf"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsHDCombiSto3["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsHDCombiSto3["dcf"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(3-0.2, 100*resultsROM2Sto3["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(3+0.2, 100*resultsROM2Sto3["dcf"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(4), ['No MPC','HDM\nTwo Sto','HDM\nCombi Sto','ROM\nTwo Sto'])
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/SCF DCF compared', dpi = 600)
    #plt.show()
    print("Hi")
    """

    #Vergleich Kontrollhorizont:
    init_val, rowsHD2Sto6, nodes, opti_res, par_rh6, mar_dict = load_results(scenario="\HeatDem_2Sto", block_length=6, monthly=True)
    resultsHD2Sto6 = calc_results_p2p(par_rh=par_rh6, block_length=6,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)
    init_val, rowsHD2Sto1, nodes, opti_res1, par_rh1, mar_dict1 = load_results(scenario="\HeatDem_2Sto", block_length=1, monthly=True)
    resultsHD2Sto1 = calc_results_p2p(par_rh=par_rh1, block_length=1,
                                                nego_results=mar_dict1["negotiation_results"],
                                                opti_res=opti_res1, grid_transaction=mar_dict1["transactions_with_grid"],
                                                params = params)
    plt.clf()
    plt.bar(0-0.2, 100*resultsHD2Sto3["mSCF"], color="darkcyan", label = "mSCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*resultsHD2Sto3["mDCF"], color="lightblue", label = "mDCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*resultsHD2Sto6["mSCF"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*resultsHD2Sto6["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(2), ['CH = 3','CH = 6'])
    plt.legend(fontsize=18, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/CH comparison mSCF mDCF ', dpi = 600)
    #plt.show()
    print("Hi")
    

    plt.clf()
    plt.bar(0-0.2, resultsHD2Sto1["total_cost_per_building"][1], width = 0.2, color="darkcyan", zorder = 2, label = "KH = 1")
    plt.bar(0, resultsHD2Sto3["total_cost_per_building"][1], width = 0.2, color="lightblue", zorder = 2, label = "KH = 3")
    plt.bar(0+0.2, resultsHD2Sto6["total_cost_per_building"][1], width = 0.2, color="lavender", zorder = 2, label = "KH = 6")
    pos = 1
    for i in [5, 7, 11]:
        plt.bar(pos-0.2, resultsHD2Sto1["total_cost_per_building"][i], width = 0.2, color="darkcyan", zorder = 2)
        plt.bar(pos, resultsHD2Sto3["total_cost_per_building"][i], width = 0.2, color="lightblue", zorder = 2)
        plt.bar(pos+0.2, resultsHD2Sto6["total_cost_per_building"][i], width = 0.2, color="lavender", zorder = 2)
        pos +=1
    plt.ylabel('Gesamtkosten in €')
    plt.xticks(np.arange(4), ['EFH\nPV+GK','EFH\nWP+BAT','EFH\nWP','MFH\nBHKW'], fontsize = "18")
    plt.xlabel('Gebäudetypen im LEM')
    #plt.legend(fontsize=18, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "18", ncol = 2)
    #plt.yticks(np.arange(0, 1400, 200), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/CH costs per building', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0-0.2, resultsHD2Sto1["gain_per_building"][1], width = 0.2, color="darkcyan", zorder = 2, label = "KH = 1")
    plt.bar(0, resultsHD2Sto3["gain_per_building"][1], width = 0.2, color="lightblue", zorder = 2, label = "KH = 3")
    plt.bar(0+0.2, resultsHD2Sto6["gain_per_building"][1], width = 0.2, color="lavender", zorder = 2, label = "KH = 6")
    pos = 1
    for i in [5, 7, 11]:
        plt.bar(pos-0.2, resultsHD2Sto1["gain_per_building"][i], width = 0.2, color="darkcyan", zorder = 2)
        plt.bar(pos, resultsHD2Sto3["gain_per_building"][i], width = 0.2, color="lightblue", zorder = 2)
        plt.bar(pos+0.2, resultsHD2Sto6["gain_per_building"][i], width = 0.2, color="lavender", zorder = 2)
        pos +=1
    plt.ylabel('Einsparung in €')
    plt.xticks(np.arange(4), ['EFH\nPV+GK','EFH\nWP+BAT','EFH\nWP','MFH\nBHKW'], fontsize = "18")
    plt.xlabel('Gebäudetypen im LEM')
    #plt.legend(fontsize=18, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "18", ncol = 2)
    #plt.yticks(np.arange(0, 600, 100), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/CH comparison gain', dpi = 600)
    #plt.show()
    print("Hi")

    plt.clf()
    plt.bar(0-0.2, 100*resultsHD2Sto1["gain_per_building"][1]/resultsHD2Sto1["total_cost_per_building"][1], width = 0.2, color="darkcyan", zorder = 2, label = "KH = 1")
    plt.bar(0, 100*resultsHD2Sto3["gain_per_building"][1]/resultsHD2Sto3["total_cost_per_building"][1], width = 0.2, color="lightblue", zorder = 2, label = "KH = 3")
    plt.bar(0+0.2, 100*resultsHD2Sto6["gain_per_building"][1]/resultsHD2Sto6["total_cost_per_building"][1], width = 0.2, color="lavender", zorder = 2, label = "KH = 6")
    pos = 1
    for i in [5, 7, 11]:
        plt.bar(pos-0.2, 100*resultsHD2Sto1["gain_per_building"][i]/resultsHD2Sto1["total_cost_per_building"][i], width = 0.2, color="darkcyan", zorder = 2)
        plt.bar(pos, 100*resultsHD2Sto3["gain_per_building"][i]/resultsHD2Sto3["total_cost_per_building"][i], width = 0.2, color="lightblue", zorder = 2)
        plt.bar(pos+0.2, 100*resultsHD2Sto6["gain_per_building"][i]/resultsHD2Sto6["total_cost_per_building"][i], width = 0.2, color="lavender", zorder = 2)
        pos +=1
    plt.ylabel('Relative Einsparung in %')
    plt.xticks(np.arange(4), ['EFH\nPV+GK','EFH\nWP+BAT','EFH\nWP','MFH\nBHKW'], fontsize = "18")
    plt.xlabel('Gebäudetypen im LEM')
    #plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.legend(bbox_to_anchor = (0, 1), loc = 'upper left', framealpha = 0.7, fontsize = "18", ncol = 2)
    plt.yticks(np.arange(0, 120, 20), fontsize = "14")
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 1)
    plt.savefig(directory + '/CH Relative gain', dpi = 600)
    #plt.show()
    print("Hi")

def opti_vs_simu_plots_new(params, results, opti_res, rows, block_length, scenario_simu, nego_results):
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario_simu)

    plt.rcParams.update({'font.size': 20}) #größere Schriftgröße für Plots nebeneinander

    # Ergebnisse ohne MPC
    init_val, rowsWoMPC3, nodes, opti_resWoMPC3, par_rh, mar_dictWoMPC3 = load_results(scenario= "\WithoutMPC", block_length=3 , monthly=True)
    resultsWoMPC3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dictWoMPC3["negotiation_results"],
                                                opti_res=opti_resWoMPC3, grid_transaction=mar_dictWoMPC3["transactions_with_grid"],
                                                params = params)

    simulation_KPIs = simulation_KPIs_per_building_p2p(rows, params, opti_res, results, nego_results)
    
    # SCF mSCF 
    plt.clf()
    plt.bar(0-0.2, 100*results["scf"], color="darkcyan", label = "SCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*results["mSCF"], color="lightblue", label = "mSCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*simulation_KPIs["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*simulation_KPIs["mscf"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsWoMPC3["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsWoMPC3["mSCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative Menge in %')
    plt.xticks(np.arange(3), ['Optimierung\n(mit MPC)','Simulation\n(mit MPC)','Optimierung\n(ohne MPC)'])
    plt.legend(fontsize=18, loc = 'upper left')
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/SCF mSCF Opti vs Simu new', dpi = 600)
    #plt.show()
    print("Hi")

    # DCF mDCF 
    plt.clf()
    plt.bar(0-0.2, 100*results["dcf"], color="darkcyan", label = "DCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*results["mDCF"], color="lightblue", label = "mDCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*simulation_KPIs["dcf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*simulation_KPIs["mdcf"], color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsWoMPC3["dcf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsWoMPC3["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative Menge in %')
    plt.xticks(np.arange(3), ['Optimierung\n(mit MPC)','Simulation\n(mit MPC)','Optimierung\n(ohne MPC)'])
    plt.legend(fontsize=18, loc = 'upper left')
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/DCF mDCF Opti vs Simu new', dpi = 600)
    #plt.show()
    print("Hi")

    # Total gain Opti vs Simu
    plt.clf()
    plt.bar(0-0.2, results["gain_per_building"][4], color="darkcyan", width = 0.2, zorder = 2, label = 'Optimierung\n(mit MPC)')
    plt.bar(0, simulation_KPIs["gain_per_building"][4], color="lightblue", width = 0.2, zorder = 2, label = 'Simulation\n(mit MPC)')
    plt.bar(0+0.2, resultsWoMPC3["gain_per_building"][4], color="lavender", width = 0.2, zorder = 2, label = 'Optimierung\n(ohne MPC)')
    plt.bar(1-0.2, results["gain_per_building"][7], color="darkcyan", width = 0.2, zorder = 2)
    plt.bar(1, simulation_KPIs["gain_per_building"][7], color="lightblue", width = 0.2, zorder = 2)
    plt.bar(1+0.2, resultsWoMPC3["gain_per_building"][7], color="lavender", width = 0.2, zorder = 2)
    plt.bar(2-0.2, results["gain_per_building"][11], color="darkcyan", width = 0.2, zorder = 2)
    plt.bar(2, simulation_KPIs["gain_per_building"][11], color="lightblue", width = 0.2, zorder = 2)
    plt.bar(2+0.2, resultsWoMPC3["gain_per_building"][11], color="lavender", width = 0.2, zorder = 2)
    plt.ylabel('Einsparung in €')
    plt.xticks(np.arange(3), ['EFH\nProsumer','EFH\nFlexumer','MFH\nProsumer'])
    plt.legend(fontsize=18, loc = 'upper left')
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/Gain per building Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

    # Total gain Opti vs Simu
    plt.clf()
    plt.bar(0-0.2, results["total_cost_per_building"][4], color="darkcyan", width = 0.2, zorder = 2, label = 'Optimierung\n(mit MPC)')
    plt.bar(0, simulation_KPIs["total_costs_per_building"][4], color="lightblue", width = 0.2, zorder = 2, label = 'Simulation\n(mit MPC)')
    plt.bar(0+0.2, resultsWoMPC3["total_cost_per_building"][4], color="lavender", width = 0.2, zorder = 2, label = 'Optimierung\n(ohne MPC)')
    plt.bar(1-0.2, results["total_cost_per_building"][7], color="darkcyan", width = 0.2, zorder = 2)
    plt.bar(1, simulation_KPIs["total_costs_per_building"][7], color="lightblue", width = 0.2, zorder = 2)
    plt.bar(1+0.2, resultsWoMPC3["total_cost_per_building"][7], color="lavender", width = 0.2, zorder = 2)
    plt.bar(2-0.2, results["total_cost_per_building"][11], color="darkcyan", width = 0.2, zorder = 2)
    plt.bar(2, simulation_KPIs["total_costs_per_building"][11], color="lightblue", width = 0.2, zorder = 2)
    plt.bar(2+0.2, resultsWoMPC3["total_cost_per_building"][11], color="lavender", width = 0.2, zorder = 2)
    plt.ylabel('Gesamtkosten in €')
    plt.xticks(np.arange(3), ['EFH\nProsumer','EFH\nFlexumer','MFH\nProsumer'])
    plt.legend(fontsize=18, loc = 'upper left')
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/Total Costs per building Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

def opti_vs_simu_plots(params, results, opti_res, rows, block_length, scenario_simu):
    directory = r"C:\Users\jsc-tma\Masterarbeit_tma\Optimierung\results\old\Medium District 12houses BOI+HP+CHP\Potsdam\3_Mar\nB=" + str(block_length) + str(scenario_simu)

    # Ergebnisse ohne MPC
    init_val, rowsWoMPC3, nodes, opti_res, par_rh, mar_dict = load_results(scenario= "\WithoutMPC", block_length=3, monthly=True)
    resultsWoMPC3 = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)

    # Kenngrößen Simulation
    scf_simu, dcf_simu, mscf_simu, mdcf_simu, total_gain_simu, total_costs_simu, real_tra_vol = simulation_KPIs_p2p(rows, params, opti_res)

    # SCF mSCF 
    plt.clf()
    plt.bar(0-0.2, 100*results["scf"], color="darkcyan", label = "SCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*results["mSCF"], color="lightblue", label = "mSCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*scf_simu, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*mscf_simu, color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsWoMPC3["scf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsWoMPC3["mSCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(3), ['Optimization\n(with MPC)','Simulation\n(with MPC)','Optimization\n(no MPC)'])
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/SCF mSCF Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

    # DCF mDCF 
    plt.clf()
    plt.bar(0-0.2, 100*results["dcf"], color="darkcyan", label = "DCF", width = 0.4, zorder = 2)
    plt.bar(0+0.2, 100*results["mDCF"], color="lightblue", label = "mDCF", width = 0.4, zorder = 2)
    plt.bar(1-0.2, 100*dcf_simu, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1+0.2, 100*mdcf_simu, color="lightblue", width = 0.4, zorder = 2)
    plt.bar(2-0.2, 100*resultsWoMPC3["dcf"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2+0.2, 100*resultsWoMPC3["mDCF"], color="lightblue", width = 0.4, zorder = 2)
    plt.ylabel('Relative quantity in %')
    plt.xticks(np.arange(3), ['Optimization\n(with MPC)','Simulation\n(with MPC)','Optimization\n(no MPC)'])
    plt.legend(fontsize=16, loc = 'upper right', bbox_to_anchor=(1, 1))
    plt.ylim((0, 100))
    plt.yticks([20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/DCF mDCF Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

    # Total traded amount
    traded_power_total_simu = sum(real_tra_vol/60)
    plt.clf()
    plt.bar(0, results["traded_power_total"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1, traded_power_total_simu, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2, resultsWoMPC3["traded_power_total"], color="darkcyan", width = 0.4, zorder = 2)
    plt.ylabel('Total traded electricity in kWh')
    plt.xticks(np.arange(3), ['Optimization\n(with MPC)','Simulation\n(with MPC)','Optimization\n(no MPC)'])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/Traded Power Gain Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

    # Total gain Opti vs Simu
    plt.clf()
    plt.bar(0, results["gain_total"], color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1, total_gain_simu, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2, resultsWoMPC3["gain_total"], color="darkcyan", width = 0.4, zorder = 2)
    plt.ylabel('Gain in €')
    plt.xticks(np.arange(3), ['Optimization\n(with MPC)','Simulation\n(with MPC)','Optimization\n(no MPC)'])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/Gain Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

    # Total costs Opti vs Simu (gas and electricity from grid)
    plt.clf()
    total_summed_up_costs = sum(results["total_cost_per_building"])
    total_summed_up_costs_noMPC = sum(resultsWoMPC3["total_cost_per_building"])
    plt.bar(0, total_summed_up_costs, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(1, total_costs_simu, color="darkcyan", width = 0.4, zorder = 2)
    plt.bar(2, total_summed_up_costs_noMPC, color="darkcyan", width = 0.4, zorder = 2)
    plt.ylabel('Total costs in €')
    plt.xticks(np.arange(3), ['Optimization\n(with MPC)','Simulation\n(with MPC)','Optimization\n(no MPC)'])
    plt.tight_layout()
    plt.grid(True, linewidth = 0.5, zorder = 2)
    plt.savefig(directory + '/Opti_vs_Simu_plots/Total Costs Opti vs Simu', dpi = 600)
    #plt.show()
    print("Hi")

block_length = 3
monthly = False
scenario = "\HeatDem_2Sto" # HeatDem_2Sto, HeatDem_CombiSto, ROM_2Sto, WithoutMPC
init_val, rows, nodes, opti_res, par_rh, mar_dict = load_results(scenario=scenario, block_length=block_length, monthly=monthly)
params = parse_inputs.read_economics()

simulation_plots_hp(rows=rows["6"], rows_all = rows["all"], no_house=6, par_rh=par_rh, opti_res=opti_res, scenario=scenario, block_length=block_length, nodes=nodes)
#simulation_plots_chp(rows=rows["11"], no_house=11, par_rh=par_rh, opti_res=opti_res, scenario=scenario, block_length=block_length)
results = calc_results_p2p(par_rh=par_rh, block_length=block_length,
                                                nego_results=mar_dict["negotiation_results"],
                                                opti_res=opti_res, grid_transaction=mar_dict["transactions_with_grid"],
                                                params = params)

#simulation_KPIs_per_building_p2p(rows=rows, params=params, opti_res=opti_res, results=results, nego_results=mar_dict["negotiation_results"])
#opti_vs_simu_plots_new(params=params, results=results, opti_res=opti_res, rows=rows, block_length=block_length, scenario_simu=scenario, nego_results=mar_dict["negotiation_results"])
#p2p_plots_compared(params=params)
#p2p_plots(results=results, par_rh=par_rh, opti_res=opti_res, scenario=scenario, block_length=block_length)
print("HI")
