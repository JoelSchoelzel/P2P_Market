#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 10:21:16 2020

@author: Sarah Henn
"""

import scipy.io 
import numpy as np

def ev_load(options, number_cars = 400):

    path_file = options["path_file"]
    path_input = path_file + "/raw_inputs/demands_vorstadtnetz/"
    # load ev data
    ev_raw = scipy.io.loadmat(path_input + "/ev_profiles_400cars_11kW_residential.mat")

    # extract availability and on-demand profiles, extract tweeks example weeks
    ev = {}
    # todo: start and end of optimization
    ev["avail"] = ev_raw["EV_occurrence"][0:, 0:number_cars]
    ev["dem_arrive"] = ev_raw["EV_uncontrolled_charging_profile"][0:, 0:number_cars]
    
    ev["daily_dem"] = ev_raw["EV_daily_demand"][0:, 0:number_cars]

    # map demand to end of available phase (grid-ractive and bi-directional charging)
    index_leave = np.zeros([len(ev["avail"]), number_cars])
    # EVs are still available at t=0 but have been charged the evening before -> don't note first True entry
    for i in range(96,len(ev["avail"])-1):
        for n in range(number_cars):
            index_leave[i, n] = ev["avail"][i, n] > ev["avail"][i+1, n]
        # last charging phase of the year ends with t=T -> set last entry True
    index_leave[i+1,:] = True


    ev["dem_leave"] = np.zeros([len(ev["avail"]), number_cars])
    for n in range(number_cars):
        for i in range(1, len(ev["daily_dem"])):
            ev["dem_leave"][(96 * i):(96 * i + 96), n] = index_leave[(96 * i):(96 * i + 96), n] * ev["daily_dem"][i-1, n]
        ev["dem_leave"][len(ev["avail"])-1, n] = index_leave[len(ev["avail"])-1, n] * ev["daily_dem"][i, n]


    return ev


def ev_share(ev_share, nodes):
    if ev_share == 0.5 or ev_share == 0.25 or ev_share == 1:
        ev_avail = np.zeros(shape=(nodes,1))
        for n in range(nodes):
            k = 1 / ev_share
            if n % k == 0:
                ev_avail[n] = 1
            else:
                ev_avail[n] = 0

    elif ev_share == 0.75:
        ev_avail = np.ones(shape=(nodes,1))
        for n in range(nodes):
            k = 1 / (1 - ev_share)
            if n % k == 0:
                ev_avail[n] = 0
            else:
                ev_avail[n] = 1

    elif ev_share == 0:
        ev_avail = np.zeros(shape=(nodes,1))

    return ev_avail


if __name__ == "__main__":

    # Set options
    options = {"path_input":  "D:/git/ref_models/dgoc_central/optimization/input_data/dvgw_study/",
               "tweeks": 4}
    ev = ev_load(options)








