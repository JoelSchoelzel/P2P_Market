#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import numpy as np
import python.opti_bes as decentral_opti
import python.opti_city as central_opti

def rolling_horizon_opti(options, nodes, par_rh, building_params, params):
    # Run rolling horizon
    init_val = {}  # not needed for first optimization, thus empty dictionary
    opti_res = {}  # to store the results of the bes optimization
    if options["optimization"] == "decentral":
        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            if n_opt == 0:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" +str(n) + ".")
                    init_val[n_opt]["building_" + str(n)] = {}
                    opti_res[n_opt][n] = decentral_operation(nodes[n],params, par_rh,
                                                              building_params.iloc[n],
                                                              init_val[n_opt]["building_" + str(n)], n_opt)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n],
                                                                                         par_rh, n_opt)
            else:
                for n in range(options["nb_bes"]):
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(n) + ".")
                    opti_res[n_opt][n] = decentral_operation(nodes[n], params, par_rh,
                                                              building_params.iloc[n],
                                                              init_val[n_opt]["building_" + str(n)], n_opt)
                    init_val[n_opt + 1]["building_" + str(n)] = init_val_decentral_operation(opti_res[n_opt][n], par_rh, n_opt)
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) + "% of optimizations processed.")
        return opti_res

    elif options["optimization"] == "central":
        # Start optimizations
        for n_opt in range(par_rh["n_opt"]):
            opti_res[n_opt] = {}
            init_val[0] = {}
            init_val[n_opt+1] = {}
            if n_opt == 0:
                print("Starting optimization: n_opt: " + str(n_opt) + ".")
                init_val[n_opt] = {}
                opti_res[n_opt] = central_operation(nodes,params, par_rh, building_params,
                                                      init_val[n_opt], n_opt, options)
                init_val[n_opt + 1] = init_val_central_operation(opti_res[n_opt], nodes, par_rh, n_opt)
            else:
                print("Starting optimization: n_opt: " + str(n_opt) + ".")
                opti_res[n_opt] = central_operation(nodes, params, par_rh, building_params,
                                                      init_val[n_opt], n_opt, options)
                init_val[n_opt + 1] = init_val_central_operation(opti_res[n_opt], nodes, par_rh, n_opt)
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_opt"] * 100) + "% of optimizations processed.")
        return opti_res

    elif options["optimization"] == "central_typeWeeks":
        # Start optimizations
        typeweek_recalc = []     # log all typeweeks that had to be recalculated

        index = list(range(options["number_typeWeeks"]))
        for k in index:
            print(index)
            init_val[k] = {}
            opti_res[k] = {}
            for n_opt in range(par_rh["n_opt"]):

                opti_res[k][n_opt] = {}
                init_val[k][0] = {}
                init_val[k][n_opt+1] = {}
                if n_opt == 0:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    init_val[k][n_opt] = {}
                    opti_res[k][n_opt], IISconstr = central_operation(nodes[k],params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)

                    if opti_res[k][n_opt][26] == 'infeasible':
                        nodes, index = infeasible_model_adjust_fuel_cell_configuration(k, nodes, options, index, IISconstr)
                        typeweek_recalc.append(k)
                        break
                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                else:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    opti_res[k][n_opt], IISconstr = central_operation(nodes[k], params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)

                    if opti_res[k][n_opt][26] == 'infeasible':
                        nodes, index = infeasible_model_adjust_fuel_cell_configuration(k, nodes, options, index, IISconstr)
                        typeweek_recalc.append(k)
                        break
                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                print("Finished optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ". " + str((par_rh["n_opt"]*k + n_opt+1) / (par_rh["n_opt"]* options["number_typeWeeks"]) * 100) + "% of optimizations processed.")
        return opti_res, typeweek_recalc, index

def infeasible_model_adjust_fuel_cell_configuration(k, nodes, options, index_typeweeks, IISconstr):
    '''
    # deactivate Sunfire FC for typeweek with infeasible model
    infeasibleBES = []
    concernedBuildingTypes = []
    for i, elem in enumerate(IISconstr):
        if 'min_heat_bz_sf' in elem:
            if not int(elem.partition("bes")[2]) in infeasibleBES:
                infeasibleBES.append(int(elem.partition("bes")[2]))

    if infeasibleBES.__len__() == 0:
        raise ValueError("Error ist probably not caused by Sunfire fuel cell. Further investigation with debugger necessarry.")

    for j in infeasibleBES:
        if not nodes[k][j]["type"] in concernedBuildingTypes:
            concernedBuildingTypes.append(nodes[k][j]["type"])

    for n in range(options["nb_bes"]):
        if nodes[k][n]["type"] in concernedBuildingTypes:
            if nodes[k][n]["devs"]["bz_sf"]["cap"] > 0:
                nodes[k][n]["devs"]["bz_sf"]["cap"] = 0
                nodes[k][n]["devs"]["bz_sf"]["status"] = "inactive"

    # calculate certain typeweek again (now without Sunfire FC)
    current_index = np.where(np.isin(index_typeweeks, k))[0][-1]
    index_typeweeks.insert(current_index + 1, k)
    '''
    return nodes, index_typeweeks

def decentral_operation(node, params, pars_rh, building_params, init_val, n_opt):

    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """
           
    opti_res = decentral_opti.compute(node, params, pars_rh, building_params, init_val, n_opt)

    return opti_res

def init_val_decentral_operation(opti_bes, par_rh, n_opt):

    init_val = decentral_opti.compute_initial_values(opti_bes, par_rh, n_opt)

    return init_val


def central_operation(nodes, params, pars_rh, building_params, init_val, n_opt, options):
    """
    This function computes a deterministic solution.
    Internally, the results of the subproblem are stored.
    """

    opti_res = central_opti.compute(nodes, params, pars_rh, building_params, init_val, n_opt, options)

    return opti_res


def init_val_central_operation(opti_res, nodes, par_rh, n_opt):
    init_val = central_opti.compute_initial_values(opti_res, nodes, par_rh, n_opt)

    return init_val