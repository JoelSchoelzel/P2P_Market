# -*- coding: utf-8 -*-
"""
Developed by:  E.ON Energy Research Center,
               Institute for Energy Efficient Buildings and Indoor Climate, 
               RWTH Aachen University, Germany, 2019.
"""

import numpy as np
import python.sun as sun

            
#%%
def get_irrad_profile(param, azimuth, elevation):
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
    sun_global = param["G_sol"]
    sun_direct = sun_global - sun_diffuse

    # todo: local properties as input in main file
    # Define local properties of Bedburg
    time_zone = 1                # ---,      time zone 
    location = (50.99, 6.57)     # degree,   latitude, longitude of location
    altitude = 70.0              # m,        height of location above sea level
    
    # Calculate geometric relations
    geometry = sun.getGeometry(0, 900, 8760, time_zone, location, altitude)
    (omega, delta, thetaZ, airmass, Gon) = geometry
    
    theta = sun.getIncidenceAngle(ele, azim, location[0], omega, delta)
    theta = theta[1] 
    
    # cosTheta is not required
    # Calculate radiation on tilted surface
    return sun.getTotalRadiationTiltedSurface(theta, thetaZ, sun_direct, sun_diffuse, airmass, Gon, ele, 0.2)





