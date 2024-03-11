import python.parse_inputs as parse_inputs
import python.load_net as net
import python.opti_bes as decentral_opti

#import data.time_data as time_data
from classes import Datahandler

# Set options for DistrictGenerator
options_DG = {
    "scenario_name": "ma_zehao",  # name of csv input file
}
# "scenario_test" for 4 buildings
# D:\jdu-zwu\P2P_Market\results\criteria_P2P_scenario_test

# create district with load (elec, heat, ..) and generation (pv, bz ..)  profiles as input for MAScity
# districtData = DistrictGenerator.run_districtgenerator(options_DG)
# print("Finished district generation (" + str(datetime.datetime.now()) + ").")

# DistrictGenerator
data = Datahandler()
data.generateDistrictComplete(options_DG["scenario_name"], calcUserProfiles=False,
                              saveUserProfiles=True)  # (calcUserProfiles=False, saveUserProfiles=True)
data.designDevices(saveGenerationProfiles=True)
# data.clusterProfiles()

districtData = data

# Set options for MAScity
options = {"optimization": "P2P",  # P2P, P2P_typeWeeks, central, central_typeWeeks, decentral or decentral_typeWeeks
           "bid_strategy": "zero",  # zero for zero-intelligence
           "crit_prio": "price",  # criteria to assign priority for trading: price, alpha_el_flex_delayed
           "descending": True,  # True: highest value of chosen has highest priority, False: lowest
           "multi_round": True,  # True: multiple trading rounds, False: single trading round
           "trading_rounds": 0,  # Number of trading rounds for multi round trading, 0 for unlimited
           "number_typeWeeks": 0,  # set 0 in case no type weeks are investigated
           # "full_path_scenario": "C:\\Users\\miche\\districtgenerator_python\\data\\scenarios\\scenario4.csv", # scenario csv
           "full_path_scenario": ("D:\\jdu-zwu\\districtgenerator_python\\data\\scenarios\\" + options_DG[
               "scenario_name"] + ".csv"),  # scenario csv, name set for DG is used
           # "times": 2688, #8760 * 4,  # whole year 15min resolution
           # "tweeks": 4,  # number of typical weeks
           "Dorfnetz": False,  # grid type # todo: aktuell klappt nur Vorstadtnetz, da bei Dorfnetz noch 1 Gebäude fehlt
           "neighborhood": "district01",  # name of neighborhood
           # "pv_share": 0.5,  # 0.25, 0.5, 0.75, 1.0
           "ev_share": 0.0,  # 0.25, 0.5, 0.75, 1.0
           "ev_public": True,  # Skript für Opti von öffentlichen Ladestationen
           "grid": False,  # True -> consider grid constraints, False -> dont
           # "dt": 0.25,  # dt in h for rolling horizon
           "discretization_input_data": districtData.time['timeResolution'] / 3600,  # in h - for: elec, dhw and heat
           "path_file": "D:/jdu-zwu/P2P_Market",  # "C:/Users/Arbeit/Documents/WiHi_EBC/MAScity/MAScity",
           "path_results": "D:/jdu-zwu/P2P_Market/results",  # "C:/Users/Arbeit/Documents/WiHi_EBC/MAScity/results",
           "time_zone": districtData.site['timeZone'],  # ---,      time zone
           "location": districtData.site['location'],  # degree,   latitude, longitude of location
           "altitude": districtData.site['altitude'],  # m,        height of location above sea level
           }


# Set rolling horizon options
par_rh = {
    # Parameters for operational optimization
    "n_hours": 36,  # ----,      number of hours of prediction horizon for rolling horizon
    "n_hours_ov": 35,  # ----,      number of hours of overlap horizon for rolling horizon
    "n_opt_max": 8760,  # 8760  # -----,       maximum number of optimizations
    "month": 12,  # -----,     optimize this month 1-12 (1: Jan, 2: Feb, ...), set to 0 to optimize entire year
    # set month to 0 for clustered input data

    # Parameters for rolling horizon with aggregated foresight
    "n_blocks": 2,  # ----, number of blocks with different resolution: minimum 2 (control horizon and overlap horizon)
    # "resolution": [0.25, 1],  # h,    time resolution of each resolution block, insert list
    "resolution": [1, 1],  # h,    time resolution of each resolution block, insert list
    # [0.25, 1] resembles: control horizon with 15min, overlap horizon with 1h discretization
    "overlap_block_duration": [0, 0], }  # h, duration of overlap time blocks, insert 0 for default: half of overlap horizon

def get_inputs(par_rh, options, districtData):
    ### Load Params
    # load rolling horizon parameters
    par_rh = parse_inputs.compute_pars_rh(par_rh, options, districtData)

    # Read economic parameters and
    # parameters for opti/gurobi
    params = parse_inputs.read_economics()

    # Load weather parameters
    #weather = pd.read_csv(options["path_file"] + "/raw_inputs/weather_potsdam.csv")  # DWD weather data for potsdam
    #nodes, solar_irr, weather = parse_inputs.get_solar_irr(options, weather, par_rh)

    # Read demands (elec, heat, dhw, ev) and pv generation
    nodes, building_params, options = parse_inputs.read_demands(options, districtData, par_rh)
    # Read devices, economic date and other parameters
    nodes, devs, building_params = parse_inputs.map_devices(options, nodes, building_params, par_rh, districtData)

    #nodes, building_params = parse_inputs.get_pv_power(nodes, options, building_params, devs, solar_irr, par_rh)
    #nodes, building_params = parse_inputs.get_pv_power_from_DG(nodes, options, building_params, districtData)


    # Read technical data of the network
    net_data = net.create_net(options)

    return nodes, building_params, params, devs, net_data, par_rh


def decentral_operation(node, params, pars_rh, building_params, init_val, n_opt, options):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_res = decentral_opti.compute(node, params, pars_rh, building_params, init_val, n_opt, options)

    return opti_res

def init_val_decentral_operation(opti_bes, par_rh, n_opt):

    init_val = decentral_opti.compute_initial_values(opti_bes, par_rh, n_opt)

    return init_val






