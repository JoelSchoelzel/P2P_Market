#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 15:38:47 2015

@author: jsc
"""

from __future__ import division
import numpy as np
import python.opti_bes as bes_operation

class bes(object):
    """
    Overview of all methods and usage of this class
    """
    
    def __init__(self, node, params, pars_rh, weather, housedevs):
        """
        """
        
        self.res_x = []
        self.res_y = []
        self.res_energy = []
        self.res_power = []
        self.res_heat = []
        self.res_soc = []
        self.res_p_imp = []
        self.res_p_ch = []
        self.res_p_dch = []
        self.res_p_use = []
        self.res_p_sell = []
        self.res_area = 0
        self.res_cap = 0
        self.res_volume = 0
        self.res_temperature = []
        self.obj = []
        self.res_c_inv = 0
        self.res_c_om = 0
        self.res_c_dem = 0
        self.res_c_met = 0
        self.res_rev = {}
        self.res_chp_sub = []
        self.res_soc_nom = []
        self.res_power_nom = []
        self.res_heat_nom = []
        self.res_soc_init = []
        self.res_p_use = {}
        self.res_p_sell ={}
        self.devs = node["devs"]
        self.nodes = node
        self.pars_rh = pars_rh
        self.eco = params["eco"]
        self.phy = params["phy"]
        self.housedevs = housedevs
        self.weather = weather

        self.res_y_imp = {}
        self.res_y_exp = {}
        
    def op_proposal(self, node, params, pars_rh, building_params, scenario, init_val, n_opt):

        """
        This function computes a deterministic solution.
        Internally, the results of the subproblem are stored.


        """
           
        opti_res = bes_operation.compute(node, params, pars_rh, building_params, scenario, init_val, n_opt)
        
        (res_y, res_power, res_heat, res_soc,
            res_p_imp, res_p_ch, res_p_dch, res_p_use, res_p_sell,
            obj, res_c_dem, res_rev, res_soc_nom, node,
            objVal, runtime, soc_init_rh) = opti_res
        
        self.opti_res = opti_res
        
        return (opti_res)

    def init_val(self, opti_bes, par_rh, n_opt):

        init_val = bes_operation.compute_initial_values(opti_bes, par_rh, n_opt)

        return init_val