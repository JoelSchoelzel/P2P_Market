import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import rc
rc("font", **{"family": "sans-serif", "sans-serif": "Times New Roman"})  # "serif": [""]})  # Computer Modern Roman"
import pandas as pd
import pickle


path_root = "/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/Results_for_plots/Quartier 3/"

# ------------------------ JANUARY ------------------------
# ---------- values over time ----------
with open(path_root+"/1_Jan/nB=5/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_5:
    time_jan_e_5 = pickle.load(time_jan_e_5)
with open(path_root+"/1_Jan/nB=5/nCH=36/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_5_h:
    time_jan_e_5_h = pickle.load(time_jan_e_5_h)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_price/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_p_5:
    time_jan_p_5 = pickle.load(time_jan_p_5)
with open(path_root + "/1_Jan/nB=5/nCH=36/mean_price/res_time_P2P_Quartier_3_jan.p", 'rb') as time_jan_p_5_h:
    time_jan_p_5_h = pickle.load(time_jan_p_5_h)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_5:
    time_jan_q_5 = pickle.load(time_jan_q_5)
with open(path_root+"/1_Jan/nB=5/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_5_h:
    time_jan_q_5_h = pickle.load(time_jan_q_5_h)

with open(path_root+"/1_Jan/nB=3/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_3:
    time_jan_e_3 = pickle.load(time_jan_e_3)
with open(path_root+"/1_Jan/nB=3/nCH=36/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_3_h:
    time_jan_e_3_h = pickle.load(time_jan_e_3_h)
with open(path_root+"/1_Jan/nB=3/nCH=nB/mean_price/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_p_3:
    time_jan_p_3 = pickle.load(time_jan_p_3)
with open(path_root + "/1_Jan/nB=3/nCH=36/mean_price/res_time_P2P_Quartier_3_jan.p", 'rb') as time_jan_p_3_h:
    time_jan_p_3_h = pickle.load(time_jan_p_3_h)
with open(path_root+"/1_Jan/nB=3/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_3:
    time_jan_q_3 = pickle.load(time_jan_q_3)
with open(path_root+"/1_Jan/nB=3/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_3_h:
    time_jan_q_3_h = pickle.load(time_jan_q_3_h)

with open(path_root+"/1_Jan/nB=1/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_1:
    time_jan_e_1 = pickle.load(time_jan_e_1)
with open(path_root+"/1_Jan/nB=1/nCH=36/flex_energy/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_e_1_h:
    time_jan_e_1_h = pickle.load(time_jan_e_1_h)
with open(path_root+"/1_Jan/nB=1/nCH=nB/mean_price/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_p_1:
    time_jan_p_1 = pickle.load(time_jan_p_1)
with open(path_root + "/1_Jan/nB=1/nCH=36/mean_price/res_time_P2P_Quartier_3_jan.p", 'rb') as time_jan_p_1_h:
    time_jan_p_1_h = pickle.load(time_jan_p_1_h)
with open(path_root+"/1_Jan/nB=1/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_1:
    time_jan_q_1 = pickle.load(time_jan_q_1)
with open(path_root+"/1_Jan/nB=1/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jan.p",'rb') as time_jan_q_1_h:
    time_jan_q_1_h = pickle.load(time_jan_q_1_h)

# ---------- absolute values ----------
with open(path_root+"/1_Jan/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_5:
    val_jan_e_5 = pickle.load(val_jan_e_5)
with open(path_root+"/1_Jan/nB=5/nCH=36/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_5_h:
    val_jan_e_5_h = pickle.load(val_jan_e_5_h)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_q_5:
    val_jan_q_5 = pickle.load(val_jan_q_5)
with open(path_root + "/1_Jan/nB=5/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jan.p", 'rb') as val_jan_q_5_h:
    val_jan_q_5_h = pickle.load(val_jan_q_5_h)
with open(path_root+"/1_Jan/nB=5/nCH=nB/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_5:
    val_jan_p_5 = pickle.load(val_jan_p_5)
with open(path_root+"/1_Jan/nB=5/nCH=36/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_5_h:
    val_jan_p_5_h = pickle.load(val_jan_p_5_h)

with open(path_root+"/1_Jan/nB=3/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_3:
    val_jan_e_3 = pickle.load(val_jan_e_3)
with open(path_root+"/1_Jan/nB=3/nCH=36/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_3_h:
    val_jan_e_3_h = pickle.load(val_jan_e_3_h)
with open(path_root+"/1_Jan/nB=3/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_q_3:
    val_jan_q_3 = pickle.load(val_jan_q_3)
with open(path_root+"/1_Jan/nB=3/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_q_3_h:
    val_jan_q_3_h = pickle.load(val_jan_q_3_h)
with open(path_root+"/1_Jan/nB=3/nCH=nB/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_3:
    val_jan_p_3 = pickle.load(val_jan_p_3)
with open(path_root+"/1_Jan/nB=3/nCH=36/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_3_h:
    val_jan_p_3_h = pickle.load(val_jan_p_3_h)

with open(path_root+"/1_Jan/nB=1/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_1:
    val_jan_e_1 = pickle.load(val_jan_e_1)
with open(path_root+"/1_Jan/nB=1/nCH=36/flex_energy/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_e_1_h:
    val_jan_e_1_h = pickle.load(val_jan_e_1_h)
with open(path_root+"/1_Jan/nB=1/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_q_1:
    val_jan_q_1 = pickle.load(val_jan_q_1)
with open(path_root+"/1_Jan/nB=1/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_q_1_h:
    val_jan_q_1_h = pickle.load(val_jan_q_1_h)
with open(path_root+"/1_Jan/nB=1/nCH=nB/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_1:
    val_jan_p_1 = pickle.load(val_jan_p_1)
with open(path_root+"/1_Jan/nB=1/nCH=36/mean_price/res_val_P2P_Quartier_3_jan.p",'rb') as val_jan_p_1_h:
    val_jan_p_1_h = pickle.load(val_jan_p_1_h)


# ------------------------ APRIL ------------------------
# ---------- values over time ----------
with open(path_root + "/2_Apr/nB=5/nCH=nB/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_5:
    time_apr_e_5 = pickle.load(time_apr_e_5)
with open(path_root + "/2_Apr/nB=5/nCH=36/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_5_h:
    time_apr_e_5_h = pickle.load(time_apr_e_5_h)
with open(path_root + "/2_Apr/nB=5/nCH=nB/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_5:
    time_apr_p_5 = pickle.load(time_apr_p_5)
with open(path_root + "/2_Apr/nB=5/nCH=36/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_5_h:
    time_apr_p_5_h = pickle.load(time_apr_p_5_h)
with open(path_root + "/2_Apr/nB=5/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_5:
    time_apr_q_5 = pickle.load(time_apr_q_5)
with open(path_root + "/2_Apr/nB=5/nCH=36/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_5_h:
    time_apr_q_5_h = pickle.load(time_apr_q_5_h)

with open(path_root + "/2_Apr/nB=3/nCH=nB/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_3:
    time_apr_e_3 = pickle.load(time_apr_e_3)
with open(path_root + "/2_Apr/nB=3/nCH=36/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_3_h:
    time_apr_e_3_h = pickle.load(time_apr_e_3_h)
with open(path_root + "/2_Apr/nB=3/nCH=nB/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_3:
    time_apr_p_3 = pickle.load(time_apr_p_3)
with open(path_root + "/2_Apr/nB=3/nCH=36/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_3_h:
    time_apr_p_3_h = pickle.load(time_apr_p_3_h)
with open(path_root + "/2_Apr/nB=3/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_3:
    time_apr_q_3 = pickle.load(time_apr_q_3)
with open(path_root + "/2_Apr/nB=3/nCH=36/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_3_h:
    time_apr_q_3_h = pickle.load(time_apr_q_3_h)

with open(path_root + "/2_Apr/nB=1/nCH=nB/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_1:
    time_apr_e_1 = pickle.load(time_apr_e_1)
with open(path_root + "/2_Apr/nB=1/nCH=36/flex_energy/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_e_1_h:
    time_apr_e_1_h = pickle.load(time_apr_e_1_h)
with open(path_root + "/2_Apr/nB=1/nCH=nB/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_1:
    time_apr_p_1 = pickle.load(time_apr_p_1)
with open(path_root + "/2_Apr/nB=1/nCH=36/mean_price/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_p_1_h:
    time_apr_p_1_h = pickle.load(time_apr_p_1_h)
with open(path_root + "/2_Apr/nB=1/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_1:
    time_apr_q_1 = pickle.load(time_apr_q_1)
with open(path_root + "/2_Apr/nB=1/nCH=36/mean_quantity/res_time_P2P_Quartier_3_apr.p", 'rb') as time_apr_q_1_h:
    time_apr_q_1_h = pickle.load(time_apr_q_1_h)


# ---------- absolute values ----------
with open(path_root+"/2_Apr/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_5:
    val_apr_e_5 = pickle.load(val_apr_e_5)
with open(path_root+"/2_Apr/nB=5/nCH=36/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_5_h:
    val_apr_e_5_h = pickle.load(val_apr_e_5_h)
with open(path_root+"/2_Apr/nB=5/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_q_5:
    val_apr_q_5 = pickle.load(val_apr_q_5)
with open(path_root + "/2_Apr/nB=5/nCH=36/mean_quantity/res_val_P2P_Quartier_3_apr.p", 'rb') as val_apr_q_5_h:
    val_apr_q_5_h = pickle.load(val_apr_q_5_h)
with open(path_root+"/2_Apr/nB=5/nCH=nB/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_5:
    val_apr_p_5 = pickle.load(val_apr_p_5)
with open(path_root+"/2_Apr/nB=5/nCH=36/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_5_h:
    val_apr_p_5_h = pickle.load(val_apr_p_5_h)

with open(path_root+"/2_Apr/nB=3/nCH=nB/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_3:
    val_apr_e_3 = pickle.load(val_apr_e_3)
with open(path_root+"/2_Apr/nB=3/nCH=36/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_3_h:
    val_apr_e_3_h = pickle.load(val_apr_e_3_h)
with open(path_root+"/2_Apr/nB=3/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_q_3:
    val_apr_q_3 = pickle.load(val_apr_q_3)
with open(path_root+"/2_Apr/nB=3/nCH=36/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_q_3_h:
    val_apr_q_3_h = pickle.load(val_apr_q_3_h)
with open(path_root+"/2_Apr/nB=3/nCH=nB/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_3:
    val_apr_p_3 = pickle.load(val_apr_p_3)
with open(path_root+"/2_Apr/nB=3/nCH=36/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_3_h:
    val_apr_p_3_h = pickle.load(val_apr_p_3_h)

with open(path_root+"/2_Apr/nB=1/nCH=nB/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_1:
    val_apr_e_1 = pickle.load(val_apr_e_1)
with open(path_root+"/2_Apr/nB=1/nCH=36/flex_energy/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_e_1_h:
    val_apr_e_1_h = pickle.load(val_apr_e_1_h)
with open(path_root+"/2_Apr/nB=1/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_q_1:
    val_apr_q_1 = pickle.load(val_apr_q_1)
with open(path_root+"/2_Apr/nB=1/nCH=36/mean_quantity/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_q_1_h:
    val_apr_q_1_h = pickle.load(val_apr_q_1_h)
with open(path_root+"/2_Apr/nB=1/nCH=nB/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_1:
    val_apr_p_1 = pickle.load(val_apr_p_1)
with open(path_root+"/2_Apr/nB=1/nCH=36/mean_price/res_val_P2P_Quartier_3_apr.p",'rb') as val_apr_p_1_h:
    val_apr_p_1_h = pickle.load(val_apr_p_1_h)


# ------------------------ JULY ------------------------
# ---------- values over time ----------
with open(path_root + "/3_Jul/nB=5/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_5:
    time_jul_e_5 = pickle.load(time_jul_e_5)
with open(path_root + "/3_Jul/nB=5/nCH=36/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_5_h:
    time_jul_e_5_h = pickle.load(time_jul_e_5_h)
with open(path_root + "/3_Jul/nB=5/nCH=nB/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_5:
    time_jul_p_5 = pickle.load(time_jul_p_5)
with open(path_root + "/3_Jul/nB=5/nCH=36/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_5_h:
    time_jul_p_5_h = pickle.load(time_jul_p_5_h)
with open(path_root + "/3_Jul/nB=5/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_5:
    time_jul_q_5 = pickle.load(time_jul_q_5)
with open(path_root + "/3_Jul/nB=5/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_5_h:
    time_jul_q_5_h = pickle.load(time_jul_q_5_h)

with open(path_root + "/3_Jul/nB=3/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_3:
    time_jul_e_3 = pickle.load(time_jul_e_3)
with open(path_root + "/3_Jul/nB=3/nCH=36/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_3_h:
    time_jul_e_3_h = pickle.load(time_jul_e_3_h)
with open(path_root + "/3_Jul/nB=3/nCH=nB/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_3:
    time_jul_p_3 = pickle.load(time_jul_p_3)
with open(path_root + "/3_Jul/nB=3/nCH=36/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_3_h:
    time_jul_p_3_h = pickle.load(time_jul_p_3_h)
with open(path_root + "/3_Jul/nB=3/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_3:
    time_jul_q_3 = pickle.load(time_jul_q_3)
with open(path_root + "/3_Jul/nB=3/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_3_h:
    time_jul_q_3_h = pickle.load(time_jul_q_3_h)

with open(path_root + "/3_Jul/nB=1/nCH=nB/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_1:
    time_jul_e_1 = pickle.load(time_jul_e_1)
with open(path_root + "/3_Jul/nB=1/nCH=36/flex_energy/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_e_1_h:
    time_jul_e_1_h = pickle.load(time_jul_e_1_h)
with open(path_root + "/3_Jul/nB=1/nCH=nB/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_1:
    time_jul_p_1 = pickle.load(time_jul_p_1)
with open(path_root + "/3_Jul/nB=1/nCH=36/mean_price/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_p_1_h:
    time_jul_p_1_h = pickle.load(time_jul_p_1_h)
with open(path_root + "/3_Jul/nB=1/nCH=nB/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_1:
    time_jul_q_1 = pickle.load(time_jul_q_1)
with open(path_root + "/3_Jul/nB=1/nCH=36/mean_quantity/res_time_P2P_Quartier_3_jul.p", 'rb') as time_jul_q_1_h:
    time_jul_q_1_h = pickle.load(time_jul_q_1_h)

# ---------- absolute values ----------
with open(path_root+"/3_Jul/nB=5/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_5:
    val_jul_e_5 = pickle.load(val_jul_e_5)
with open(path_root+"/3_Jul/nB=5/nCH=36/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_5_h:
    val_jul_e_5_h = pickle.load(val_jul_e_5_h)
with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_q_5:
    val_jul_q_5 = pickle.load(val_jul_q_5)
with open(path_root + "/3_Jul/nB=5/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jul.p", 'rb') as val_jul_q_5_h:
    val_jul_q_5_h = pickle.load(val_jul_q_5_h)
with open(path_root+"/3_Jul/nB=5/nCH=nB/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_5:
    val_jul_p_5 = pickle.load(val_jul_p_5)
with open(path_root+"/3_Jul/nB=5/nCH=36/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_5_h:
    val_jul_p_5_h = pickle.load(val_jul_p_5_h)

with open(path_root+"/3_Jul/nB=3/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_3:
    val_jul_e_3 = pickle.load(val_jul_e_3)
with open(path_root+"/3_Jul/nB=3/nCH=36/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_3_h:
    val_jul_e_3_h = pickle.load(val_jul_e_3_h)
with open(path_root+"/3_Jul/nB=3/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_q_3:
    val_jul_q_3 = pickle.load(val_jul_q_3)
with open(path_root+"/3_Jul/nB=3/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_q_3_h:
    val_jul_q_3_h = pickle.load(val_jul_q_3_h)
with open(path_root+"/3_Jul/nB=3/nCH=nB/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_3:
    val_jul_p_3 = pickle.load(val_jul_p_3)
with open(path_root+"/3_Jul/nB=3/nCH=36/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_3_h:
    val_jul_p_3_h = pickle.load(val_jul_p_3_h)

with open(path_root+"/3_Jul/nB=1/nCH=nB/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_1:
    val_jul_e_1 = pickle.load(val_jul_e_1)
with open(path_root+"/3_Jul/nB=1/nCH=36/flex_energy/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_e_1_h:
    val_jul_e_1_h = pickle.load(val_jul_e_1_h)
with open(path_root+"/3_Jul/nB=1/nCH=nB/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_q_1:
    val_jul_q_1 = pickle.load(val_jul_q_1)
with open(path_root+"/3_Jul/nB=1/nCH=36/mean_quantity/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_q_1_h:
    val_jul_q_1_h = pickle.load(val_jul_q_1_h)
with open(path_root+"/3_Jul/nB=1/nCH=nB/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_1:
    val_jul_p_1 = pickle.load(val_jul_p_1)
with open(path_root+"/3_Jul/nB=1/nCH=36/mean_price/res_val_P2P_Quartier_3_jul.p",'rb') as val_jul_p_1_h:
    val_jul_p_1_h = pickle.load(val_jul_p_1_h)




# create the DataFrame to plot over time
# ------------ JANUARY ------------
# ------ demand ------
df_time_jan_e_5_dem = pd.DataFrame(list(time_jan_e_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_e_5_h_dem = pd.DataFrame(list(time_jan_e_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_5_dem = pd.DataFrame(list(time_jan_q_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_5_h_dem = pd.DataFrame(list(time_jan_q_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_5_dem = pd.DataFrame(list(time_jan_p_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_5_h_dem = pd.DataFrame(list(time_jan_p_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jan_e_3_dem = pd.DataFrame(list(time_jan_e_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_e_3_h_dem = pd.DataFrame(list(time_jan_e_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_3_dem = pd.DataFrame(list(time_jan_q_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_3_h_dem = pd.DataFrame(list(time_jan_q_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_3_dem = pd.DataFrame(list(time_jan_p_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_3_h_dem = pd.DataFrame(list(time_jan_p_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jan_e_1_dem = pd.DataFrame(list(time_jan_e_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_e_1_h_dem = pd.DataFrame(list(time_jan_e_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_1_dem = pd.DataFrame(list(time_jan_q_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_q_1_h_dem = pd.DataFrame(list(time_jan_q_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_1_dem = pd.DataFrame(list(time_jan_p_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jan_p_1_h_dem = pd.DataFrame(list(time_jan_p_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])

# ------ supply ------
df_time_jan_e_5_sup = pd.DataFrame(list(time_jan_e_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_e_5_h_sup = pd.DataFrame(list(time_jan_e_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_5_sup = pd.DataFrame(list(time_jan_q_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_5_h_sup = pd.DataFrame(list(time_jan_q_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_5_sup = pd.DataFrame(list(time_jan_p_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_5_h_sup = pd.DataFrame(list(time_jan_p_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jan_e_3_sup = pd.DataFrame(list(time_jan_e_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_e_3_h_sup = pd.DataFrame(list(time_jan_e_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_3_sup = pd.DataFrame(list(time_jan_q_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_3_h_sup = pd.DataFrame(list(time_jan_q_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_3_sup = pd.DataFrame(list(time_jan_p_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_3_h_sup = pd.DataFrame(list(time_jan_p_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jan_e_1_sup = pd.DataFrame(list(time_jan_e_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_e_1_h_sup = pd.DataFrame(list(time_jan_e_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_1_sup = pd.DataFrame(list(time_jan_q_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_q_1_h_sup = pd.DataFrame(list(time_jan_q_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_1_sup = pd.DataFrame(list(time_jan_p_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jan_p_1_h_sup = pd.DataFrame(list(time_jan_p_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])


# ------ traded power ------
df_time_jan_e_5_trade = pd.DataFrame(list(time_jan_e_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_e_5_h_trade = pd.DataFrame(list(time_jan_e_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_5_trade = pd.DataFrame(list(time_jan_q_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_5_h_trade = pd.DataFrame(list(time_jan_q_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_5_trade = pd.DataFrame(list(time_jan_p_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_5_h_trade = pd.DataFrame(list(time_jan_p_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_jan_e_3_trade = pd.DataFrame(list(time_jan_e_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_e_3_h_trade = pd.DataFrame(list(time_jan_e_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_3_trade = pd.DataFrame(list(time_jan_q_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_3_h_trade = pd.DataFrame(list(time_jan_q_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_3_trade = pd.DataFrame(list(time_jan_p_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_3_h_trade = pd.DataFrame(list(time_jan_p_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_jan_e_1_trade = pd.DataFrame(list(time_jan_e_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_e_1_h_trade = pd.DataFrame(list(time_jan_e_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_1_trade = pd.DataFrame(list(time_jan_q_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_q_1_h_trade = pd.DataFrame(list(time_jan_q_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_1_trade = pd.DataFrame(list(time_jan_p_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jan_p_1_h_trade = pd.DataFrame(list(time_jan_p_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])



# ------------ APRIL ------------
# ------ demand ------
df_time_apr_e_5_dem = pd.DataFrame(list(time_apr_e_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_e_5_h_dem = pd.DataFrame(list(time_apr_e_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_5_dem = pd.DataFrame(list(time_apr_q_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_5_h_dem = pd.DataFrame(list(time_apr_q_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_5_dem = pd.DataFrame(list(time_apr_p_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_5_h_dem = pd.DataFrame(list(time_apr_p_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_apr_e_3_dem = pd.DataFrame(list(time_apr_e_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_e_3_h_dem = pd.DataFrame(list(time_apr_e_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_3_dem = pd.DataFrame(list(time_apr_q_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_3_h_dem = pd.DataFrame(list(time_apr_q_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_3_dem = pd.DataFrame(list(time_apr_p_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_3_h_dem = pd.DataFrame(list(time_apr_p_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_apr_e_1_dem = pd.DataFrame(list(time_apr_e_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_e_1_h_dem = pd.DataFrame(list(time_apr_e_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_1_dem = pd.DataFrame(list(time_apr_q_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_q_1_h_dem = pd.DataFrame(list(time_apr_q_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_1_dem = pd.DataFrame(list(time_apr_p_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_apr_p_1_h_dem = pd.DataFrame(list(time_apr_p_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])

# ------ supply ------
df_time_apr_e_5_sup = pd.DataFrame(list(time_apr_e_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_e_5_h_sup = pd.DataFrame(list(time_apr_e_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_5_sup = pd.DataFrame(list(time_apr_q_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_5_h_sup = pd.DataFrame(list(time_apr_q_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_5_sup = pd.DataFrame(list(time_apr_p_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_5_h_sup = pd.DataFrame(list(time_apr_p_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_apr_e_3_sup = pd.DataFrame(list(time_apr_e_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_e_3_h_sup = pd.DataFrame(list(time_apr_e_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_3_sup = pd.DataFrame(list(time_apr_q_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_3_h_sup = pd.DataFrame(list(time_apr_q_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_3_sup = pd.DataFrame(list(time_apr_p_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_3_h_sup = pd.DataFrame(list(time_apr_p_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_apr_e_1_sup = pd.DataFrame(list(time_apr_e_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_e_1_h_sup = pd.DataFrame(list(time_apr_e_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_1_sup = pd.DataFrame(list(time_apr_q_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_q_1_h_sup = pd.DataFrame(list(time_apr_q_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_1_sup = pd.DataFrame(list(time_apr_p_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_apr_p_1_h_sup = pd.DataFrame(list(time_apr_p_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])


# ------ traded power ------
df_time_apr_e_5_trade = pd.DataFrame(list(time_apr_e_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_e_5_h_trade = pd.DataFrame(list(time_apr_e_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_5_trade = pd.DataFrame(list(time_apr_q_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_5_h_trade = pd.DataFrame(list(time_apr_q_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_5_trade = pd.DataFrame(list(time_apr_p_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_5_h_trade = pd.DataFrame(list(time_apr_p_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_apr_e_3_trade = pd.DataFrame(list(time_apr_e_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_e_3_h_trade = pd.DataFrame(list(time_apr_e_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_3_trade = pd.DataFrame(list(time_apr_q_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_3_h_trade = pd.DataFrame(list(time_apr_q_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_3_trade = pd.DataFrame(list(time_apr_p_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_3_h_trade = pd.DataFrame(list(time_apr_p_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_apr_e_1_trade = pd.DataFrame(list(time_apr_e_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_e_1_h_trade = pd.DataFrame(list(time_apr_e_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_1_trade = pd.DataFrame(list(time_apr_q_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_q_1_h_trade = pd.DataFrame(list(time_apr_q_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_1_trade = pd.DataFrame(list(time_apr_p_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_apr_p_1_h_trade = pd.DataFrame(list(time_apr_p_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])





# ------------ JULY ------------
# ------ demand ------
df_time_jul_e_5_dem = pd.DataFrame(list(time_jul_e_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_e_5_h_dem = pd.DataFrame(list(time_jul_e_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_5_dem = pd.DataFrame(list(time_jul_q_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_5_h_dem = pd.DataFrame(list(time_jul_q_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_5_dem = pd.DataFrame(list(time_jul_p_5["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_5_h_dem = pd.DataFrame(list(time_jul_p_5_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jul_e_3_dem = pd.DataFrame(list(time_jul_e_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_e_3_h_dem = pd.DataFrame(list(time_jul_e_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_3_dem = pd.DataFrame(list(time_jul_q_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_3_h_dem = pd.DataFrame(list(time_jul_q_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_3_dem = pd.DataFrame(list(time_jul_p_3["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_3_h_dem = pd.DataFrame(list(time_jul_p_3_h["total_demand"].items()), columns=["Timestep", "Total demand"])

df_time_jul_e_1_dem = pd.DataFrame(list(time_jul_e_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_e_1_h_dem = pd.DataFrame(list(time_jul_e_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_1_dem = pd.DataFrame(list(time_jul_q_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_q_1_h_dem = pd.DataFrame(list(time_jul_q_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_1_dem = pd.DataFrame(list(time_jul_p_1["total_demand"].items()), columns=["Timestep", "Total demand"])
df_time_jul_p_1_h_dem = pd.DataFrame(list(time_jul_p_1_h["total_demand"].items()), columns=["Timestep", "Total demand"])

# ------ supply ------
df_time_jul_e_5_sup = pd.DataFrame(list(time_jul_e_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_e_5_h_sup = pd.DataFrame(list(time_jul_e_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_5_sup = pd.DataFrame(list(time_jul_q_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_5_h_sup = pd.DataFrame(list(time_jul_q_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_5_sup = pd.DataFrame(list(time_jul_p_5["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_5_h_sup = pd.DataFrame(list(time_jul_p_5_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jul_e_3_sup = pd.DataFrame(list(time_jul_e_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_e_3_h_sup = pd.DataFrame(list(time_jul_e_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_3_sup = pd.DataFrame(list(time_jul_q_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_3_h_sup = pd.DataFrame(list(time_jul_q_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_3_sup = pd.DataFrame(list(time_jul_p_3["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_3_h_sup = pd.DataFrame(list(time_jul_p_3_h["total_supply"].items()), columns=["Timestep", "Total supply"])

df_time_jul_e_1_sup = pd.DataFrame(list(time_jul_e_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_e_1_h_sup = pd.DataFrame(list(time_jul_e_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_1_sup = pd.DataFrame(list(time_jul_q_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_q_1_h_sup = pd.DataFrame(list(time_jul_q_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_1_sup = pd.DataFrame(list(time_jul_p_1["total_supply"].items()), columns=["Timestep", "Total supply"])
df_time_jul_p_1_h_sup = pd.DataFrame(list(time_jul_p_1_h["total_supply"].items()), columns=["Timestep", "Total supply"])


# ------ traded power ------
df_time_jul_e_5_trade = pd.DataFrame(list(time_jul_e_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_e_5_h_trade = pd.DataFrame(list(time_jul_e_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_5_trade = pd.DataFrame(list(time_jul_q_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_5_h_trade = pd.DataFrame(list(time_jul_q_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_5_trade = pd.DataFrame(list(time_jul_p_5["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_5_h_trade = pd.DataFrame(list(time_jul_p_5_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_jul_e_3_trade = pd.DataFrame(list(time_jul_e_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_e_3_h_trade = pd.DataFrame(list(time_jul_e_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_3_trade = pd.DataFrame(list(time_jul_q_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_3_h_trade = pd.DataFrame(list(time_jul_q_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_3_trade = pd.DataFrame(list(time_jul_p_3["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_3_h_trade = pd.DataFrame(list(time_jul_p_3_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

df_time_jul_e_1_trade = pd.DataFrame(list(time_jul_e_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_e_1_h_trade = pd.DataFrame(list(time_jul_e_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_1_trade = pd.DataFrame(list(time_jul_q_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_q_1_h_trade = pd.DataFrame(list(time_jul_q_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_1_trade = pd.DataFrame(list(time_jul_p_1["traded_power"].items()), columns=["Timestep", "Total traded power"])
df_time_jul_p_1_h_trade = pd.DataFrame(list(time_jul_p_1_h["traded_power"].items()), columns=["Timestep", "Total traded power"])

# ------------ average trade price ------------
df_time_apr_e_5_price = pd.DataFrame(list(time_apr_e_5["average_trade_price"].items()), columns=["Timestep", "Average trade price"])
df_time_apr_e_5_h_price = pd.DataFrame(list(time_apr_e_5_h["average_trade_price"].items()), columns=["Timestep", "Average trade price"])

# ------------ RWTH COLORS ------------
red = ['#CC071E', '#D85C41', '#E69679', '#F3CDBB', '#FAEBE3']
blue = ['#00549F', '#407FB7', '#8EBAE5', '#C7DDF2', '#E8F1FA']
violet = ['#7A6FAC', '#9B91C1', '#BCB5D7', '#DEDAEB', '#F2F0F7']
green = ['#57ab27', '#8dc060', '#b8d698', '#ddebce', '#f2f7ec']
bordeaux = ['#a11035', '#b65256', '#cd8b87', '#e5c5c0', '#f5e8e5']
black = ['#000000', '#696969', '', '#808080', '#A9A9A9', '#DCDCDC']

# ------------ EBC COLORS ------------
red_ebc = ['#CC071E', '#DD402D', '#D85C41', '#E69679']
orange_ebc = ['#F6A800', '#FABE50', '#FDD48F']
blue_ebc = ['#00549F', '#407FB7 ', '#8EBAE5']
green_ebc = ['#57AB27', '#8DC060', '#B8D698']
bordeaux_ebc = ['#A11035', '#B65256', '#CD8B87',]
black_ebc = ['#000000', '#646567', '#9C9E9F', '#CFD1D2']
grey_ebc = ['#4E4F50', '#9D9EA0', '#C4C5C6']


# ------------ PLOTTING CRIT ------------
plot_kpi = "avg price"  # dem, sup, trade
data = "time"  # time or value
plt.figure(figsize=(10, 5))

# ------------------------------ START PLOTTING ------------------------------
if data == "time":
    if plot_kpi == "dem, sup, trade":
        df_head_e_5_dem = df_time_jan_e_5_dem.head(168)  # 168
        df_head_e_5_sup = df_time_jan_e_5_sup.head(168)
        df_head_e_5_trade = df_time_jan_e_5_trade.head(168)
        plt.plot(df_head_e_5_dem["Timestep"], df_head_e_5_dem["Total demand"], color=red_ebc[0], label="Demand")
        plt.plot(df_head_e_5_sup["Timestep"], df_head_e_5_sup["Total supply"], color=blue_ebc[0], label="Supply")
        plt.plot(df_head_e_5_trade["Timestep"], df_head_e_5_trade["Total traded power"], color=green_ebc[0], label="Traded Power")
        plt.xlabel("Timesteps [h]", fontsize=14)  # X-axis label
        plt.ylabel("Power [kW]",fontsize=14)  # Y-axis label
        plt.title(r"Trading within district 3 (January, flex energy, $n_{PH}=n_{B}=5h$)", fontweight="bold", fontsize=16)  # Title of the plot
        plt.legend(fontsize=12)

    elif plot_kpi == "dem, sup, trade 36":
        df_head_e_5_h_dem = df_time_apr_e_5_h_dem.head(168)  # 168
        df_head_e_5_h_sup = df_time_apr_e_5_h_sup.head(168)
        df_head_e_5_h_trade = df_time_apr_e_5_h_trade.head(168)
        plt.plot(df_head_e_5_h_dem["Timestep"], df_head_e_5_h_dem["Total demand"], color=red_ebc[0], label="Demand")
        plt.plot(df_head_e_5_h_sup["Timestep"], df_head_e_5_h_sup["Total supply"], color=blue_ebc[0], label="Supply")
        plt.plot(df_head_e_5_h_trade["Timestep"], df_head_e_5_h_trade["Total traded power"], color=green_ebc[0], label="Traded Power")
        plt.xlabel("Timesteps [h]", fontsize=14)  # X-axis label
        plt.ylabel("Power [kW]",fontsize=14)  # Y-axis label
        plt.title(r"Trading within district 3 (April, flex energy, $n_{PH}=36h$, $n_{B}=5h$)", fontweight="bold", fontsize=16)  # Title of the plot
        plt.legend(fontsize=12)

    elif plot_kpi == "avg price":
        filtered_data = df_time_apr_e_5_price["Average trade price"][df_time_apr_e_5_price["Average trade price"] != 0]
        filtered_data2 = df_time_apr_e_5_h_price["Average trade price"][df_time_apr_e_5_h_price["Average trade price"] != 0]
        data_to_plot = [filtered_data, filtered_data2]
        plt.boxplot(data_to_plot, patch_artist=True, boxprops=dict(facecolor=grey_ebc[0], color=grey_ebc[0]),
                    whiskerprops=dict(color=grey_ebc[0]), capprops=dict(color=grey_ebc[0]), medianprops=dict(color=red_ebc[0]))
        plt.xticks([1, 2], [r'$n_{PH}=n_{B}$', '$n_{PH}=36h$'], fontsize=14)
        plt.title(r"Average trade price for district 3, April, $n_{PH}=5h$", fontsize=16)
        plt.ylabel("Price [€/kWh]", fontsize=14)
        plt.yticks(fontsize=14)

elif data == "value":

    if plot_kpi == "traded power jan":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jan_e_1["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jan_q_1["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(2, val_jan_p_1["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jan_e_1_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jan_q_1_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(6, val_jan_p_1_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jan_e_3["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jan_q_3["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(12, val_jan_p_3["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jan_e_3_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jan_q_3_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(16, val_jan_p_3_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jan_e_5["total_traded_power"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jan_q_5["total_traded_power"], color=blue_ebc[2], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jan_p_5["total_traded_power"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jan_e_5_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jan_q_5_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(26, val_jan_p_5_h["total_traded_power"], color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -600

        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)

        plt.ylabel("Power [kWh]", fontsize=14)
        plt.ylim(0, 4800)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.title("Traded power quantities within district 3 in January", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25], [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                                            r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "traded power apr":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_apr_e_1["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_apr_q_1["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(2, val_apr_p_1["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_apr_e_1_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_apr_q_1_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(6, val_apr_p_1_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_apr_e_3["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_apr_q_3["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(12, val_apr_p_3["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_apr_e_3_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_apr_q_3_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(16, val_apr_p_3_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_apr_e_5["total_traded_power"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_apr_q_5["total_traded_power"], color=blue_ebc[2], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_apr_p_5["total_traded_power"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_apr_e_5_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_apr_q_5_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(26, val_apr_p_5_h["total_traded_power"], color=grey_ebc[1], width=1))

        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -600
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("Power [kWh]", fontsize=14)
        plt.ylim(0, 4800)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.title("Traded power quantities within district 3 in April", fontweight="bold",
                  fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25], [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                                            r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$"], fontsize=12)
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "traded power jul":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jul_e_1["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jul_q_1["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(2, val_jul_p_1["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jul_e_1_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jul_q_1_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(6, val_jul_p_1_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jul_e_3["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jul_q_3["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(12, val_jul_p_3["total_traded_power"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jul_e_3_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jul_q_3_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(16, val_jul_p_3_h["total_traded_power"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jul_e_5["total_traded_power"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jul_q_5["total_traded_power"], color=blue_ebc[2], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jul_p_5["total_traded_power"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jul_e_5_h["total_traded_power"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jul_q_5_h["total_traded_power"], color=blue_ebc[2], width=1))
        bars.append(plt.bar(26, val_jul_p_5_h["total_traded_power"], color=grey_ebc[1], width=1))

        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -650
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("Power [kWh]", fontsize=14)
        plt.ylim(0, 4800)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.title("Traded power quantities within district 3 in July", fontweight="bold",
                  fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25], [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                                            r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$"], fontsize=12)
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "gain_jan":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jan_e_1["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jan_q_1["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_jan_p_1["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jan_e_1_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jan_q_1_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_jan_p_1_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jan_e_3["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jan_q_3["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_jan_p_3["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jan_e_3_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jan_q_3_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_jan_p_3_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jan_e_5["gain"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jan_q_5["gain"], color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jan_p_5["gain"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jan_e_5_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jan_q_5_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_jan_p_5_h["gain"], color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -200
        plt.gca().tick_params(axis='y', labelsize=12)

        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)

        plt.ylabel("Profit [€]",fontsize=14)
        plt.ylim(0, 1700)
        plt.title("Economic gain for district 3 in January", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"],fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "gain_apr":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_apr_e_1["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_apr_q_1["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_apr_p_1["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_apr_e_1_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_apr_q_1_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_apr_p_1_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_apr_e_3["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_apr_q_3["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_apr_p_3["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_apr_e_3_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_apr_q_3_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_apr_p_3_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_apr_e_5["gain"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_apr_q_5["gain"], color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_apr_p_5["gain"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_apr_e_5_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_apr_q_5_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_apr_p_5_h["gain"], color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -200
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("Profit [€]", fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        #plt.ylim(0, 2150)
        plt.title("Economic gain for district 3 in April", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "gain_jul":
        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jul_e_1["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jul_q_1["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_jul_p_1["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jul_e_1_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jul_q_1_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_jul_p_1_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jul_e_3["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jul_q_3["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_jul_p_3["gain"], color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jul_e_3_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jul_q_3_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_jul_p_3_h["gain"], color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jul_e_5["gain"], color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jul_q_5["gain"], color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jul_p_5["gain"], color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jul_e_5_h["gain"], color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jul_q_5_h["gain"], color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_jul_p_5_h["gain"], color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -200
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold",fontsize=12)
        plt.ylabel("Profit [€]",fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        #plt.ylim(0, 2150)
        plt.title("Economic gain for district 3 in July", fontweight="bold",fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"],fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True,fontsize=14)

    elif plot_kpi == "scf_apr":

        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_apr_e_1["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_apr_q_1["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_apr_p_1["scf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_apr_e_1_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_apr_q_1_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_apr_p_1_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_apr_e_3["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_apr_q_3["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_apr_p_3["scf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_apr_e_3_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_apr_q_3_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_apr_p_3_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_apr_e_5["scf_month"]*100, color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_apr_q_5["scf_month"]*100, color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_apr_p_5["scf_month"]*100, color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_apr_e_5_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_apr_q_5_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_apr_p_5_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -10
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("DCF [%]", fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.ylim(0, 100)
        plt.title("SCF for district 3 in April", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "dcf_apr":

        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_apr_e_1["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_apr_q_1["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_apr_p_1["dcf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_apr_e_1_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_apr_q_1_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_apr_p_1_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_apr_e_3["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_apr_q_3["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_apr_p_3["dcf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_apr_e_3_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_apr_q_3_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_apr_p_3_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_apr_e_5["dcf_month"]*100, color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_apr_q_5["dcf_month"]*100, color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_apr_p_5["dcf_month"]*100, color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_apr_e_5_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_apr_q_5_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_apr_p_5_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -10
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("DCF [%]", fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.ylim(0, 100)
        plt.title("DCF for district 3 in April", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "scf_jul":

        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jul_e_1["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jul_q_1["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_jul_p_1["scf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jul_e_1_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jul_q_1_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_jul_p_1_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jul_e_3["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jul_q_3["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_jul_p_3["scf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jul_e_3_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jul_q_3_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_jul_p_3_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jul_e_5["scf_month"]*100, color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jul_q_5["scf_month"]*100, color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jul_p_5["scf_month"]*100, color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jul_e_5_h["scf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jul_q_5_h["scf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_jul_p_5_h["scf_month"]*100, color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -10
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("SCF [%]", fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.ylim(0, 100)
        plt.title("SCF for district 3 in July", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)

    elif plot_kpi == "dcf_jul":

        bars = []
        # ---------- nB=1 ----------
        bars.append(plt.bar(0, val_jul_e_1["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(1, val_jul_q_1["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(2, val_jul_p_1["dcf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(4, val_jul_e_1_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(5, val_jul_q_1_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(6, val_jul_p_1_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=3 ----------
        bars.append(plt.bar(10, val_jul_e_3["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(11, val_jul_q_3["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(12, val_jul_p_3["dcf_month"]*100, color=grey_ebc[1], width=1))

        bars.append(plt.bar(14, val_jul_e_3_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(15, val_jul_q_3_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(16, val_jul_p_3_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # ---------- nB=5 ----------
        bars.append(plt.bar(20, val_jul_e_5["dcf_month"]*100, color=grey_ebc[0], width=1, label="flex energy"))
        bars.append(plt.bar(21, val_jul_q_5["dcf_month"]*100, color=red_ebc[0], width=1, label="mean quantity"))
        bars.append(plt.bar(22, val_jul_p_5["dcf_month"]*100, color=grey_ebc[1], width=1, label="mean price"))

        bars.append(plt.bar(24, val_jul_e_5_h["dcf_month"]*100, color=grey_ebc[0], width=1))
        bars.append(plt.bar(25, val_jul_q_5_h["dcf_month"]*100, color=red_ebc[0], width=1))
        bars.append(plt.bar(26, val_jul_p_5_h["dcf_month"]*100, color=grey_ebc[1], width=1))

        # Iterate over the bars and add the value on top of each bar
        for bar_group in bars:
            for bar in bar_group:
                height = bar.get_height()
                # text = f'{height:.2f}'
                text = f'{int(round(height))}'
                # plt.text(bar.get_x() + bar.get_width() / 2.0, height, text, ha='center', va='bottom')

        # Additional x-axis labels for the groups
        group_labels = [r'$n_{bid}=1h$', r'$n_{bid}=3h$', r'$n_{bid}=5h$']
        group_midpoints = [3, 13, 23]
        y_position = -10
        # Add the group labels below the x-axis
        for midpoint, label in zip(group_midpoints, group_labels):
            plt.text(midpoint, y_position, label, ha='center', va='top', transform=plt.gca().transData,
                     fontweight="bold", fontsize=12)
        plt.ylabel("DCF [%]", fontsize=14)
        plt.gca().tick_params(axis='y', labelsize=12)
        plt.ylim(0, 100)
        plt.title("DCF for district 3 in July", fontweight="bold", fontsize=16)  # Title of the plot
        plt.xticks([1, 5, 11, 15, 21, 25],
                   [r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$", r"$n_{PH}=36h$", r"$n_{PH}=n_{bid}$",
                    r"$n_{PH}=36h$"], fontsize=12)
        # Adjust the plot to make space for the additional labels
        plt.subplots_adjust(bottom=0.25)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=14)





plt.grid(axis='y')
plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/1_Plots/Quartier_3_"+plot_kpi+".svg")
plt.savefig("/Users/lenabmg/Documents/1_RWTH Studium/Masterarbeit/P2P_Market/results/1_Plots/Quartier_3_"+plot_kpi+".png")
plt.show()






