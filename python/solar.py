# -*- coding: utf-8 -*-
"""
Developed by:  E.ON Energy Research Center,
               Institute for Energy Efficient Buildings and Indoor Climate, 
               RWTH Aachen University, Germany, 2019.
"""

import numpy as np
import python.sun as sun

            
#%%
def get_irrad_profile(param, azimuth, elevation, options):
    """
    Calculates global irradiance on tilted surface from weather file.
    Parameters
    ----------
    param : dictionary contains
        weather data from weather file
        and PV surface data
    Returns
    -------
    sun.getTotalRadiationTiltedSurface() : numpy array
        global irradiance on tilted surface
    """
    
    # Load PV data
    ele = elevation
    azim = azimuth
    
    # Load time series as numpy array
    sun_diffuse = param["G_dif"]
    sun_direct = param["G_dir"]

    # Define local properties
    time_zone = options["time_zone"]            # ---,      time zone
    location = options["location"]              # degree,   latitude, longitude of location
    altitude = options["altitude"]              # m,        height of location above sea level
    
    # Calculate geometric relations
    timeDiscretization = int(3600*options["discretization_input_data"])
    timesteps = int(8760/options["discretization_input_data"])

    geometry = sun.getGeometry(0, timeDiscretization, timesteps, time_zone, location, altitude) # first three: (initialTime, timeDiscretization, number of timesteps)
    (omega, delta, thetaZ, airmass, Gon) = geometry
    
    theta = sun.getIncidenceAngle(ele, azim, location[0], omega, delta)
    theta = theta[1]
    
    # cosTheta is not required
    # Calculate radiation on tilted surface
    return sun.getTotalRadiationTiltedSurface(theta, thetaZ, sun_direct, sun_diffuse, airmass, Gon, ele, 0.2)





