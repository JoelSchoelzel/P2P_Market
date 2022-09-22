import random
import pandas as pd
import numpy as np


if __name__ == '__main__':
    # todo: add f_EV
    options_district = {"nb_buildings": 20, # number of buildings in district
                        "share_SFH": 0.4, # e.g. 0.60; share of SFHs in district, rest is MFH
                        "construction_period": "02", # construction period 03: 1950+, 02: 1970+, 01: 1990+ (Zensus 2011)
                        "share_rf_L1": 0.2, # e.g. 0.25: every fourth building with tabula retrofit level 1
                        "share_HP": 0.2837, # share of heat pumps/building, rest is boiler
                        "probability_hp_rf_L1": 3, # e.g. 3: probability a building with retrofit L1 is heated with HP
                                    # is 3x probability building without retrofit is heated with HP
                        "share_EV": 0.36, # EV/flat
                        "probability_EV_SFH": 2, # e.g. 2: probability for EV/flat in SFH is twice as high as
                                    # probability for EV/flat in MFH
                        "share_PV": 0.2,
                        "probability_pv_hp": 2, # e.g. 2: probability a building with HP features PV
                                    # is 2x probability building without HP features PV
                        "f_PV": [0.40, 0.80], # range; area_PV = f_PV * area_roof
                        "share_STC": 0.1,
                        "f_STC": [0.10, 0.20], # range; area_STC = f_STC * area_roof
                        "share_BAT_PV": 0.5, # e.g. 0.5: 50% of PV systems include BAT
                        "f_BAT": [0.7, 1], # range; Wh battery / Wp PV
                        "f_TES": [35, 50], # range; l storage volume / kW heater
                        "share_bz_sf_SFH": 0.5, # Sunfire BZ/SFH
                        "share_bz_sf_MFH": 0.5, # Sunfire BZ/flat
                                    # e.g. 0.25: every fourth flat that is heated with boiler gets SF BZ in addition
                        "gamma_PV": [-45, 45], # range; -180 <= gamma <= 180, with zero due south, east negative and west positive.
                        "path_save_csv": "C:/Users/Arbeit/Documents/WiHi_EBC/districtgenerator_python/data/scenarios/",

                        }

    # building id and type
    building_id = np.zeros(options_district["nb_buildings"], dtype=int)
    building_type = [] # SFH or MFH
    for n in range(options_district["nb_buildings"]):
        building_id[n] = n
        if n < (options_district["nb_buildings"] * options_district["share_SFH"]):
            building_type.append("SFH")
        else:
            building_type.append("MFH")

    # year of construction
    year = []
    nb_SFH = int(options_district["nb_buildings"] * options_district["share_SFH"])
    nb_MFH = int(options_district["nb_buildings"] - nb_SFH)

    construction_period = {}
    construction_period["01"] = dict(year_start=1990, year_end=2015)
    construction_period["02"] = dict(year_start=1970, year_end=1989)
    construction_period["03"] = dict(year_start=1950, year_end=1969)

    if nb_SFH == 1:
        year.append(int(0.5*(construction_period[options_district["construction_period"]]["year_start"] +
                        construction_period[options_district["construction_period"]]["year_end"])))

    if nb_SFH > 1:
        for n1 in range(nb_SFH):
            year.append(int(construction_period[options_district["construction_period"]]["year_start"] +
                            n1*(construction_period[options_district["construction_period"]]["year_end"] -
                                 construction_period[options_district["construction_period"]]["year_start"])/
                                ((nb_SFH)-1)))

    if nb_MFH == 1:
        year.append(int(0.5*(construction_period[options_district["construction_period"]]["year_start"] +
                        construction_period[options_district["construction_period"]]["year_end"])))

    if nb_MFH > 1:
        for n2 in range(nb_MFH):
            year.append(int(construction_period[options_district["construction_period"]]["year_start"] +
                            n2 * (construction_period[options_district["construction_period"]]["year_end"] -
                              construction_period[options_district["construction_period"]]["year_start"])
                            /(nb_MFH-1)))

    # retrofit level 1 # todo: older buildings more likely to get retrofit
    nb_buildings_rf_L1 = int(options_district["nb_buildings"] * options_district["share_rf_L1"])
    buildings_rf_L1 = random.sample(list(building_id), k=nb_buildings_rf_L1)
    retrofit = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in buildings_rf_L1:
            retrofit[n] = 1

    # area according to tabula data
    area_tab = {}
    area_tab["0"] = dict(start=1949, end=1957, A_SFH=111, A_MFH=632) # year, year, area, area [m²]
    area_tab["1"] = dict(start=1958, end=1968, A_SFH=121, A_MFH=3129)
    area_tab["2"] = dict(start=1969, end=1978, A_SFH=173, A_MFH=469)
    area_tab["3"] = dict(start=1979, end=1983, A_SFH=216, A_MFH=654)
    area_tab["4"] = dict(start=1984, end=1994, A_SFH=150, A_MFH=778)
    area_tab["5"] = dict(start=1995, end=2001, A_SFH=122, A_MFH=835)
    area_tab["6"] = dict(start=2002, end=2009, A_SFH=147, A_MFH=2190)
    area_tab["7"] = dict(start=2010, end=2015, A_SFH=187, A_MFH=1305)

    area = np.zeros(options_district["nb_buildings"], dtype=int)
    for n in range(options_district["nb_buildings"]):
        for i in range(area_tab.__len__()):
            if year[n] >= area_tab[str(i)]["start"] and year[n] <= area_tab[str(i)]["end"]:
                if building_type[n] == "SFH":
                    area[n] = area_tab[str(i)]["A_SFH"]
                elif building_type[n] == "MFH":
                    area[n] = area_tab[str(i)]["A_MFH"]

    # heating device
    nb_buildings_hp = int(options_district["nb_buildings"] * options_district["share_HP"])
    weights_hp_rf = np.ones(options_district["nb_buildings"])

    # raise probability buildings with retrofit are heated with heat pump
    for n in buildings_rf_L1:
        weights_hp_rf[n] = options_district["probability_hp_rf_L1"]

    weights_hp_rf = weights_hp_rf / weights_hp_rf.sum() # normalize to sum 1

    buildings_hp = np.random.choice(building_id, size=nb_buildings_hp,replace=False, p=weights_hp_rf)
    #buildings_hp = random.sample(building_id, wei k=nb_buildings_hp) # same probabilities
    heater = []

    for n in range(options_district["nb_buildings"]):
        if n in buildings_hp:
            heater.append("HP")
        else:
            heater.append("BOI")

    # electric vehicles (share_EV relates to flats)
    nb_flats = np.zeros(options_district["nb_buildings"], dtype=int)
    weights_ev_building = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in range(options_district["nb_buildings"]):
        if building_type[n] == "SFH":
            nb_flats[n] = 1
            weights_ev_building[n] = nb_flats[n] * options_district["probability_EV_SFH"]
        elif building_type[n] == "MFH": # according to districtgenerator
            if area[n] <= 720:
                nb_flats[n] = 6
                weights_ev_building[n] = nb_flats[n]
            elif area[n] > 960:
                nb_flats[n] = 10
                weights_ev_building[n] = nb_flats[n]
            else:
                nb_flats[n] = 8
                weights_ev_building[n] = nb_flats[n]

    nb_evs = int(nb_flats.sum() * options_district["share_EV"]) # total number EVs in district
    # probability of EVs in building correlates with number of flats in building
    weights_ev_building = weights_ev_building/weights_ev_building.sum() # normalize to sum 1

    buildings_ev = np.random.choice(building_id, size=nb_evs,replace=True, p=weights_ev_building)
    ev = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in buildings_ev:
        ev[n] +=1

    # PV
    nb_buildings_pv = int(options_district["nb_buildings"] * options_district["share_PV"])
    weights_pv_hp = np.ones(options_district["nb_buildings"])

    # raise probability buildings with heat pump feature PV
    for n in buildings_hp:
        weights_pv_hp[n] = options_district["probability_pv_hp"]

    weights_pv_hp = weights_pv_hp / weights_pv_hp.sum() # normalize to sum 1
    buildings_pv = np.random.choice(building_id, size=nb_buildings_pv,replace=False, p=weights_pv_hp)
    pv = np.zeros(options_district["nb_buildings"], dtype=int)
    f_PV = np.zeros(options_district["nb_buildings"])
    gamma_PV = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in buildings_pv:
        pv[n] = 1
        f_PV[n] = round(random.uniform(options_district["f_PV"][0], options_district["f_PV"][1]), 2)
        gamma_PV[n] = random.randint(options_district["gamma_PV"][0], options_district["gamma_PV"][1])

    # STC
    nb_buildings_stc = int(options_district["nb_buildings"] * options_district["share_STC"])
    buildings_stc = random.sample(list(building_id), k=nb_buildings_stc)
    stc = np.zeros(options_district["nb_buildings"], dtype=int)
    f_stc = np.zeros(options_district["nb_buildings"])

    for n in buildings_stc:
        stc[n] = 1
        f_stc[n] = round(random.uniform(options_district["f_STC"][0], options_district["f_STC"][1]), 2)

    # BAT
    nb_buildings_bat = int(options_district["share_BAT_PV"] * nb_buildings_pv)
    buildings_bat = random.sample(list(buildings_pv), k=nb_buildings_bat)
    bat = np.zeros(options_district["nb_buildings"], dtype=int)
    f_bat = np.zeros(options_district["nb_buildings"])

    for n in buildings_bat:
        bat[n] = 1
        f_bat[n] = round(random.uniform(options_district["f_BAT"][0], options_district["f_BAT"][1]), 2)


    # TES
    f_tes = np.zeros(options_district["nb_buildings"], dtype=int)

    for n in range(options_district["nb_buildings"]):
        f_tes[n] = random.randint(options_district["f_TES"][0], options_district["f_TES"][1])

    # Sunfire BZ
    bz = np.zeros(options_district["nb_buildings"], dtype=int)
    buildings_boi_sfh = [] # building ids of SFHs with boiler
    buildings_boi_mfh = []
    buildings_boi_mfh_flats = [] # number of flats for MFHs with boiler

    for n in range(options_district["nb_buildings"]):
        if building_type[n] == "SFH" and heater[n] == "BOI":
            buildings_boi_sfh.append(n)
        elif building_type[n] == "MFH" and heater[n] == "BOI":
            buildings_boi_mfh.append(n)
            buildings_boi_mfh_flats.append(nb_flats[n])

    nb_sf_bz_sfh = int(buildings_boi_sfh.__len__() * options_district["share_bz_sf_SFH"])
    buildings_bz_sfh = random.sample(list(buildings_boi_sfh), k=nb_sf_bz_sfh)

    nb_sf_bz_mfh = int(sum(buildings_boi_mfh_flats) * options_district["share_bz_sf_MFH"])
    if nb_sf_bz_mfh > 0:
        weights_sf_bz_mfh = buildings_boi_mfh_flats/sum(buildings_boi_mfh_flats)
        buildings_bz_mfh = np.random.choice(buildings_boi_mfh, size=nb_sf_bz_mfh,replace=True, p=weights_sf_bz_mfh)

        for n in buildings_bz_mfh:
            bz[n] +=1

    for n in buildings_bz_sfh:
        bz[n] = 1

    # create dataframe
    df = {'id':building_id, 'building':building_type, 'year':year, 'retrofit':retrofit, 'area':area, 'heater': heater, 'PV': pv,
          'STC': stc, 'EV': ev, 'BAT': bat, 'f_TES': f_tes, 'f_BAT': f_bat, 'f_PV': f_PV, 'f_STC': f_stc, 'gamma_PV': gamma_PV, 'Sunfire_BZ': bz}
    distr = pd.DataFrame(data=df)

    # save dataframe to csv file
    distr.to_csv(options_district["path_save_csv"] + "District_CP" + options_district["construction_period"] + "_SFH" + str(int(options_district["share_SFH"]*100)) +
                 "_BZ" + str(int(options_district["share_bz_sf_SFH"]*100)) + "-" + str(int(options_district["share_bz_sf_MFH"]*100)) + ".csv", index=False)
