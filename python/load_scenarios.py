#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Sarah Henn
"""
import pandas as pd

def create_scenarios(options):

    # Define path for use case input data
    path_file = options["path_file"]
    path_input = path_file + "/raw_inputs/"

    if options["Dorfnetz"]:
        grid = "dorfnetz"
    else:
        grid = "vorstadtnetz"

    # Building parameters
    building_params = pd.read_csv(path_input + "buildings_" + grid + ".csv", delimiter=";")

    scenarios = pd.DataFrame(index=building_params.index)

    if options["Dorfnetz"]:
        sc_hp = [0,4,8,12,16,20,24,28,32,36,40,45]
        sc_chp = [0,1,2,3,4,5,6,7,8,9,10,11,12]
        for i in range(len(sc_hp) * len(sc_chp)):
            scenarios[i] = "gas"
        counter = 0
        for hp in sc_hp:
            for chp in sc_chp:
                scenarios[counter][0:hp] = "hp"
                scenarios[counter][hp:45] = "gas"
                scenarios[counter][45:45+chp] = "chp"
                scenarios[counter][45+chp:57] = "gas"
                counter += 1

    if not options["Dorfnetz"]:
        sc_hp = [0,10,20,30,40,50,60,70,80,90,100,110,116]
        sc_chp = [0,2,4,6,8,10,12,14,16,18,20,22,24,26,28]
        for i in range(len(sc_hp) * len(sc_chp)):
            scenarios[i] = "gas"
        counter = 0
        for hp in sc_hp:
            for chp in sc_chp:
                scenarios[counter][0:hp] = "hp"
                scenarios[counter][hp:116] = "gas"
                scenarios[counter][116:116+chp] = "chp"
                scenarios[counter][116+chp:144] = "gas"
                counter += 1

    scenarios.to_csv(path_input + "scenarios_" + grid + ".csv", sep=";", index=False)

    return scenarios

def get_scenarios(options):

    # Define path for use case input data
    path_file = options["path_file"]
    path_input = path_file + "/raw_inputs/"

    if options["Dorfnetz"]:
        grid = "dorfnetz"
    else:
        grid = "vorstadtnetz"

    scns = pd.read_csv(path_input + "scenarios_" + grid + ".csv",delimiter=";")

    return scns

if __name__ == "__main__":

    # Set options
    options = {"Dorfnetz": True,
               "path_input": "D:/git/ref_models/dgoc_central/optimization/input_data/dvgw_study/",
               "path_results": "D:/git/ref_models/dgoc_central/optimization/results/"}

    scenarios = create_scenarios(options)