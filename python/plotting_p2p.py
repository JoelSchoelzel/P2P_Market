import matplotlib.pyplot as plt
import pandas as pd

# transform the data saved in mar_dict into a DataFrame, in order to plot them with matplotlib

def mar_dict_to_df(mar_dict,par_rh):
    """Transform the data saved in mar_dict into a DataFrame, in order to plot them with matplotlib"""

    time_steps = []
    traded_power = []
    for n_opt in range(len(par_rh["org_time_steps"])):
        time_steps.append(par_rh["hour_start"][n_opt])
        traded_power.append(mar_dict["total_market_info"][n_opt]["total_traded_volume"])

    data = {
        "time_steps": time_steps,
        "traded_power_within_district": traded_power
    }

    df = pd.DataFrame(data)

    return df



"""file_name = "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/P2P_opti_output/scenario2.p"

with open(file_name, "rb") as f:
    data = pickle.load(f)

for building in data[0][0]:
    p_buy = list()
    p_sell = list()
    for time_step in data:
        p_buy.append(data[time_step][4][building][time_step])
        p_sell.append(data[time_step][8][building]["chp"][time_step])
    plt.plot(p_buy)
    plt.plot(p_sell)
    plt.title(f"Building {building}")
    plt.show()

    # EBC and RWTH colors
    colors = {  # EBC colors
        "red": '#DD402D', "darkgray": '#4E4F50', "gray": '#9D9EA0', "lightgray": '#C4C5C6',
        # following: RWTH colors
        "black100": '000000', "black75": '#646567', "black50": '#9C9E9F', "black25": '#CFD1D2',
        "red100": '#CC071E', "red75": '#D85C41', "red50": '#E69679',
        "bordeaux100": '#A11035', "bordeaux75": '#B65256', "bordeaux50": '#CD8B87',
        "orange100": '#F6A800', "orange75": '#FABE50', "orange50": '#FDD48F',
        "green100": '# 57AB27', "green75": '#8DC060', "green50": '#B8D698',
        "blue100": '#00549F', "blue75": '#407FB7 ', "blue50": '#8EBAE5'}
    
    colorscheme = [colors["black25"], colors["black50"], colors["red100"]]  # color scheme for unstacked bar plots


    plt.rc('axes', axisbelow=True) # grid in background


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
    fig.savefig(options_plot["path_save_figures"] + "\\" + name, bbox_inches='tight')"""

