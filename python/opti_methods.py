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
        for k in range(options["number_typeWeeks"]):
            init_val[k] = {}
            opti_res[k] = {}
            for n_opt in range(par_rh["n_opt"]):
                opti_res[k][n_opt] = {}
                init_val[k][0] = {}
                init_val[k][n_opt+1] = {}
                if n_opt == 0:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    init_val[k][n_opt] = {}
                    opti_res[k][n_opt] = central_operation(nodes[k],params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)
                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                else:
                    print("Starting optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ".")
                    opti_res[k][n_opt] = central_operation(nodes[k], params, par_rh, building_params,
                                                          init_val[k][n_opt], n_opt, options)
                    init_val[k][n_opt + 1] = init_val_central_operation(opti_res[k][n_opt], nodes[k], par_rh, n_opt)
                print("Finished optimization: type week: " + str(k) + " n_opt: " + str(n_opt) + ". " + str((par_rh["n_opt"]*k + n_opt+1) / (par_rh["n_opt"]* options["number_typeWeeks"]) * 100) + "% of optimizations processed.")
        return opti_res


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