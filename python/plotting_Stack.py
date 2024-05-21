import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import rc
import pandas as pd
import pickle
import os

# Setting the font for the plots
rc("font", **{"family": "sans-serif", "sans-serif": "Times New Roman"})

# Base path for results
path_root = "C:\\Users\\cemca\\PycharmProjects\\MA\\P2P_Market\\results\\results_for_plotting"

# Load data for quartier_3, july, block bids, block horizon
Q3_Jul_bb_bh_ts_path = os.path.join(path_root, 'Quartier_3', 'Jul', 'block_bids', 'block_horizon', 'res_time_step.pkl')
Q3_Jul_bb_bh_m_path = os.path.join(path_root, 'Quartier_3', 'Jul', 'block_bids', 'block_horizon', 'res_month.pkl')

# load data for quartier_3, january, block bids, block horizon
Q3_Jan_bb_bh_ts_path = os.path.join(path_root, 'Quartier_3', 'Jan', 'block_bids', 'block_horizon', 'res_time_step.pkl')
Q3_Jan_bb_bh_m_path = os.path.join(path_root, 'Quartier_3', 'Jan', 'block_bids', 'block_horizon', 'res_month.pkl')

# Load data for quartier_3, april, block bids, block horizon
Q3_Apr_bb_bh_ts_path = os.path.join(path_root, 'Quartier_3', 'Apr', 'block_bids', 'block_horizon', 'res_time_step.pkl')
Q3_Apr_bb_bh_m_path = os.path.join(path_root, 'Quartier_3', 'Apr', 'block_bids', 'block_horizon', 'res_month.pkl')

Jul_bh_time_step, Jul_bh_month = None, None
Jan_bh_time_step, Jan_bh_month = None, None
Apr_bh_time_step, Apr_bh_month = None, None

try:
    with open(Q3_Jul_bb_bh_ts_path, 'rb') as f:
        Jul_bh_time_step = pickle.load(f)
    with open(Q3_Jul_bb_bh_m_path, 'rb') as f:
        Jul_bh_month = pickle.load(f)
except FileNotFoundError:
    print("File not found for July")

try:
    with open(Q3_Jan_bb_bh_ts_path, 'rb') as f:
        Jan_bh_time_step = pickle.load(f)
    with open(Q3_Jan_bb_bh_m_path, 'rb') as f:
        Jan_bh_month = pickle.load(f)
except FileNotFoundError:
    print("File not found for January")

try:
    with open(Q3_Apr_bb_bh_ts_path, 'rb') as f:
        Apr_bh_time_step = pickle.load(f)
    with open(Q3_Apr_bb_bh_m_path, 'rb') as f:
        Apr_bh_month = pickle.load(f)
except FileNotFoundError:
    print("File not found for April")


# Load data for quartier_3, july, block bids, total horizon
Q3_Jul_bb_th_ts_path = os.path.join(path_root, 'Quartier_3', 'Jul', 'block_bids', 'total_horizon', 'res_time_step.pkl')
Q3_Jul_bb_th_m_path = os.path.join(path_root, 'Quartier_3', 'Jul', 'block_bids', 'total_horizon', 'res_month.pkl')

# Load data for quartier_3, january, block bids, total horizon
Q3_Jan_bb_th_ts_path = os.path.join(path_root, 'Quartier_3', 'Jan', 'block_bids', 'total_horizon', 'res_time_step.pkl')
Q3_Jan_bb_th_m_path = os.path.join(path_root, 'Quartier_3', 'Jan', 'block_bids', 'total_horizon', 'res_month.pkl')

# Load data for quartier_3, april, block bids, total horizon
Q3_Apr_bb_th_ts_path = os.path.join(path_root, 'Quartier_3', 'Apr', 'block_bids', 'total_horizon', 'res_time_step.pkl')
Q3_Apr_bb_th_m_path = os.path.join(path_root, 'Quartier_3', 'Apr', 'block_bids', 'total_horizon', 'res_month.pkl')

