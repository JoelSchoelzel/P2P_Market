

import matplotlib.pyplot as plt
import matplotlib
import pickle
import pandas as pd
import os



def plot_peak_power_tranformer_to_grid(options_plot, data, colors):

    if options_plot["mode"] == 1:
        title = "80% SFH / 20% MFH: Peak power of transformer (to grid)"
        name = "SFH-MFH_P_peak_trafo_to_grid"
    else:
        title = "100% TH: Peak power of transformer (to grid)"
        name = "TH_P_peak_trafo_to_grid"

    df = pd.DataFrame([["1969-1978", data[0][0]["peak_power_transformer_to_grid"], data[1][0]["peak_power_transformer_to_grid"], data[2][0]["peak_power_transformer_to_grid"]],
                       ["1984-1994", data[3][0]["peak_power_transformer_to_grid"], data[4][0]["peak_power_transformer_to_grid"], data[5][0]["peak_power_transformer_to_grid"]],
                       ["2002-2009", data[6][0]["peak_power_transformer_to_grid"], data[7][0]["peak_power_transformer_to_grid"], data[8][0]["peak_power_transformer_to_grid"]]],
                      columns=["construction period", "00% FC", "25% FC", "50% FC"])

    ax = df.plot(x="construction period", rot=0, ylabel="P_peak transformer to grid [kW]", kind="bar", grid=True, stacked=False,
                 title=title, color=colors)
    ax.legend(bbox_to_anchor=(1.0, 0.5))
    fig = ax.get_figure()
    fig.savefig(options_plot["path_save_figures"] + "\\" + name, bbox_inches='tight')

    if options_plot["show_plots"]:
        plt.show()

def plot_peak_power_tranformer_from_grid(options_plot, data, colors):

    if options_plot["mode"] == 1:
        title = "80% SFH / 20% MFH: Peak power of transformer (from grid)"
        name = "SFH-MFH_P_peak_trafo_from_grid"
    else:
        title = "100% TH: Peak power of transformer (from grid)"
        name = "TH_P_peak_trafo_from_grid"

    df = pd.DataFrame([["1969-1978", data[0][0]["peak_power_transformer_from_grid"], data[1][0]["peak_power_transformer_from_grid"], data[2][0]["peak_power_transformer_from_grid"]],
                       ["1984-1994", data[3][0]["peak_power_transformer_from_grid"], data[4][0]["peak_power_transformer_from_grid"], data[5][0]["peak_power_transformer_from_grid"]],
                       ["2002-2009", data[6][0]["peak_power_transformer_from_grid"], data[7][0]["peak_power_transformer_from_grid"], data[8][0]["peak_power_transformer_from_grid"]]],
                      columns=["construction period", "00% FC", "25% FC", "50% FC"])

    ax = df.plot(x="construction period", rot=0, ylabel="P_peak transformer from grid [kW]", kind="bar", grid=True, stacked=False,
                 title=title, color=colors)
    ax.legend(bbox_to_anchor=(1.0, 0.5))
    fig = ax.get_figure()
    fig.savefig(options_plot["path_save_figures"] + "\\" + name, bbox_inches='tight')

    if options_plot["show_plots"]:
        plt.show()

