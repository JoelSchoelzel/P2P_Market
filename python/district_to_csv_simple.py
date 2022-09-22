import random
import pandas as pd
import numpy as np


if __name__ == '__main__':

    options_district = {"nb_buildings": 20, # number of buildings in district
                        "shares_building_types": [0, 0, 100], # SFH, MFH, TH ; sum has to be 100
                        # e.g. 60 for SFH: share of single family houses in district is 60%
                        "construction_period": "01", # construction period 03: 1969-78, 02: 1984-94, 01: 2002-09
                        "rf_L1": 4, # e.g. 4: every fourth building with tabula retrofit level 1

                        "HP": [4, 4, 4], # SFH, MFH, TH
                        # e.g. 3 for SFH/MFH/TH: every third SFH/MFH/TH with heat pump, rest is boiler

                        "EV": [3, 3, 3], # SFH, MFH, TH
                        # e.g. 3 for SFH/TH: every third SFH/TH with one EV
                        # e.g. 3 for MFH: every third MFH-APARTMENT with one EV
                        "f_EV": ["L", "S", "M"], # SFH, MFH, TH
                        # EV battery capacity: S, M or L

                        "PV": [3, 3, 3], # SFH, MFH, TH
                        # e.g. 3 for SFH/MFH/TH: every third SFH/MFH/TH with PV system
                        "f_PV": [0.6, 0.7, 0.5], # SFH, MFH, TH ; area_PV = f_PV * area_roof
                        "gamma_PV": [10, 0, -10], # SFH, MFH, TH [degree]
                        # -180 <= gamma_PV <= 180, with zero due south, east negative and west positive

                        "STC": [5, 5, 5], # SFH, MFH, TH
                        # e.g. 3 for SFH/MFH/TH: every third SFH/MFH/TH with solar thermal collector
                        "f_STC": [0.15, 0.2, 0.1], # SFH, MFH, TH
                        # area_STC = f_STC * area_roof

                        "BAT": [2, 3, 2], # SFH, MFH, TH
                        # e.g. 2 for SFH: every second SFH with PV system gets battery system
                        "f_BAT": [0.8, 1.0, 0.8], # SFH, MFH, TH ; Wh battery / Wp PV

                        "f_TES": [35, 40, 35], # SFH, MFH, TH
                        # thermal energy storage: l storage volume / kW heater

                        "BZ": [0, 0, 0], # SFH, MFH, TH
                        # e.g. 3 for SFH/TH: every third SFH/TH with boiler is extended with a Sunfire fuel cell
                        # e.g. 3 for MFH: every third MFH-APARTMENT adds one SF fuel cell to the building's heating system

                        "path_save_csv": "C:/Users/Arbeit/Documents/WiHi_EBC/districtgenerator_python/data/scenarios/",
                        }

    if sum(options_district["shares_building_types"]) != 100:
        raise ValueError("Shares of buildings types do not sum up to 100 (%).")

    # building id and type
    nb_SFH = int(options_district["nb_buildings"] * options_district["shares_building_types"][0]/100)
    nb_MFH = int(options_district["nb_buildings"] * options_district["shares_building_types"][1]/100)
    nb_TH = int(options_district["nb_buildings"] * options_district["shares_building_types"][2]/100)

    IDs = {} # store building IDs for e.g. all SFHs, all MFHs with PV, all THs with boiler etc.
    IDs["all_buildings"] = []
    IDs["SFH"] = []
    IDs["MFH"] = []
    IDs["TH"] = []

    building_type = [] # SFH, MFH or TH
    for n in range(options_district["nb_buildings"]):
        IDs["all_buildings"].append(n)
        if n < nb_SFH:
            building_type.append("SFH")
            IDs["SFH"].append(n)
        elif n < (nb_SFH + nb_MFH):
            building_type.append("MFH")
            IDs["MFH"].append(n)
        else:
            building_type.append("TH")
            IDs["TH"].append(n)

    # year of construction
    year = []

    construction_period = {}
    construction_period["01"] = dict(year_start=2002, year_end=2009)
    construction_period["02"] = dict(year_start=1984, year_end=1994)
    construction_period["03"] = dict(year_start=1969, year_end=1978)

    if nb_SFH == 1:
        year.append(int(0.5*(construction_period[options_district["construction_period"]]["year_start"] +
                        construction_period[options_district["construction_period"]]["year_end"])))
    if nb_SFH > 1:
        for n in range(nb_SFH):
            year.append(int(construction_period[options_district["construction_period"]]["year_start"] +
                            n*(construction_period[options_district["construction_period"]]["year_end"] -
                                 construction_period[options_district["construction_period"]]["year_start"])/
                                ((nb_SFH)-1)))

    if nb_MFH == 1:
        year.append(int(0.5*(construction_period[options_district["construction_period"]]["year_start"] +
                        construction_period[options_district["construction_period"]]["year_end"])))
    if nb_MFH > 1:
        for n in range(nb_MFH):
            year.append(int(construction_period[options_district["construction_period"]]["year_start"] +
                            n * (construction_period[options_district["construction_period"]]["year_end"] -
                              construction_period[options_district["construction_period"]]["year_start"])
                            /(nb_MFH-1)))

    if nb_TH == 1:
        year.append(int(0.5*(construction_period[options_district["construction_period"]]["year_start"] +
                        construction_period[options_district["construction_period"]]["year_end"])))
    if nb_TH > 1:
        for n in range(nb_TH):
            year.append(int(construction_period[options_district["construction_period"]]["year_start"] +
                            n * (construction_period[options_district["construction_period"]]["year_end"] -
                              construction_period[options_district["construction_period"]]["year_start"])
                            /(nb_TH-1)))

    # retrofit level 1
    retrofit = np.zeros(options_district["nb_buildings"], dtype=int)

    if options_district["rf_L1"] > 0:
        for n in range(options_district["nb_buildings"]):
            if n % options_district["rf_L1"] == 0:
                retrofit[n] = 1

    # area according to tabula data
    area_tab = {}
    area_tab["0"] = dict(start=1969, end=1978, A_SFH=155, A_MFH=410, A_TH=129) # area in m²
    area_tab["1"] = dict(start=1984, end=1994, A_SFH=153, A_MFH=430, A_TH=130)
    area_tab["2"] = dict(start=2002, end=2009, A_SFH=154, A_MFH=459, A_TH=135)

    area = np.zeros(options_district["nb_buildings"], dtype=int)
    for n in range(options_district["nb_buildings"]):
        for i in range(area_tab.__len__()):
            if year[n] >= area_tab[str(i)]["start"] and year[n] <= area_tab[str(i)]["end"]:
                if building_type[n] == "SFH":
                    area[n] = area_tab[str(i)]["A_SFH"]
                elif building_type[n] == "MFH":
                    area[n] = area_tab[str(i)]["A_MFH"]
                elif building_type[n] == "TH":
                    area[n] = area_tab[str(i)]["A_TH"]

    # heating device
    IDs["BOI_SFH"] = []
    IDs["BOI_MFH"] = []
    IDs["BOI_TH"] = []

    heater = ["---" for n in range(options_district["nb_buildings"])]

    for n in range(IDs["SFH"].__len__()):
        if (options_district["HP"][0] > 0) and (n % options_district["HP"][0] == 0):
            heater[IDs["SFH"][n]] = "HP"
        else:
            heater[IDs["SFH"][n]] = "BOI"
            IDs["BOI_SFH"].append(IDs["SFH"][n])
    for n in range(IDs["MFH"].__len__()):
        if (options_district["HP"][1] > 0) and (n % options_district["HP"][1] == 0):
            heater[IDs["MFH"][n]] = "HP"
        else:
            heater[IDs["MFH"][n]] = "BOI"
            IDs["BOI_MFH"].append(IDs["MFH"][n])
    for n in range(IDs["TH"].__len__()):
        if (options_district["HP"][2] > 0) and (n % options_district["HP"][2] == 0):
            heater[IDs["TH"][n]] = "HP"
        else:
            heater[IDs["TH"][n]] = "BOI"
            IDs["BOI_TH"].append(IDs["TH"][n])

    # electric vehicles (share_EV relates to flats)
    nb_flats = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in range(options_district["nb_buildings"]):
        if building_type[n] == "SFH":
            nb_flats[n] = 1
        elif building_type[n] == "MFH": # according to districtgenerator
            if area[n] <= 720:
                nb_flats[n] = 6
            elif area[n] > 960:
                nb_flats[n] = 10
            else:
                nb_flats[n] = 8
        elif building_type[n] == "TH":
            nb_flats[n] = 1

    ev = np.zeros(options_district["nb_buildings"], dtype=int)
    f_ev = ["0" for n in range(options_district["nb_buildings"])]

    if options_district["EV"][0] > 0:
        for n in range(IDs["SFH"].__len__()):
            if n % options_district["EV"][0] == 0:
                ev[IDs["SFH"][n]] = 1
                f_ev[IDs["SFH"][n]] = options_district["f_EV"][0]
    if options_district["EV"][1] > 0:
        for n in range(IDs["MFH"].__len__()):
            ev[IDs["MFH"][n]] = round(nb_flats[IDs["MFH"][n]] / options_district["EV"][1], 0)
            f_ev[IDs["MFH"][n]] = options_district["f_EV"][1]
    if options_district["EV"][2] > 0:
        for n in range(IDs["TH"].__len__()):
            if n % options_district["EV"][2] == 0:
                ev[IDs["TH"][n]] = 1
                f_ev[IDs["TH"][n]] = options_district["f_EV"][2]

    # PV
    IDs["PV_SFH"] = []
    IDs["PV_MFH"] = []
    IDs["PV_TH"] = []

    pv = np.zeros(options_district["nb_buildings"], dtype=int)
    f_pv = np.zeros(options_district["nb_buildings"])
    gamma_pv = np.zeros(options_district["nb_buildings"], dtype=int)

    if options_district["PV"][0] > 0:
        for n in range(IDs["SFH"].__len__()):
            if n % options_district["PV"][0] == 0:
                pv[IDs["SFH"][n]] = 1
                f_pv[IDs["SFH"][n]] = options_district["f_PV"][0]
                gamma_pv[IDs["SFH"][n]] = options_district["gamma_PV"][0]
                IDs["PV_SFH"].append(IDs["SFH"][n])
    if options_district["PV"][1] > 0:
        for n in range(IDs["MFH"].__len__()):
            if n % options_district["PV"][1] == 0:
                pv[IDs["MFH"][n]] = 1
                f_pv[IDs["MFH"][n]] = options_district["f_PV"][1]
                gamma_pv[IDs["MFH"][n]] = options_district["gamma_PV"][1]
                IDs["PV_MFH"].append(IDs["MFH"][n])
    if options_district["PV"][2] > 0:
        for n in range(IDs["TH"].__len__()):
            if n % options_district["PV"][2] == 0:
                pv[IDs["TH"][n]] = 1
                f_pv[IDs["TH"][n]] = options_district["f_PV"][2]
                gamma_pv[IDs["TH"][n]] = options_district["gamma_PV"][2]
                IDs["PV_TH"].append(IDs["TH"][n])

    # STC
    stc = np.zeros(options_district["nb_buildings"], dtype=int)
    f_stc = np.zeros(options_district["nb_buildings"])

    if options_district["STC"][0] > 0:
        for n in range(IDs["SFH"].__len__()):
            if n % options_district["STC"][0] == 0:
                stc[IDs["SFH"][n]] = 1
                f_stc[IDs["SFH"][n]] = options_district["f_STC"][0]
    if options_district["STC"][1] > 0:
        for n in range(IDs["MFH"].__len__()):
            if n % options_district["STC"][1] == 0:
                stc[IDs["MFH"][n]] = 1
                f_stc[IDs["MFH"][n]] = options_district["f_STC"][1]
    if options_district["STC"][2] > 0:
        for n in range(IDs["TH"].__len__()):
            if n % options_district["STC"][2] == 0:
                stc[IDs["TH"][n]] = 1
                f_stc[IDs["TH"][n]] = options_district["f_STC"][2]

    # BAT
    bat = np.zeros(options_district["nb_buildings"], dtype=int)
    f_bat = np.zeros(options_district["nb_buildings"])

    if options_district["BAT"][0] > 0:
        for n in IDs["PV_SFH"][::options_district["BAT"][0]]:
            bat[n] = 1
            f_bat[n] = options_district["f_BAT"][0]
    if options_district["BAT"][1] > 0:
        for n in IDs["PV_MFH"][::options_district["BAT"][1]]:
            bat[n] = 1
            f_bat[n] = options_district["f_BAT"][1]
    if options_district["BAT"][2] > 0:
        for n in IDs["PV_TH"][::options_district["BAT"][2]]:
            bat[n] = 1
            f_bat[n] = options_district["f_BAT"][2]

    # TES
    f_tes = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in IDs["SFH"]:
        f_tes[n] = options_district["f_TES"][0]
    for n in IDs["MFH"]:
        f_tes[n] = options_district["f_TES"][1]
    for n in IDs["TH"]:
        f_tes[n] = options_district["f_TES"][2]

    # Sunfire BZ
    bz = np.zeros(options_district["nb_buildings"], dtype=int)

    if options_district["BZ"][0] > 0:
        for n in range(IDs["BOI_SFH"].__len__()):
            if n % options_district["BZ"][0] == 0:
                bz[IDs["BOI_SFH"][n]] = 1
    if options_district["BZ"][1] > 0:
        for n in range(IDs["BOI_MFH"].__len__()):
            bz[IDs["BOI_MFH"][n]] = round(nb_flats[IDs["BOI_MFH"][n]] / options_district["BZ"][1], 0)
    if options_district["BZ"][2] > 0:
        for n in range(IDs["BOI_TH"].__len__()):
            if n % options_district["BZ"][2] == 0:
                bz[IDs["BOI_TH"][n]] = 1

    # create dataframe
    df = {'id': IDs["all_buildings"], 'building': building_type, 'year': year, 'retrofit': retrofit, 'area': area, 'heater': heater, 'PV': pv,
          'STC': stc, 'EV': ev, 'BAT': bat, 'f_TES': f_tes, 'f_BAT': f_bat, 'f_EV': f_ev, 'f_PV': f_pv, 'f_STC': f_stc, 'gamma_PV': gamma_pv, 'Sunfire_BZ': bz}

    distr = pd.DataFrame(data=df)

    # save dataframe to csv file
    distr.to_csv(options_district["path_save_csv"] + "District_CP" + options_district["construction_period"] + "_SFH" + str(int(options_district["shares_building_types"][0])) +
                 "_MFH" + str(int(options_district["shares_building_types"][1])) + "_TH" + str(int(options_district["shares_building_types"][2])) +
                 "_BZ" + str(int(options_district["BZ"][0])) + "-" + str(int(options_district["BZ"][1])) + "-" + str(int(options_district["BZ"][2])) + ".csv", index=False)