Jul_th_time_step, Jul_th_month = None, None
Jan_th_time_step, Jan_th_month = None, None
Apr_th_time_step, Apr_th_month = None, None

try:
    with open(Q3_Jul_bb_th_ts_path, 'rb') as f:
        Jul_th_time_step = pickle.load(f)
    with open(Q3_Jul_bb_th_m_path, 'rb') as f:
        Jul_th_month = pickle.load(f)
except FileNotFoundError:
    print("File for monthly data not found for July")

try:
    with open(Q3_Jan_bb_th_ts_path, 'rb') as f:
        Jan_th_time_step = pickle.load(f)
    with open(Q3_Jan_bb_th_m_path, 'rb') as f:
        Jan_th_month = pickle.load(f)
except FileNotFoundError:
    print("File for monthly data not found for January")

try:
    with open(Q3_Apr_bb_th_ts_path, 'rb') as f:
        Apr_th_time_step = pickle.load(f)
    with open(Q3_Apr_bb_th_m_path, 'rb') as f:
        Apr_th_month = pickle.load(f)
except FileNotFoundError:
    print("File for monthly data not found for April")

# ------------ RWTH COLORS ------------
red = ['#CC071E', '#D85C41', '#E69679', '#F3CDBB', '#FAEBE3']
blue = ['#00549F', '#407FB7', '#8EBAE5', '#C7DDF2', '#E8F1FA']
violet = ['#7A6FAC', '#9B91C1', '#BCB5D7', '#DEDAEB', '#F2F0F7']
green = ['#57ab27', '#8dc060', '#b8d698', '#ddebce', '#f2f7ec']
bordeaux = ['#a11035', '#b65256', '#cd8b87', '#e5c5c0', '#f5e8e5']
black = ['#000000', '#696969', '', '#808080', '#A9A9A9', '#DCDCDC']

# ------------ EBC COLORS ------------
red_ebc = ['#CC071E', '#DD402D', '#D85C41', '#E69679']
orange_ebc = ['#F6A800', '#FABE50', '#FDD48F']
blue_ebc = ['#00549F', '#407FB7 ', '#8EBAE5']
green_ebc = ['#57AB27', '#8DC060', '#B8D698']
bordeaux_ebc = ['#A11035', '#B65256', '#CD8B87',]
black_ebc = ['#000000', '#646567', '#9C9E9F', '#CFD1D2']
grey_ebc = ['#4E4F50', '#9D9EA0', '#C4C5C6']

horizon = 'total_horizon'  # or 'block_horizon'

# ------------ Extracting data for time steps ------------
# Extracting data for time steps for January
if horizon == 'block_horizon':
    if Jan_bh_time_step:
        time_steps_jan = list(Jan_bh_time_step['traded_power_market'].keys())
        traded_power_market_jan = list(Jan_bh_time_step['traded_power_market'].values())
        power_from_grid_jan = list(Jan_bh_time_step['power_from_grid'].values())
        power_to_grid_jan = list(Jan_bh_time_step['power_to_grid'].values())
        initial_demand_jan = list(Jan_bh_time_step['initial_demand'].values())
        final_demand_jan = list(Jan_bh_time_step['final_demand'].values())
        total_supply_jan = list(Jan_bh_time_step['total_supply'].values())
        total_demand_jan = list(Jan_bh_time_step['total_demand'].values())
        gain_jan = list(Jan_bh_time_step['gain'].values())
        scf_jan = list(Jan_bh_time_step['scf'].values())
        dcf_jan = list(Jan_bh_time_step['dcf'].values())
        mscf_jan = list(Jan_bh_time_step['mscf'].values())
        mdcf_jan = list(Jan_bh_time_step['mdcf'].values())
        soc_bat_jan = Jan_bh_time_step['soc_bat'][11]
        soc_tes_jan = Jan_bh_time_step['soc_tes'][18]