def plot_CO2_emissions(options_plot, data, colors):

    if options_plot["mode"] == 1:
        title = "80% SFH / 20% MFH: CO2 emissions"
        name = "SFH-MFH_CO2"
    else:
        title = "100% TH: CO2 emissions"
        name = "TH_CO2"

    #matplotlib.style.use('ggplot')

    FC00 = pd.DataFrame({
        "Gas (00% FC)": [40, 12, 10],
        "El (00% FC)": [19, 8, 30],
        "PV Gen (00% FC)": [10, 10, 42]
    }, index=["1969-1978", "1984-1994", "2002-2009"]
    )

    FC25 = pd.DataFrame({
        "Gas (25% FC)": [20, 22, 10],
        "El (25% FC)": [12, 19, 27],
        "PV Gen (25% FC)": [21, 31, 52]
    }, index=["1969-1978", "1984-1994", "2002-2009"]
    )

    FC50 = pd.DataFrame({
        "Gas (50% FC)": [20, 22, 10],
        "El (50% FC)": [12, 19, 27],
        "PV Gen (50% FC)": [21, 31, 52]
    }, index=["1969-1978", "1984-1994", "2002-2009"]
    )

    fig, ax = plt.subplots()

    FC50.plot(kind="bar", rot=0,  stacked=True, width=0.22, color=[colors["black75"], colors["red100"], colors["orange100"]],
                      ax=ax, position=-0.5, title=title, xlabel="construction period",
                        ylabel="CO2 emissions [kg]", grid=True)
    FC25.plot(kind="bar", rot=0, stacked=True, width=0.22, color=[colors["black50"], colors["red75"], colors["orange75"]],
                       ax=ax, position=0.5, grid=True)
    FC00.plot(kind="bar", rot=0, stacked=True, width=0.22, color=[colors["black25"], colors["red50"], colors["orange50"]],
                       ax=ax, position=1.5, grid=True) #hatch='//'


    ax.set_xlim(right=len(FC00) - 0.5)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],bbox_to_anchor=(1.0, 0.9))
    fig = ax.get_figure()
    fig.savefig(options_plot["path_save_figures"] + "\\" + name, bbox_inches='tight')

    if options_plot["show_plots"]:
        plt.show()



if __name__ == '__main__':

    options_plot = {"mode": 2, # 1: 80% SFH / 20% MFH -or- 2: 100% TH
                    # if mode is changed: adjust paths_in
                    "T": [10, 14], # Temp_heating_limit_SF_BZ [T_low, T_high]
                    "show_plots": True,
                    "path_save_figures": 'C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\plots\\Testreihe01'}

    if not os.path.exists(options_plot["path_save_figures"]):
        os.makedirs(options_plot["path_save_figures"])

    # add paths to pickle files to be loaded here:
    paths_in = ["C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p",  #0: 1969-1978, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p",  #1: 1969-1978, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p",  #2: 1969-1978, 50% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p",  #3: 1984-1994, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p",  #4: 1984-1994, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p",  #5: 1984-1994, 50% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T10.p",  #6: 2002-2009, 0% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T12.p",  #7: 2002-2009, 25% BZ
                "C:\\Users\\Arbeit\\Documents\\WiHi_EBC\\MAScity\\results\\criteria_district_Neubau_T14.p"]  #8: 2002-2009, 50% BZ

    # read data
    data = []
    for k in range(paths_in.__len__()):
        with open(paths_in[k], 'rb') as f:
            data.append(pickle.load(f))

    # EBC and RWTH colors
    colors = {# EBC colors
              "red": '#DD402D', "darkgray": '#4E4F50', "gray": '#9D9EA0', "lightgray": '#C4C5C6',
              # following: RWTH colors
              "black100": '000000', "black75": '#646567', "black50": '#9C9E9F', "black25": '#CFD1D2',
              "red100": '#CC071E', "red75": '#D85C41', "red50": '#E69679',
              "bordeaux100": '#A11035', "bordeaux75": '#B65256', "bordeaux50": '#CD8B87',
              "orange100": '#F6A800', "orange75": '#FABE50', "orange50": '#FDD48F',
              "green100": '# 57AB27', "green75": '#8DC060', "green50": '#B8D698',
              "blue100": '#00549F', "blue75": '#407FB7 ', "blue50": '#8EBAE5'}

    colorscheme = [colors["black25"], colors["black50"], colors["red100"]] # color scheme for unstacked bar plots

    plt.rc('axes', axisbelow=True) # grid in background

    plot_peak_power_tranformer_to_grid(options_plot, data, colorscheme)

    plot_peak_power_tranformer_from_grid(options_plot, data, colorscheme)

    plot_CO2_emissions(options_plot, data, colors)





