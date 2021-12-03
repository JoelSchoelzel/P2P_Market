

import numpy as np
import matplotlib.pyplot as plt

def compute_district_loads(opti_bes, options, par_rh, n_opt):

    gas_district = np.zeros(len(par_rh["time_steps"]))
    residual_district = np.zeros(len(par_rh["time_steps"]))

    for n_opt in range(par_rh["n_opt"]):
        for t in par_rh["time_steps"][n_opt][0:par_rh["n_hours"] - par_rh["n_hours_ov"]]:
            for n in range(options["nb_bes"]):
                residual_district[n_opt] = residual_district[n_opt] + opti_bes[n_opt][n][4][t] \
                                       - opti_bes[n_opt][n][8]["pv"][t] \
                                       - opti_bes[n_opt][n][8]["chp"][t]

    fig, ax1 = plt.subplots(1, figsize=(11, 6))
    ax1.plot(residual_district[:5*24], color='darkblue', linewidth=1.0, label="Residuallast")
    ax1.set(ylabel='Power in kW')
    ax1.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.3)
    #plt.savefig("residual_power_total_scn_comp", dpi=300, bbox_inches="tight")
    plt.show()