else:
    if Jan_th_time_step:
        time_steps_jan = list(Jan_th_time_step['traded_power_market'].keys())
        traded_power_market_jan = list(Jan_th_time_step['traded_power_market'].values())
        power_from_grid_jan = list(Jan_th_time_step['power_from_grid'].values())
        power_to_grid_jan = list(Jan_th_time_step['power_to_grid'].values())
        initial_demand_jan = list(Jan_th_time_step['initial_demand'].values())
        final_demand_jan = list(Jan_th_time_step['final_demand'].values())
        total_supply_jan = list(Jan_th_time_step['total_supply'].values())
        total_demand_jan = list(Jan_th_time_step['total_demand'].values())
        gain_jan = list(Jan_th_time_step['gain'].values())
        scf_jan = list(Jan_th_time_step['scf'].values())
        dcf_jan = list(Jan_th_time_step['dcf'].values())
        mscf_jan = list(Jan_th_time_step['mscf'].values())
        mdcf_jan = list(Jan_th_time_step['mdcf'].values())
        soc_bat_jan = Jan_th_time_step['soc_bat'][11]
        soc_tes_jan = Jan_th_time_step['soc_tes'][18]

# Extracting data for time steps for April
if horizon == 'block_horizon':
    if Apr_bh_time_step:
        time_steps_apr = list(Apr_bh_time_step['traded_power_market'].keys())
        traded_power_market_apr = list(Apr_bh_time_step['traded_power_market'].values())
        power_from_grid_apr = list(Apr_bh_time_step['power_from_grid'].values())
        power_to_grid_apr = list(Apr_bh_time_step['power_to_grid'].values())
        initial_demand_apr = list(Apr_bh_time_step['initial_demand'].values())
        final_demand_apr = list(Apr_bh_time_step['final_demand'].values())
        total_supply_apr = list(Apr_bh_time_step['total_supply'].values())
        total_demand_apr = list(Apr_bh_time_step['total_demand'].values())
        gain_apr = list(Apr_bh_time_step['gain'].values())
        scf_apr = list(Apr_bh_time_step['scf'].values())
        dcf_apr = list(Apr_bh_time_step['dcf'].values())
        mscf_apr = list(Apr_bh_time_step['mscf'].values())
        mdcf_apr = list(Apr_bh_time_step['mdcf'].values())
        soc_bat_apr = Apr_bh_time_step['soc_bat'][11]
        soc_tes_apr = Apr_bh_time_step['soc_tes'][18]
else:
    if Apr_th_time_step:
        time_steps_apr = list(Apr_th_time_step['traded_power_market'].keys())
        traded_power_market_apr = list(Apr_th_time_step['traded_power_market'].values())
        power_from_grid_apr = list(Apr_th_time_step['power_from_grid'].values())
        power_to_grid_apr = list(Apr_th_time_step['power_to_grid'].values())
        initial_demand_apr = list(Apr_th_time_step['initial_demand'].values())
        final_demand_apr = list(Apr_th_time_step['final_demand'].values())
        total_supply_apr = list(Apr_th_time_step['total_supply'].values())
        total_demand_apr = list(Apr_th_time_step['total_demand'].values())
        gain_apr = list(Apr_th_time_step['gain'].values())
        scf_apr = list(Apr_th_time_step['scf'].values())
        dcf_apr = list(Apr_th_time_step['dcf'].values())
        mscf_apr = list(Apr_th_time_step['mscf'].values())
        mdcf_apr = list(Apr_th_time_step['mdcf'].values())
        soc_bat_apr = Apr_th_time_step['soc_bat'][11]
        soc_tes_apr = Apr_th_time_step['soc_tes'][18]

