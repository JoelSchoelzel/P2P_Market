#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 01 11:28:27 2015

@author: tsz
"""

from __future__ import division
import numpy as np
import pandas as pd
import math
#import k_medoids
import python.k_medoids as k_medoids
import python.parse_inputs as parse_inputs
from scipy.io import loadmat

def _distances(values, norm=2):
    """
    Compute distance matrix for all data sets (rows of values)
    
    Parameters
    ----------
    values : 2-dimensional array
        Rows represent days and columns values
    norm : integer, optional
        Compute the distance according to this norm. 2 is the standard
        Euklidean-norm.
    
    Return
    ------
    d : 2-dimensional array
        Distances between each data set
    """
    # Initialize distance matrix
    d = np.zeros((values.shape[1], values.shape[1]))

    # Define a function that computes the distance between two days
    dist = (lambda day1, day2, r: 
            math.pow(np.sum(np.power(np.abs(day1 - day2), r)), 1/r))

    # Remember: The d matrix is symmetrical!
    for i in range(values.shape[1]): # loop over first days
        for j in range(i+1, values.shape[1]): # loop second days
            d[i, j] = dist(values[:,i], values[:,j], norm)
    
    # Fill the remaining entries
    d = d + d.T
    
    return d



def cluster(inputs, number_clusters=12, len_day=24, norm=2, time_limit=300, mip_gap=0.0,
            weights=None):
    """
    Cluster a set of inputs into clusters by solving a k-medoid problem.
    
    Parameters
    ----------
    inputs : 2-dimensional array
        First dimension: Number of different input types.
        Second dimension: Values for each time step of interes.
    number_clusters : integer, optional
        How many clusters shall be computed?
    norm : integer, optional
        Compute the distance according to this norm. 2 is the standard
        Euklidean-norm.
    time_limit : integer, optional
        Time limit for the optimization in seconds
    mip_gap : float, optional
        Optimality tolerance (0: proven global optimum)
    weights : 1-dimensional array, optional
        Weight for each input. If not provided, all inputs are treated equally.
    
    Returns
    -------
    scaled_typ_days : 
        Scaled typical demand days. The scaling is based on the annual demands.
    nc : array_like
        Weighting factors of each cluster
    z : 2-dimensional array
        Mapping of each day to the clusters
    """
    # Determine time steps per day
#    len_day = int(inputs.shape[1] / 365)
#    len_day = int(inputs.shape[1] / 52)
    
    num_periods = int(inputs.shape[1] / len_day)
    
    # Set weights if not already given
    if weights == None:
        weights = np.ones(inputs.shape[0])
    elif not sum(weights) == 1: # Rescale weights
        weights = np.array(weights) / sum(weights)
    
    # Manipulate inputs
    # Initialize arrays
    inputsTransformed = []
    inputsScaled = []
    inputsScaledTransformed = []
    
    # Fill and reshape
    # Scaling to values between 0 and 1, thus all inputs shall have the same
    # weight and will be clustered equally in terms of quality 
    for i in range(inputs.shape[0]):
        vals = inputs[i,:]
        temp = ((vals - np.min(vals)) / (np.max(vals) - np.min(vals))
                * math.sqrt(weights[i]))
        inputsScaled.append(temp)
        inputsScaledTransformed.append(temp.reshape((len_day, num_periods), order="F"))
        inputsTransformed.append(vals.reshape((len_day, num_periods), order="F"))
#        inputsScaledTransformed.append(temp.reshape((len_day, 52), order="F"))
#        inputsTransformed.append(vals.reshape((len_day, 52), order="F"))

    # Put the scaled and reshaped inputs together
    L = np.concatenate(tuple(inputsScaledTransformed))

    # Compute distances
    d = _distances(L, norm)

    # Execute optimization model
    (y, z, obj) = k_medoids.k_medoids(d, number_clusters, time_limit, mip_gap)
    
    # Section 2.3 and retain typical days
    nc = np.zeros_like(y)
    typicalDays = []

    # nc contains how many days are there in each cluster
    nc = []
    for i in range(len(y)):
        temp = np.sum(z[i,:])
        if temp > 0:
            nc.append(temp)
            typicalDays.append([ins[:,i] for ins in inputsTransformed])

    typicalDays = np.array(typicalDays)
    nc = np.array(nc, dtype="int")
    nc_cumsum = np.cumsum(nc) * len_day

    # Construct (yearly) load curves
    # ub = upper bound, lb = lower bound
    clustered = np.zeros_like(inputs)
    for i in range(len(nc)):
        if i == 0:
            lb = 0
        else:
            lb = nc_cumsum[i-1]
        ub = nc_cumsum[i]
        
        for j in range(len(inputsTransformed)):
            clustered[j, lb:ub] = np.tile(typicalDays[i][j], nc[i])

    # Scaling to preserve original demands
    sums_inputs = [np.sum(inputs[j,:]) for j in range(inputs.shape[0])]
    scaled = np.array([nc[day] * typicalDays[day,:,:] 
                       for day in range(number_clusters)])
    sums_scaled = [np.sum(scaled[:,j,:]) for j in range(inputs.shape[0])]
    scaling_factors = [sums_inputs[j] / sums_scaled[j] 
                       for j in range(inputs.shape[0])]
    scaled_typ_days = [scaling_factors[j] * typicalDays[:,j,:]
                       for j in range(inputs.shape[0])]
    

    return (scaled_typ_days, nc, z, inputsTransformed)

def get_cluster():

    # Clustering
    raw_inputs = {}
    raw_inputs["solar_irrad"] = np.loadtxt("raw_inputs/solar_rad_35deg.csv", max_rows=8760)
    raw_inputs["temperature"] = np.loadtxt("raw_inputs/temperature.csv", max_rows=8760)
    raw_inputs["windspeed"] = pd.read_csv("raw_inputs/bedburg/weather.csv")["Windgeschw 10m m/s"].to_numpy()

    dhw = {}
    sh = {}

    #nodes,weather_param,devs1,devs2,devs3,COP,tech_par=parameters_timo.load_params(113,8734,1,True)
    nodes,houses = parse_inputs.read_demands("nodes.txt", 0, 8760, 113)

    demands = {}
    demands = parse_inputs.demand_electrolysis()

    inputs_clustering = []

    inputs_clustering.append(raw_inputs["solar_irrad"][:8736])
    inputs_clustering.append(raw_inputs["temperature"][:8736])
    inputs_clustering.append(raw_inputs["windspeed"][:8736])
    for n in range(113):
        inputs_clustering.append(nodes[n]["elec"][:8736])
        inputs_clustering.append(nodes[n]["heat"][:8736])
        inputs_clustering.append(nodes[n]["dhw"][:8736])
    for elec in range(1):
        inputs_clustering.append(demands["hydro_fc_heat"][:8736])
        inputs_clustering.append(demands["hydro_chp_heat"][:8736])
        inputs_clustering.append(demands["hydro_trans"][:8736])


    (inputs, nc, z,inputs_transformed) = cluster(np.array(inputs_clustering),
                                     number_clusters=3, len_day=24*7, norm=2, time_limit=300, mip_gap=0.0,weights=None)


    len_day = np.shape(inputs[0])[1] # Determine time steps per day

    clustered = {}
    clustered["solar_irrad"] = inputs[0]
    clustered["temperature"] = inputs[1]
    clustered["windspeed"] = inputs[2]
    for n in range(113):
        clustered["bes_"+str(n)] = {"elec":      inputs[3+n*3],
                        "heat":      inputs[4+n*3],
                        "dhw":             inputs[5+n*3],
                        "weights":          nc}


    clustered["elec_"+str(0)] = {"hydro_fc_heat": inputs[-3],
                                "hydro_chp_heat": inputs[-2],
                                "hydro_trans": inputs[-1],
                                "weights": nc}


    clustered_long = {}
    clustered_long["solar_irrad"] = {}
    clustered_long["temperature"] = {}
    clustered_long["windspeed"] = {}
    for n in range(113):
      clustered_long["bes_" + str(n)] = {}
    for ev in range(20):
        clustered_long["ev_" + str(ev)] = {}
    clustered_long["elec_" + str(0)] = {}

    for i in range(3):
        clustered_long["solar_irrad"][i] = np.append(inputs[0][i], inputs[0][i][:36])
        clustered_long["temperature"][i] = np.append(inputs[1][i], inputs[1][i][:0+36])
        clustered_long["windspeed"][i] = np.append(inputs[2][i], inputs[2][i][:0+36])
        for n in range(113):
            clustered_long["bes_" + str(n)][i] = {"elec": np.append(inputs[3 + n * 3][i], inputs[3 + n * 3][i][:0+36]),
                                            "heat": np.append(inputs[4 + n * 3][i], inputs[4 + n * 3][i][:0+36]),
                                            "dhw": np.append(inputs[5 + n * 3][i], inputs[5 + n * 3][i][:0+36]),
                                            "weights": nc}


        clustered_long["elec_" + str(0)][i] = {"hydro_fc_heat": np.append(inputs[-3][i], inputs[-3][i][:0+36]),
                                   "hydro_chp_heat": np.append(inputs[-2][i], inputs[-2][i][:0+36]),
                                   "hydro_trans": np.append(inputs[-1][i], inputs[-1][i][:0+36]),
                                   "weights": nc}

    # get sigma-function: for each day of the year, find the corresponding type-day
    # Get list of days which are used as type-days
    typeweeks = np.zeros(3, dtype=np.int32)
    n = 0
    for d in range(52):
        if any(z[d]):
            typeweeks[n] = d
            n += 1

    # Assign each day of the year to its typeday
    sigma = np.zeros(52, dtype=np.int32)
    for week in range(len(sigma)):
        d = np.where(z[:, week] == 1)[0][0]
        sigma[week] = np.where(typeweeks == d)[0][0]

    return clustered_long, sigma

def get_cluster_2():

    raw_inputs = {}

    raw_inputs["wind_gen_bed"] = pd.read_csv("raw_inputs/bedburg/optimization_input_data_bedburg_wind_energy.csv")["Windpower"].to_numpy()
    raw_inputs["windspeed"] = pd.read_csv("raw_inputs/bedburg/weather.csv")["Windgeschw 10m m/s"].to_numpy()
    for i in range(len(raw_inputs["wind_gen_bed"])):
        try:
            raw_inputs["wind_gen_bed"][i] = float(raw_inputs["wind_gen_bed"][i])
        except ValueError:
            raw_inputs["wind_gen_bed"][i] = float(2800)

    inputs_clustering_wind_gen = []
    inputs_clustering_wind_gen.append(raw_inputs["wind_gen_bed"][:8736])
    inputs_clustering_wind_gen.append(raw_inputs["windspeed"][:8736])
    (inputs_2, nc_2, z_2, inputs_transformed_2) = cluster(np.array(inputs_clustering_wind_gen),
                                                  number_clusters=3, len_day=24 * 7, norm=2, time_limit=300,
                                                  mip_gap=0.0, weights=None)
    clustered_wind_gen  = {}
    clustered_wind_gen["win_gen_bed"] = {}
    clustered_wind_gen["windspeed"] = {}
    for i in range(3):
        clustered_wind_gen["win_gen_bed"][i] = np.append(inputs_2[0][i], inputs_2[0][i][:36])
        clustered_wind_gen["windspeed"][i] = np.append(inputs_2[1][i], inputs_2[1][i][:36])

    for i in range(3):
        for y in range(204):
            if clustered_wind_gen["win_gen_bed"][i][y] > 5700:
                    clustered_wind_gen["win_gen_bed"][i][y]  = 5700
            else: clustered_wind_gen["win_gen_bed"][i][y]  = int(clustered_wind_gen["win_gen_bed"][i][y] )



    return clustered_wind_gen