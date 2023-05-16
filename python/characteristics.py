import datetime
import pickle
# calculate characteristics according to Stinner et al.,
# "https://linkinghub.elsevier.com/retrieve/pii/S0306261916311424"


def calc_characs(nodes, options, par_rh):

    EHG = ["hp35", "hp55", "chp", "bz"]
    heaters = ["hp35", "hp55", "chp", "bz", "boiler"]

    characs = {}
    for n in range(options["nb_bes"]):
        characs[n] = {
            "alpha_th": {},
            "beta_th": {},
            "alpha_el_flex_forced": {},
            "alpha_el_flex_delayed": {},
            "beta_el_forced": {},
            "beta_el_delayed": {},
            "tau_forced": {},
            "tau_delayed": {},
            "power_flex_forced": {},
            "power_flex_delayed": {},
            "power_avg_forced": {},
            "power_avg_delayed": {},
            "power_cycle_forced": {},
            "power_cycle_delayed": {},
            "energy_forced": {},
            "energy_delayed": {},
        }

        ### heat

        #alpha_th
        # nominal heat production
        dQ_EHG_nom = sum(nodes[n]["devs"][dev]["cap"] for dev in heaters)

        # nominal heat load as maximum average per hour
        dQ_build_nom = max(
            nodes[n]["heat"][n_opt] + (0.5 * nodes[n]["dhw"][n_opt]) for n_opt in range(par_rh["n_opt"]))

        alpha_th = dQ_EHG_nom / dQ_build_nom
        characs[n]["alpha_th"] = alpha_th

        # beta_th
        # storage capacity
        Q_stor_avg = nodes[n]["devs"]["tes"]["cap"]

        # space heating
        Q_SH = sum(nodes[n]["heat"][n_opt] for n_opt in range(par_rh["n_opt"]))

        # DHW
        Q_DHW = sum(nodes[n]["dhw"][n_opt] for n_opt in range(par_rh["n_opt"]))

        n_hours = par_rh["n_opt"]

        beta_th = Q_stor_avg * n_hours / (Q_SH + Q_DHW)
        characs[n]["beta_th"] = beta_th


        ### elec

        # maximum power that can be generated
        power_max = nodes[n]["devs"]["chp"]["cap"] * nodes[n]["devs"]["chp"]["eta_th"]

        # minimum power that can be generated
        power_min = 0

        # nominal heat load, half of DHW is covered by EH already
        dQ_build_nom = max(nodes[n]["heat"][n_opt] + (0.5 * nodes[n]["dhw"][n_opt]) for n_opt in range(par_rh["n_opt"]))

        for n_opt in range(par_rh["n_opt"]):

            ### temporal flexibility

            # forced flexibility, time until TES is fully charged with maximum charging
            # TES assumed to be fully discharged at beginning
            charge = 0
            tau_forced = 0
            while charge < nodes[n]["devs"]["tes"]["cap"]:
                if sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) == 0:
                    break
                max_charging = sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) - nodes[n]["heat"][n_opt + tau_forced] - (0.5 * nodes[n]["dhw"][n_opt + tau_forced])
                if charge + max_charging <= nodes[n]["devs"]["tes"]["cap"]:
                    charge += max_charging
                    tau_forced += 1
                else:
                    tau_forced += (nodes[n]["devs"]["tes"]["cap"] - charge) / max_charging
                    charge = nodes[n]["devs"]["tes"]["cap"]
                # check whether end of data is reached
                if n_opt + tau_forced >= par_rh["n_opt"]:
                    break

            characs[n]["tau_forced"][n_opt] = tau_forced

            # delayed flexibility, time until TES is fully discharged with no charging

            # check whether TES can be fully charged during preceding time steps
            # max heat production must be greater than heat demand in every considered timestep to be sure
            charge = nodes[n]["devs"]["tes"]["cap"]
            fully_charged = True
            for i in range(5):
                if (sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][n_opt - i] - (0.5 * nodes[n]["dhw"][n_opt - i])) < 0:
                    fully_charged = False
            charge = nodes[n]["devs"]["tes"]["cap"]
            if not fully_charged:
                for i in range(5):
                    charge += sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][n_opt - i] - (0.5 * nodes[n]["dhw"][n_opt - i])
                    if charge < 0:
                        charge = 0

            tau_delayed = 0
            while charge > 0:
                discharging = nodes[n]["heat"][n_opt + tau_delayed] + (0.5 * nodes[n]["dhw"][n_opt + tau_delayed])
                if charge - discharging > 0:
                    charge -= discharging
                    tau_delayed += 1
                else:
                    tau_delayed += charge / discharging
                    charge = 0
                # check whether end of data is reached
                if n_opt + tau_delayed >= par_rh["n_opt"]:
                    break

            characs[n]["tau_delayed"][n_opt] = tau_delayed

            ### power flexibility

            # reference case: power required without use of flexibility
            # elec + heatpumps
            if nodes[n]["devs"]["hp35"]["cap"] > 0:
                power_ref = nodes[n]["elec"][n_opt] + nodes[n]["heat"][n_opt] / nodes[n]["devs"]["COP_sh35"][n_opt]
            elif nodes[n]["devs"]["hp55"]["cap"] > 0:
                power_ref = nodes[n]["elec"][n_opt] + nodes[n]["heat"][n_opt] / nodes[n]["devs"]["COP_sh55"][n_opt]
            else:
                power_ref = nodes[n]["elec"][n_opt]

            # power flexibility, difference between reference case and max/min
            if power_max > 0:
                power_flex_forced = power_max - power_ref
            else:
                power_flex_forced = 0
            power_flex_delayed = power_ref - power_min

            # alpha_el_flex
            alpha_el_flex_forced = power_flex_forced / dQ_build_nom
            alpha_el_flex_delayed = power_flex_delayed / dQ_build_nom

            characs[n]["power_flex_forced"][n_opt] = power_flex_forced
            characs[n]["power_flex_delayed"][n_opt] = power_flex_delayed
            characs[n]["alpha_el_flex_forced"][n_opt] = alpha_el_flex_forced
            characs[n]["alpha_el_flex_delayed"][n_opt] = alpha_el_flex_delayed

        print("Part 1 finished.")

        for n_opt in range(par_rh["n_opt"]):

            # average and cycle power flexibility
            energy_forced = 0
            i = 0
            while i < characs[n]["tau_forced"][n_opt] - 1:
                energy_forced += characs[n]["power_flex_forced"][n_opt + i]
                i += 1
                # check whether end of data is reached
                if n_opt + i >= par_rh["n_opt"]-1:
                    break
            energy_forced += characs[n]["power_flex_forced"][n_opt + i] * (characs[n]["tau_forced"][n_opt] - i)
            # check whether cycle is within data, otherwise tau_delayed of n_opt instead of (n_opt + tau_forced) is used
            if n_opt + int(characs[n]["tau_forced"][n_opt]) < par_rh["n_opt"]:
                power_cycle_forced = energy_forced / (characs[n]["tau_forced"][n_opt] + characs[n]["tau_delayed"][n_opt + int(characs[n]["tau_forced"][n_opt])])
            else:
                power_cycle_forced = energy_forced / (characs[n]["tau_forced"][n_opt] + characs[n]["tau_delayed"][n_opt])
            power_avg_forced = energy_forced / characs[n]["tau_forced"][n_opt]

            energy_delayed = 0
            i = 0
            while i < characs[n]["tau_delayed"][n_opt] - 1:
                energy_delayed += characs[n]["power_flex_delayed"][n_opt + i]
                i += 1
                # check whether end of data is reached
                if n_opt + i >= par_rh["n_opt"] - 1:
                    break
            energy_delayed += characs[n]["power_flex_delayed"][n_opt + i] * (characs[n]["tau_delayed"][n_opt] - i)
            # check whether cycle is within data, otherwise tau_forced of n_opt instead of (n_opt + tau_delayed) is used
            if n_opt + int(characs[n]["tau_delayed"][n_opt]) < par_rh["n_opt"]:
                power_cycle_delayed = energy_delayed / (characs[n]["tau_delayed"][n_opt] + characs[n]["tau_forced"][n_opt + int(characs[n]["tau_delayed"][n_opt])])
            else:
                power_cycle_delayed = energy_delayed / (characs[n]["tau_delayed"][n_opt] + characs[n]["tau_forced"][n_opt])
            power_avg_delayed = energy_delayed / characs[n]["tau_delayed"][n_opt]

            characs[n]["power_avg_forced"][n_opt] = power_avg_forced
            characs[n]["power_avg_delayed"][n_opt] = power_avg_delayed
            characs[n]["power_cycle_delayed"][n_opt] = power_cycle_delayed
            characs[n]["power_cycle_forced"][n_opt] = power_cycle_forced
            characs[n]["energy_forced"][n_opt] = energy_forced
            characs[n]["energy_delayed"][n_opt] = energy_delayed

            Q_SH = sum(nodes[n]["heat"][n_opt] for n_opt in range(par_rh["n_opt"]))
            Q_DHW = sum(nodes[n]["dhw"][n_opt] for n_opt in range(par_rh["n_opt"]))
            beta_el_forced = energy_forced * par_rh["n_opt"] / (Q_SH + Q_DHW)
            beta_el_delayed = energy_delayed * par_rh["n_opt"] / (Q_SH + Q_DHW)

            characs[n]["beta_el_forced"][n_opt] = beta_el_forced
            characs[n]["beta_el_delayed"][n_opt] = beta_el_delayed

            print("Finished building: " + str(n) + ", n_opt: " + str(n_opt) + ".")

        print("Building " + str(n) + " finished.")

    #with open(options["path_results"] + "/P2P_characteristics/" + datetime.datetime.now().strftime("%m-%d-%H-%M") + ".p",
    #          'wb') as fp: pickle.dump(characs, fp)

    return characs