# Extracting data for time steps for July
if horizon == 'block_horizon':
    time_steps_jul = list(Jul_bh_time_step['traded_power_market'].keys())
    traded_power_market_jul = list(Jul_bh_time_step['traded_power_market'].values())
    power_from_grid_jul = list(Jul_bh_time_step['power_from_grid'].values())
    power_to_grid_jul = list(Jul_bh_time_step['power_to_grid'].values())
    initial_demand_jul = list(Jul_bh_time_step['initial_demand'].values())
    final_demand_jul = list(Jul_bh_time_step['final_demand'].values())
    total_supply_jul = list(Jul_bh_time_step['total_supply'].values())
    total_demand_jul = list(Jul_bh_time_step['total_demand'].values())
    gain_jul = list(Jul_bh_time_step['gain'].values())
    scf_jul = list(Jul_bh_time_step['scf'].values())
    dcf_jul = list(Jul_bh_time_step['dcf'].values())
    mscf_jul = list(Jul_bh_time_step['mscf'].values())
    mdcf_jul = list(Jul_bh_time_step['mdcf'].values())
    soc_bat_jul = Jul_bh_time_step['soc_bat'][11]
    soc_tes_jul = Jul_bh_time_step['soc_tes'][18]
else:
    time_steps_jul = list(Jul_th_time_step['traded_power_market'].keys())
    traded_power_market_jul = list(Jul_th_time_step['traded_power_market'].values())
    power_from_grid_jul = list(Jul_th_time_step['power_from_grid'].values())
    power_to_grid_jul = list(Jul_th_time_step['power_to_grid'].values())
    initial_demand_jul = list(Jul_th_time_step['initial_demand'].values())
    final_demand_jul = list(Jul_th_time_step['final_demand'].values())
    total_supply_jul = list(Jul_th_time_step['total_supply'].values())
    total_demand_jul = list(Jul_th_time_step['total_demand'].values())
    gain_jul = list(Jul_th_time_step['gain'].values())
    scf_jul = list(Jul_th_time_step['scf'].values())
    dcf_jul = list(Jul_th_time_step['dcf'].values())
    mscf_jul = list(Jul_th_time_step['mscf'].values())
    mdcf_jul = list(Jul_th_time_step['mdcf'].values())
    soc_bat_jul = Jul_th_time_step['soc_bat'][11]
    soc_tes_jul = Jul_th_time_step['soc_tes'][18]

# ------------ Extracting data for the whole month ------------
# Extracting data for month in January
if horizon == 'block_horizon':
    if Jan_bh_month:
        trade_power_month_jan = Jan_bh_month['traded_power_month']
        power_from_grid_month_jan = Jan_bh_month['power_from_grid_month']
        power_to_grid_month_jan = Jan_bh_month['power_to_grid_month']
        gain_month_jan = Jan_bh_month['gain_month']
        scf_month_jan = Jan_bh_month['scf_month']
        dcf_month_jan = Jan_bh_month['dcf_month']
        mscf_month_jan = Jan_bh_month['mscf_month']
        mdcf_month_jan = Jan_bh_month['mdcf_month']
else:
    if Jan_th_month:
        trade_power_month_jan = Jan_th_month['traded_power_month']
        power_from_grid_month_jan = Jan_th_month['power_from_grid_month']
        power_to_grid_month_jan = Jan_th_month['power_to_grid_month']
        gain_month_jan = Jan_th_month['gain_month']
        scf_month_jan = Jan_th_month['scf_month']
        dcf_month_jan = Jan_th_month['dcf_month']
        mscf_month_jan = Jan_th_month['mscf_month']
        mdcf_month_jan = Jan_th_month['mdcf_month']

# Extracting data for month in April
if horizon == 'block_horizon':
    if Apr_bh_month:
        trade_power_month_apr = list(Apr_bh_month['traded_power_month'])
        power_from_grid_month_apr = list(Apr_bh_month['power_from_grid_month'])
        power_to_grid_month_apr = list(Apr_bh_month['power_to_grid_month'])
        gain_month_apr = list(Apr_bh_month['gain_month'])
        scf_month_apr = list(Apr_bh_month['scf_month'])
        dcf_month_apr = list(Apr_bh_month['dcf_month'])
        mscf_month_apr = list(Apr_bh_month['mscf_month'])
        mdcf_month_apr = list(Apr_bh_month['mdcf_month'])
