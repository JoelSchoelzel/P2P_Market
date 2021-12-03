#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 09:27:25 2020

@author: timowenzel
"""

import numpy as np


def pv_share(pv_share,nodes):
    
    if pv_share==0.5 or pv_share==0.25 or pv_share==1:
        pv_avail=np.zeros(shape=(nodes,1))
        for n in range(nodes):
            k=1/pv_share
            if  n%k==0:
                pv_avail[n]=1
            else:
                pv_avail[n]=0
    
    elif pv_share==0.75:
        pv_avail=np.ones(shape=(nodes,1))
        for n in range(nodes):
            k=1/(1-pv_share)
            if  n%k==0:
                pv_avail[n]=0
            else:
                pv_avail[n]=1
      
    elif pv_share==0:
        pv_avail=np.zeros(shape=(nodes,1))
        
    return pv_avail