else:
    if Apr_th_month:
        trade_power_month_apr = list(Apr_th_month['traded_power_month'])
        power_from_grid_month_apr = list(Apr_th_month['power_from_grid_month'])
        power_to_grid_month_apr = list(Apr_th_month['power_to_grid_month'])
        gain_month_apr = list(Apr_th_month['gain_month'])
        scf_month_apr = list(Apr_th_month['scf_month'])
        dcf_month_apr = list(Apr_th_month['dcf_month'])
        mscf_month_apr = list(Apr_th_month['mscf_month'])
        mdcf_month_apr = list(Apr_th_month['mdcf_month'])

# Extracting data for month in July
if horizon == 'block_horizon':
    trade_power_month_jul = Jul_bh_month['traded_power_month']
    power_from_grid_month_jul = Jul_bh_month['power_from_grid_month']
    power_to_grid_month_jul = Jul_bh_month['power_to_grid_month']
    gain_month_jul = Jul_bh_month['gain_month'] /1000
    scf_month_jul = Jul_bh_month['scf_month']
    dcf_month_jul = Jul_bh_month['dcf_month']
    mscf_month_jul = Jul_bh_month['mscf_month']
    mdcf_month_jul = Jul_bh_month['mdcf_month']
else:
    trade_power_month_jul = Jul_th_month['traded_power_month']
    power_from_grid_month_jul = Jul_th_month['power_from_grid_month']
    power_to_grid_month_jul = Jul_th_month['power_to_grid_month']
    gain_month_jul = Jul_th_month['gain_month'] / 1000
    scf_month_jul = Jul_th_month['scf_month']
    dcf_month_jul = Jul_th_month['dcf_month']
    mscf_month_jul = Jul_th_month['mscf_month']
    mdcf_month_jul = Jul_th_month['mdcf_month']

# Define the path to save plots
plot_save_path = "C:\\Users\\cemca\\PycharmProject\\MA\\P2P_Market\\results\\Plots"
os.makedirs(plot_save_path, exist_ok=True)

# Function to convert time steps to days
# def time_steps_to_days(time_steps):
#     return [t / 24 for t in time_steps]
# Convert time steps to days for better readability
time_steps_days_jan = [t / 24 for t in time_steps_jan]
time_steps_days_jul = [t / 24 for t in time_steps_jul]



plt.figure(figsize=(10, 5))

# ------------ Time step plots for January ------------
# Plot 1: Total traded power inside the district
plt.plot(time_steps_days_jan, total_supply_jan, label='Total Supply', color=green_ebc[0])
plt.plot(time_steps_days_jan, total_demand_jan, label='Total Demand', color=red_ebc[0])
plt.plot(time_steps_days_jan, traded_power_market_jan, label='Traded Power', color=blue_ebc[0])
plt.xlabel('Time [Days]', fontsize=14)
plt.ylabel('Power [kWh]', fontsize=14)
plt.title('Total supply, demand and traded power inside the District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Total_Traded_Power_January.png")
plot_name_svg = os.path.join(plot_save_path, "Total_Traded_Power_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 2: Power import/export to the grid
plt.plot(time_steps_jan, power_from_grid_jan, label='Power from Grid', color=orange_ebc[0])
plt.plot(time_steps_jan, power_to_grid_jan, label='Power to Grid', color=blue_ebc[0])
plt.xlabel('Time [h]')
plt.ylabel('Power [kWh]')
plt.title('Power Import/Export to the Grid for District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Power_Import_Export_January.png")
plot_name_svg = os.path.join(plot_save_path, "Power_Import_Export_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 3: Initial demand, resulting demand, and available supply
plt.plot(time_steps_days_jan, initial_demand_jan, label='Initial Demand', color=red_ebc[2])
plt.plot(time_steps_days_jan, final_demand_jan, label='Resulting Demand', color=green_ebc[2])
plt.plot(time_steps_days_jan, total_supply_jan, label='Available Supply', color=black_ebc[0])
plt.xlabel('Time [Days]')
plt.ylabel('Amount [kWh]')
plt.title('Demand Change and Available Supply for District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Demand_Supply_January.png")
plot_name_svg = os.path.join(plot_save_path, "Demand_Supply_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 4: Economic gain
plt.plot(time_steps_days_jan, gain_jan, label='Economic Gain', color=green_ebc[2])
plt.xlabel('Time [h]]')
plt.ylabel('Gain [€]')
plt.title('Economic Gain for District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Economic_Gain_January.png")
plot_name_svg = os.path.join(plot_save_path, "Economic_Gain_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Define how many hours you want to display (120 for the first 5 days)
hours_to_display = 24   # 24 hours per day * days

# Adjust the time steps and the corresponding values for the first 5 days
time_steps_days_jan_section = time_steps_days_jan[:hours_to_display]
scf_jan_section = scf_jan[:hours_to_display]
dcf_jan_section = dcf_jan[:hours_to_display]
mscf_jan_section = mscf_jan[:hours_to_display]
mdcf_jan_section = mdcf_jan[:hours_to_display]
# Plot 5: Supply Coverage Factor (SCF) and Demand Coverage Factor (DCF)
plt.scatter(time_steps_days_jan_section, scf_jan_section, label='SCF', color=blue_ebc[2], marker='^')
plt.scatter(time_steps_days_jan_section, dcf_jan_section, label='DCF', color=red_ebc[2], marker='s')
plt.xlabel('Time [Days]')
plt.ylabel('Factor [%]')
plt.title('SCF and DCF for District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "SCF_DCF_January.png")
plot_name_svg = os.path.join(plot_save_path, "SCF_DCF_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 6: Market Supply Coverage Factor (MSCF) and Market Demand Coverage Factor (MDCF)
plt.scatter(time_steps_days_jan_section, mscf_jan_section, label='MSCF', color=green_ebc[2], marker='^')
plt.scatter(time_steps_days_jan_section, mdcf_jan_section, label='MDCF', color=black_ebc[2], marker='s')
plt.xlabel('Time [Days]')
plt.ylabel('Factor [%]')
plt.title('MSCF and MDCF for District 3 in January')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "MSCF_MDCF_January.png")
plot_name_svg = os.path.join(plot_save_path, "MSCF_MDCF_January.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# ------------ Time step plots for July ------------
# Plot 1: Total traded power inside the district
plt.plot(time_steps_days_jul, total_supply_jul, label='Total Supply', color=green_ebc[0])
plt.plot(time_steps_days_jul, total_demand_jul, label='Total Demand', color=red_ebc[0])
plt.plot(time_steps_days_jul, traded_power_market_jul, label='Traded Power', color=blue_ebc[0])
plt.xlabel('Time [Days]', fontsize=14)
plt.ylabel('Power [kWh]', fontsize=14)
plt.title('Total supply, demand and traded power inside the district 3 in July')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Total_Traded_Power_July.png")
plot_name_svg = os.path.join(plot_save_path, "Total_Traded_Power_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 2: Power import/export to the grid
plt.plot(time_steps_jul, power_from_grid_jul, label='Power from Grid', color=orange_ebc[0])
plt.plot(time_steps_jul, power_to_grid_jul, label='Power to Grid', color=blue_ebc[0])
plt.xlabel('Time [h]')
plt.ylabel('Power [kWh]')
plt.title('Power Import/Export to the Grid for District 3 in July')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Power_Import_Export_July.png")
plot_name_svg = os.path.join(plot_save_path, "Power_Import_Export_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 3: Initial demand, resulting demand, and available supply
plt.plot(time_steps_days_jul, initial_demand_jul, label='Initial Demand', color=red_ebc[2])
plt.plot(time_steps_days_jul, final_demand_jul, label='Resulting Demand', color=green_ebc[2])
plt.plot(time_steps_days_jul, total_supply_jul, label='Available Supply', color=black_ebc[0])
plt.xlabel('Time [h]')
plt.ylabel('Amount [kWh]')
plt.title('Demand Change and Available Supply for District 3 in July')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Demand_Supply_July.png")
plot_name_svg = os.path.join(plot_save_path, "Demand_Supply_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 4: Economic gain
plt.plot(time_steps_days_jul, gain_jul, label='Economic Gain', color=green_ebc[2])
plt.xlabel('Time [h]]')
plt.ylabel('Gain [€*1000]')
plt.title('Economic Gain')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Economic_Gain_July.png")
plot_name_svg = os.path.join(plot_save_path, "Economic_Gain_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Define how many hours you want to display (120 for the first 5 days)
hours_to_display = 24   # 24 hours per day * 5 days

# Adjust the time steps and the corresponding values for the first 5 days
time_steps_days_jul_section = time_steps_days_jul[:hours_to_display]
scf_jul_section = scf_jul[:hours_to_display]
dcf_jul_section = dcf_jul[:hours_to_display]
mscf_jul_section = mscf_jul[:hours_to_display]
mdcf_jul_section = mdcf_jul[:hours_to_display]
# Plot 5: Supply Coverage Factor (SCF) and Demand Coverage Factor (DCF)
plt.scatter(time_steps_days_jul_section, scf_jul_section, label='SCF', color=blue_ebc[2], marker='^')
plt.scatter(time_steps_days_jul_section, dcf_jul_section, label='DCF', color=red_ebc[2], marker='s')
plt.xlabel('Time [Days]')
plt.ylabel('Factor [%]')
plt.title('Supply Coverage Factor (SCF) and Demand Coverage Factor (DCF)')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "SCF_DCF_July.png")
plot_name_svg = os.path.join(plot_save_path, "SCF_DCF_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 6: Market Supply Coverage Factor (MSCF) and Market Demand Coverage Factor (MDCF)
plt.scatter(time_steps_days_jul_section, mscf_jul_section, label='MSCF', color=green_ebc[2], marker='^')
plt.scatter(time_steps_days_jul_section, mdcf_jul_section, label='MDCF', color=black_ebc[2], marker='s')
plt.xlabel('Time [Days]')
plt.ylabel('Factor [%]')
plt.title('Market Supply Coverage Factor (MSCF) and Market Demand Coverage Factor (MDCF)')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "MSCF_MDCF_July.png")
plot_name_svg = os.path.join(plot_save_path, "MSCF_MDCF_July.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 7: SOC of battery for building 11 in District 3 in July and January
plt.plot(soc_bat_jul, label='SoC Battery Jul', color=blue_ebc[0])
plt.plot(soc_bat_jan, label='SoC Battery Jan', color=red_ebc[0])
plt.xlabel('Time [Days]')
plt.ylabel('SoC [kWh]')
plt.title('SoC of Battery for Building 11 in District 3')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "SOC_Battery_11.png")
plot_name_svg = os.path.join(plot_save_path, "SOC_Battery_11.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 8: SOC of TES for building 18 in District 3 in July and January
plt.plot(soc_tes_jul, label='SoC TES Jul', color=green_ebc[0])
plt.plot(soc_tes_jan, label='SoC TES Jan', color=orange_ebc[0])
plt.xlabel('Time [Days]')
plt.ylabel('SoC [kWh]')
plt.title('SoC of TES for Building 18 in District 3')
plt.legend(fontsize=12)
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "SOC_TES_18.png")
plot_name_svg = os.path.join(plot_save_path, "SOC_TES_18.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()


# ------------ Monthly plots ------------
months_full = ['January', 'April', 'July']

if horizon == 'block_horizon':
    try:
       Jan_bh_month
       Apr_bh_month
    except NameError:
        print("Variables for block horizon are not defined")
        Jan_bh_month = None
        Apr_bh_month = None
else:
    try:
        Jan_th_month
        Apr_th_month
    except NameError:
        print("Variables for total horizon are not defined")
        Jan_th_month = None
        Apr_th_month = None

# Plot 1: Total trade inside the district
total_traded_power = [trade_power_month_jan,
                      trade_power_month_apr if Apr_bh_month else 0,
                      trade_power_month_jul]
plt.figure(figsize=(10, 5))
plt.bar(months_full, total_traded_power, color=blue_ebc[0])
plt.xlabel('Month')
plt.ylabel('Power [kWh]')
plt.title('Total Traded Power Inside the District')
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Total_Traded_Power_Monthly.png")
plot_name_svg = os.path.join(plot_save_path, "Total_Traded_Power_Monthly.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 2: Monthly power import/export
power_from_grid_month = [power_from_grid_month_jan,
                         power_from_grid_month_apr if Apr_bh_month else 0,
                         power_from_grid_month_jul]
power_to_grid_month = [power_to_grid_month_jan,
                       power_to_grid_month_apr if Apr_bh_month else 0,
                       power_to_grid_month_jul]
plt.figure(figsize=(10, 5))
width = 0.35
x = range(len(months_full))
plt.bar(x, power_from_grid_month, width, label='Power from Grid', color=orange_ebc[0])
plt.bar([p + width for p in x], power_to_grid_month, width, label='Power to Grid', color=blue_ebc[0])
plt.xlabel('Month')
plt.ylabel('Power [kWh]')
plt.title('Monthly Power Import/Export')
plt.xticks([p + width / 2 for p in x], months_full)
plt.legend()
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Power_Import_Export_Monthly.png")
plot_name_svg = os.path.join(plot_save_path, "Power_Import_Export_Monthly.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 3: Monthly economic gain
economic_gain_month = [gain_month_jan,
                       gain_month_apr if Apr_bh_month else 0,
                       gain_month_jul]
plt.figure(figsize=(10, 6))
plt.bar(months_full, economic_gain_month, color=green_ebc[0])
plt.xlabel('Month')
plt.ylabel('Economic Gain [€]')
plt.title('Monthly Economic Gain [€]')
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "Economic_Gain_Monthly.png")
plot_name_svg = os.path.join(plot_save_path, "Economic_Gain_Monthly.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 4: Monthly SCF/DCF
scf_month = [scf_month_jan * 100,
             scf_month_apr * 100 if Apr_bh_month else 0,
             scf_month_jul * 100]
dcf_month = [dcf_month_jan * 100,
             dcf_month_apr * 100 if Apr_bh_month else 0,
             dcf_month_jul * 100]
plt.figure(figsize=(10, 6))
width = 0.35
x = range(len(months_full))
plt.bar(x, scf_month, width, label='SCF', color=blue_ebc[2])
plt.bar([p + width for p in x], dcf_month, width, label='DCF', color=red_ebc[2])
plt.xlabel('Month')
plt.ylabel('Factor [%]')
plt.title('Monthly SCF/DCF')
plt.xticks([p + width / 2 for p in x], months_full)
plt.legend()
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "SCF_DCF_Monthly.png")
plot_name_svg = os.path.join(plot_save_path, "SCF_DCF_Monthly.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()

# Plot 5: Monthly MSCF/MDCF
mscf_month = [mscf_month_jan * 100,
              mscf_month_apr * 100 if Apr_bh_month else 0,
              mscf_month_jul * 100]
mdcf_month = [mdcf_month_jan * 100,
              mdcf_month_apr * 100 if Apr_bh_month else 0,
              mdcf_month_jul * 100]
plt.figure(figsize=(10, 6))
width = 0.35
x = range(len(months_full))
plt.bar(x, mscf_month, width, label='MSCF', color=green_ebc[2])
plt.bar([p + width for p in x], mdcf_month, width, label='MDCF', color=black_ebc[2])
plt.xlabel('Month')
plt.ylabel('Factor [%]')
plt.title('Monthly MSCF/MDCF')
plt.xticks([p + width / 2 for p in x], months_full)
plt.legend()
plt.grid(True)
plot_name_png = os.path.join(plot_save_path, "MSCF_MDCF_Monthly.png")
plot_name_svg = os.path.join(plot_save_path, "MSCF_MDCF_Monthly.svg")
plt.savefig(plot_name_png)
plt.savefig(plot_name_svg)
plt.show()


