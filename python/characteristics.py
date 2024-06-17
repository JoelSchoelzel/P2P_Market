import datetime
import pickle
import math
import numpy as np


def calc_characs(nodes, options, par_rh, block_length, opti_res: dict = None, start_step: int = None): #length: int = 3
    """
    Calculate KPIs to evaluate different flexibilities of each building according to Stinner et al.

    If an optimization result is provided, the SOC of the result is used. Otherwise an empty storage is assumed for

    Args:
        nodes (dict):
        options (dict):
        par_rh (dict):
        opti_res: optimization result to get SOC, if not provided a empty/full SOC is assumed
        start_step: starting optimization step for which flexibility characs are calculated,
            if not provided all optimization steps are calculated
        block_length: amount of optimization steps to be calculated, only relevant when start_step is provided

    Returns:
        characs (dict): Dictionary containing the following KPIs:
            "alpha_th": thermal capacity
            "beta_th": TES capacity
            "alpha_el_flex_forced": normalized power_flex_forced
            "alpha_el_flex_delayed": normalized power_flex_delayed
            "beta_el_forced": normalized energy_forced
            "beta_el_delayed": normalized energy_delayed
            "tau_forced": time to charge TES
            "tau_delayed": time to discharge TES
            "power_flex_forced": power flexibility as difference between reference case and max power generation
            "power_flex_delayed": power flexibility as difference between reference case and min power generation
            "power_avg_forced": forced power flexibility averaged over tau_forced
            "power_avg_delayed": delayed power flexibility averaged over tau_delayed
            "power_cycle_forced": forced power flexibility averaged over tau_forced + tau_delayed (full cycle)
            "power_cycle_delayed": forced power flexibility averaged over tau_delayed + tau_forced (full cycle)
            "energy_forced": energy the TES can be charged with
            "energy_delayed": energy the TES can be discharged by
    """


    # list of all heaters that use/produce electricity
    EHG = ["hp35", "hp55", "chp", "bz"]

    # list of all heaters
    heaters = ["hp35", "hp55", "chp", "bz", "boiler"]

    # list of energy storages
    storages = ["tes", "bat"]
    soc_opti = {}
    soc = {}
    for dev in storages:
        soc_opti[dev] = []

    # set step params
    if start_step is not None:
        start_hour = par_rh["hour_start"][start_step]
        # when a start step is provided, start and block_length is used:
        max_step = start_hour + par_rh["n_hours"]  # set the starting step + 36 hours as the maximum step
        data_steps = list(range(start_hour, max_step))  # use the data for 36 hours (optimization horizon)
        block_bids_steps = list(
            range(start_hour, start_hour + block_length))  # only calculate results for the specified steps
    else:
        # when no start step is provided, all steps in par_rh are used
        max_step = par_rh["n_opt"]  # maximum step is end of data
        data_steps = list(range(par_rh["n_opt"]))  # use data of all steps
        block_bids_steps = list(range(par_rh["n_opt"]))  # calculate results for all steps


    # create dict to store the characs in
    characs = {}
    for n in range(options["nb_bes"]):
        characs[n] = {
            "alpha_th": {},
            "beta_th": {},
            "alpha_el_flex_forced": {},
            "alpha_el_flex_delayed": {},
            "beta_el_forced": {},
            "beta_el_delayed": {},
            "tau_forced_heat": {},
            "tau_delayed_heat": {},
            "tau_forced_bat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "tau_delayed_bat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "power_flex_forced_heat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "power_flex_delayed_heat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "power_flex_forced_bat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "power_flex_delayed_bat": {start_hour + i: elem for i, elem in enumerate(range(36))},
            "power_avg_forced_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_avg_delayed_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_cycle_forced_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_cycle_delayed_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "energy_forced_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "energy_delayed_heat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_avg_forced_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_avg_delayed_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_cycle_forced_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "power_cycle_delayed_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "energy_forced_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},
            "energy_delayed_bat": {start_hour + i: elem for i, elem in enumerate(range(len(block_bids_steps)))},

            "power_bid_avg_forced_heat": {},
            "power_bid_avg_delayed_heat": {},
            "energy_bid_avg_forced_heat": {},
            "energy_bid_avg_delayed_heat": {},
            "power_bid_avg_forced_bat": {},
            "power_bid_avg_delayed_bat": {},
            "energy_bid_avg_forced_bat": {},
            "energy_bid_avg_delayed_bat": {},

        }

        for dev in storages:
            if opti_res is not None:
                # use the SOC from optimization results if provided
                soc_opti[dev] = {step: opti_res[start_step][n][3][dev][step] for step in data_steps}
            else:
                # set to None if optimization results are not provided
                soc_opti[dev] = None

        ## Check if the heater is a boiler and set all characteristics to zero since there is no flexibility
        # todo boiler + BAT
        #if nodes[n]["devs"]["boiler"]["cap"] > 0:
        #    for key in ["alpha_th", "beta_th"]:
        #        characs[n][key] = 0
        #    for key in ["tau_forced", "tau_delayed", "power_flex_forced", "power_flex_delayed", "power_avg_forced",
        #                "power_avg_delayed", "power_cycle_forced", "power_cycle_delayed", "energy_forced",
        #                "energy_delayed", "alpha_el_flex_forced", "alpha_el_flex_delayed", "beta_el_forced", "beta_el_delayed"]:
        #        for time_step in block_bids_steps:
        #                characs[n][key][time_step] = 0

        #    continue  # Skip further calculations for this heater


        ### --------------------- heat --------------------- ###

        # alpha_th
        # nominal heat production
        dQ_EHG_nom = sum(nodes[n]["devs"][dev]["cap"] for dev in heaters)

        # nominal heat load as maximum average per hour
        dQ_build_nom = max(
            nodes[n]["heat"][n_opt] + (0.5 * nodes[n]["dhw"][n_opt]) for n_opt in range(par_rh["n_opt"]))

        # calculate alpha_th
        alpha_th = dQ_EHG_nom / dQ_build_nom
        characs[n]["alpha_th"] = alpha_th

        # beta_th
        # storage capacity
        Q_stor_avg = nodes[n]["devs"]["tes"]["cap"]

        # space heating
        Q_SH = sum(nodes[n]["heat"][n_opt] for n_opt in range(par_rh["n_opt"]))

        # DHW (domestic hot water)
        Q_DHW = sum(nodes[n]["dhw"][n_opt] for n_opt in range(par_rh["n_opt"]))

        n_hours = par_rh["n_opt"]

        # calculate beta_th
        beta_th = Q_stor_avg * n_hours / (Q_SH + Q_DHW)
        characs[n]["beta_th"] = beta_th


        ### --------------------- elec --------------------- ###

        # calculate temporal and power flexibility for all data steps
        for t in data_steps:

            ### -------------- temporal flexibility -------------- ###
            # forced flexibility, time until TES is fully charged with maximum charging
            for dev in storages:
                if soc_opti[dev] is not None:
                    # use SOC from optimization results when provided
                    soc[dev] = soc_opti[dev][t]
                else:
                    # TES assumed to be fully discharged at beginning if no SOC is provided
                    soc[dev] = 0
            print(soc)

            ### -------------- tes -------------- ###
            # tau_forced: time it takes to charge
            tau_forced_heat = 0
            # loop until the TES is fully charged
            while soc["tes"] < nodes[n]["devs"]["tes"]["cap"]:
                # check whether there are any heaters, break otherwise
                if sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) == 0:
                    break
                # maximal charging is difference between capacity of heaters and heat demand at (n_opt + tau_forced)
                max_charging = sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) \
                               - nodes[n]["heat"][t + tau_forced_heat] \
                               - (0.5 * nodes[n]["dhw"][t + tau_forced_heat])
                # check whether the TES can be charged by maximal charging without exceeding the capacity
                if soc["tes"] + max_charging <= nodes[n]["devs"]["tes"]["cap"]:
                    # max_charging is added and tau_forced incremented by an hour
                    soc["tes"] += max_charging
                    tau_forced_heat += 1
                # in case maximal charging would exceed the capacity:
                else:
                    # tau_forced is incremented by the fraction of the hour that charging is still possible
                    # constant rate of charging is assumed during the hour
                    tau_forced_heat += (nodes[n]["devs"]["tes"]["cap"] - soc["tes"]) / max_charging
                    # soc is set to the capacity
                    # TODO: why?
                    soc["tes"] = nodes[n]["devs"]["tes"]["cap"]
                # check whether end of data is reached
                if t + tau_forced_heat >= max_step:
                    break

            characs[n]["tau_forced_heat"][t] = tau_forced_heat

            ### -------------- BAT -------------- ###
            # tau_forced: time it takes to charge
            tau_forced_bat = 0
            # loop until the BAT is fully charged
            while soc["bat"] < nodes[n]["devs"]["bat"]["cap"]:
                # check whether there is a battery, break otherwise
                if nodes[n]["devs"]["bat"]["cap"] == 0:
                    print("check1")
                    break
                # maximal charging of bat
                max_charging = nodes[n]["devs"]["bat"]["cap"] * nodes[n]["devs"]["bat"]["max_ch"]
                # check whether the BAT can be charged by maximal charging without exceeding the capacity
                if soc["bat"] + max_charging <= nodes[n]["devs"]["bat"]["cap"]:
                    print("check2")
                    # max_charging is added and tau_forced incremented by an hour
                    soc["bat"] += max_charging
                    tau_forced_bat += 1
                # in case maximal charging would exceed the capacity:
                else:
                    print("check3")
                    # tau_forced is incremented by the fraction of the hour that charging is still possible
                    # constant rate of charging is assumed during the hour
                    tau_forced_bat += (nodes[n]["devs"]["bat"]["cap"] - soc["bat"]) / max_charging
                    # soc is set to the capacity
                    # TODO: why?
                    soc["bat"] = nodes[n]["devs"]["bat"]["cap"]
                # check whether end of data is reached
                if t + tau_forced_bat >= max_step:
                    print("check4")
                    break

            characs[n]["tau_forced_bat"][t] = tau_forced_bat
            print("check5")

        for t in data_steps:

            # delayed flexibility, time until ### -------------- tes -------------- ### is fully discharged with no charging

            if soc_opti["tes"] is not None:
                # use SOC from optimization results when provided
                soc["tes"] = soc_opti["tes"][t]
            else:
                # todo: why?
                # when SOC is not provided
                # check whether TES can be fully charged during preceding time steps
                # max heat production must be greater than heat demand in every considered timestep to be sure
                fully_charged = True
                # iterate through last few hours
                for i in range(24):
                    # set fully_charged to False if demand was greater the capacity of heaters
                    if (sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][t - i] - (0.5 * nodes[n]["dhw"][t - i])) < 0:
                        fully_charged = False
                soc["tes"] = nodes[n]["devs"]["tes"]["cap"]
                # determine the maximum possible charge when demand was greater than max production at any point
                if not fully_charged:
                    # iterate through last few hours
                    for i in range(24):
                        # add maximum charging (difference between capacity of heaters and heat demand) to charge
                        soc["tes"] += sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][t - i] - (0.5 * nodes[n]["dhw"][t - i])
                        # make sure soc stays between the maximum and minimum value (between capacity and 0)
                        if soc["tes"] >= nodes[n]["devs"]["tes"]["cap"]:
                            soc["tes"] = nodes[n]["devs"]["tes"]["cap"]
                        elif soc["tes"] < 0:
                            soc["tes"] = 0
            """
            for dev in storages:
                if soc_opti[dev] is not None:
                    # use SOC from optimization results when provided
                    soc2[dev] = soc_opti[dev][n_opt]
            """

            # tau_delayed: time it takes to discharge
            tau_delayed_heat = 0
            # loop until the storage is fully discharged
            while soc["tes"] > 0:
                # maximum discharging is the heat demand at (n_opt + tau_delayed)
                discharging = nodes[n]["heat"][t + tau_delayed_heat] + (0.5 * nodes[n]["dhw"][t + tau_delayed_heat])
                # check whether there's enough soc remaining for maximum discharging
                if soc["tes"] - discharging > 0:
                    # discharge is subtracted and tau_delayed incremented by an hour
                    soc["tes"] -= discharging
                    tau_delayed_heat += 1
                # in case not enough charge is remaining:
                else:
                    # tau_delayed is incremented by the fraction of the hour that discharging is still possible
                    # constant rate of discharging is assumed during the hour
                    tau_delayed_heat += soc["tes"] / discharging
                    soc["tes"] = 0
                # check whether end of data is reached
                if t + tau_delayed_heat >= max_step:
                    break

            characs[n]["tau_delayed_heat"][t] = tau_delayed_heat

            # delayed flexibility, time until ### -------------- BAT -------------- ### is fully discharged with no charging

            if soc_opti["bat"] is not None:
                # use SOC from optimization results when provided
                soc["bat"] = soc_opti["bat"][t]
            else:
                # todo: why?
                # when SOC is not provided
                # check whether TES can be fully charged during preceding time steps
                # max heat production must be greater than heat demand in every considered timestep to be sure
                fully_charged = True
                # iterate through last few hours
                for i in range(24):
                    # set fully_charged to False if demand was greater the capacity of heaters
                    if (sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][t - i] - (0.5 * nodes[n]["dhw"][t - i])) < 0:
                        fully_charged = False
                soc["bat"] = nodes[n]["devs"]["bat"]["cap"]
                # determine the maximum possible charge when demand was greater than max production at any point
                if not fully_charged:
                    # iterate through last few hours
                    for i in range(24):
                        # add maximum charging (difference between capacity of heaters and heat demand) to charge
                        soc["bat"] += sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][t - i] - (0.5 * nodes[n]["dhw"][t - i])
                        # make sure soc stays between the maximum and minimum value (between capacity and 0)
                        if soc["bat"] >= nodes[n]["devs"]["bat"]["cap"]:
                            soc["bat"] = nodes[n]["devs"]["bat"]["cap"]
                        elif soc["bat"] < 0:
                            soc["bat"] = 0

            # tau_delayed: time it takes to discharge
            tau_delayed_bat = 0
            # loop until the storage is fully discharged
            while soc["bat"] > 0:
                # maximum discharging of bat
                discharging = nodes[n]["devs"]["bat"]["cap"] * nodes[n]["devs"]["bat"]["max_dch"]
                # check whether there's enough soc remaining for maximum discharging
                if soc["bat"] - discharging > 0:
                    # discharge is subtracted and tau_delayed incremented by an hour
                    soc["bat"] -= discharging
                    tau_delayed_bat += 1
                # in case not enough charge is remaining:
                else:
                    # tau_delayed is incremented by the fraction of the hour that discharging is still possible
                    # constant rate of discharging is assumed during the hour
                    tau_delayed_bat += soc["bat"] / discharging
                    soc["bat"] = 0
                # check whether end of data is reached
                if t + tau_delayed_bat >= max_step:
                    break

            characs[n]["tau_delayed_bat"][t] = tau_delayed_bat
            ### -------------- temporal flexibility -------------- ###

        power_ref_heat = {}
        power_ref_bat = {}
        power_flex_forced_heat = {}
        power_flex_delayed_heat = {}
        power_flex_forced_bat = {}
        power_flex_delayed_bat = {}
        for t in data_steps:
            ### -------------- power flexibility -------------- ###
            # reference case: power required without use of flexibility
            # elec + power used by heatpumps
            # Todo: elec und pv nicht rein!? sind ja nicht flexibel
            # todo: chp ref case für chp + eh rein
            if nodes[n]["devs"]["hp35"]["cap"] > 0:
                power_ref_heat[t] = opti_res[start_step][n][1]["hp35"][t]
            elif nodes[n]["devs"]["hp55"]["cap"] > 0:
                power_ref_heat[t] = opti_res[start_step][n][1]["hp55"][t]
            else:
                power_ref_heat[t] = opti_res[start_step][n][1]["chp"][t]

            # flexibility definition for BAT (considering effect to grid): charging = negative, dch = positive (like HP/EH)

            if opti_res[start_step][n][5]["bat"][t] > 0:
                power_ref_bat[t] = opti_res[start_step][n][5]["bat"][t]
            elif opti_res[start_step][n][6]["bat"][t] > 0:
                power_ref_bat[t] = opti_res[start_step][n][6]["bat"][t]

            # maximum power that can be used/generated
            if nodes[n]["devs"]["hp35"]["cap"] > 0:
                power_max_heat = nodes[n]["devs"]["hp35"]["cap"] * nodes[n]["devs"]["COP_sh35"][t] + (60 - 35) / (60 - 25) * nodes[n]["dhw"][t]
            elif nodes[n]["devs"]["hp55"]["cap"] > 0:
                power_max_heat = nodes[n]["devs"]["hp55"]["cap"] * nodes[n]["devs"]["COP_sh55"][t] + (60 - 55) / (60 - 25) * nodes[n]["dhw"][t]
            else:
                power_max_heat = nodes[n]["devs"]["chp"]["cap"] / nodes[n]["devs"]["chp"]["eta_th"] * nodes[n]["devs"]["chp"]["eta_el"]

            # minimum power that can be used/generated
            power_min_heat = 0
            # power flexibility as difference between reference case and max/min power generation
            if power_max_heat > 0:
                power_flex_forced_heat[t] = power_max_heat - power_ref_heat[t]
            else:
                power_flex_forced_heat[t] = 0
            power_flex_delayed_heat[t] = power_ref_heat[t] - power_min_heat

            power_max_bat = nodes[n]["devs"]["bat"]["cap"] * nodes[n]["devs"]["bat"]["max_ch"]
            if opti_res[start_step][n][5]["bat"][t] >= 0:
                power_flex_forced_bat[t] = power_max_bat - opti_res[start_step][n][5]["bat"][t]
                power_flex_delayed_bat[t] = power_max_bat + opti_res[start_step][n][5]["bat"][t]
            elif opti_res[start_step][n][6]["bat"][t] > 0:
                power_flex_forced_bat[t] = power_max_bat + opti_res[start_step][n][6]["bat"][t]
                power_flex_delayed_bat[t] = power_max_bat - opti_res[start_step][n][6]["bat"][t]

            # alpha_el_flex
            #alpha_el_flex_forced = power_flex_forced / dQ_build_nom
            #alpha_el_flex_delayed = power_flex_delayed / dQ_build_nom

            # store the calculated characs
            characs[n]["power_flex_forced_heat"][t] = power_flex_forced_heat[t]
            characs[n]["power_flex_delayed_heat"][t] = power_flex_delayed_heat[t]
            characs[n]["power_flex_forced_bat"][t] = power_flex_forced_bat[t]
            characs[n]["power_flex_delayed_bat"][t] = power_flex_delayed_bat[t]
            #characs[n]["alpha_el_flex_forced"][n_opt] = alpha_el_flex_forced
            #characs[n]["alpha_el_flex_delayed"][n_opt] = alpha_el_flex_delayed

            ### -------------- power flexibility -------------- ###

        print("Part 1 finished.")

        # ---- for heat ---- #
        power_avg_forced_heat = {}
        power_avg_delayed_heat = {}
        power_cycle_delayed_heat = {}
        power_cycle_forced_heat = {}
        energy_forced_heat = {}
        energy_delayed_heat = {}
        # calculate average and cycle power as well as energy flexibility for steps within block bid only
        for t_bid in block_bids_steps:

            # average and cycle power flexibility
            energy_forced_heat[t_bid] = 0  # energy that can the TES can be charged with
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_forced
            while i < characs[n]["tau_forced_heat"][t_bid] - 1:
                # add the energy that can be charged during that hour (power equals energy due to duration of 1 hour)
                energy_forced_heat[t_bid] += characs[n]["power_flex_forced_heat"][t_bid + i]
                i += 1
                # check whether end of data is reached
                if t_bid + i >= max_step-1:
                    break
            # add the energy charged during the remaining fraction of an hour, time is described by (tau_forced - i)
            energy_forced_heat[t_bid] += characs[n]["power_flex_forced_heat"][t_bid + i] * (characs[n]["tau_forced_heat"][t_bid] - i)

            # cycle describes time frame of first charging and then discharging the storage afterwards and vice versa
            # check whether data for the whole cycle exists, n_opt + tau_forced must be within n_opts of the simulation
            if t_bid + int(characs[n]["tau_forced_heat"][t_bid]) < max_step:
                # power_cycle_forced is the forced energy divided by the duration of the cycle
                # time of the cycle is sum of tau_forced at n_opt and tau_delayed at (n_opt + tau_forced)
                try:
                    power_cycle_forced_heat[t_bid] = energy_forced_heat[t_bid] / (characs[n]["tau_forced_heat"][t_bid] +
                                                          characs[n]["tau_delayed_heat"][t_bid +
                                                          int(characs[n]["tau_forced_heat"][t_bid])])
                    if math.isnan(power_cycle_forced_heat[t_bid]):
                        power_cycle_forced_heat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_forced_heat[t_bid] = 0
            # if tau_delayed at (n_opt + tau_forced) doesn't exist because it exceeds the data,
            # tau_delayed at n_opt instead of (n_opt + tau_forced) is used
            else:
                try:
                    power_cycle_forced_heat[t_bid] = energy_forced_heat[t_bid] / (characs[n]["tau_forced_heat"][t_bid] +
                                                          characs[n]["tau_delayed_heat"][t_bid])
                    if math.isnan(power_cycle_forced_heat[t_bid]):
                        power_cycle_forced_heat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_forced_heat[t_bid] = 0

            # power_average_forced is charged energy (energy_forced) divided by duration of charging (tau_forced)
            # check whether tau_forced > 0 to avoid division by zero
            if characs[n]["tau_forced_heat"][t_bid] > 0:
                power_avg_forced_heat[t_bid] = energy_forced_heat[t_bid] / characs[n]["tau_forced_heat"][t_bid]
            else:
                power_avg_forced_heat[t_bid] = 0

            energy_delayed_heat[t_bid] = 0  # energy that can be discharged by the TES
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_delayed
            while i < characs[n]["tau_delayed_heat"][t_bid] - 1:
                # add the energy that can be discharged during that hour (power equals energy due to duration of 1 hour)
                energy_delayed_heat[t_bid] += characs[n]["power_flex_delayed_heat"][t_bid + i]
                i += 1
                # check whether end of data is reached
                if t_bid + i >= max_step - 1:
                    break
            # add the energy discharged during the remaining fraction of an hour, time is described by (tau_delayed - i)
            energy_delayed_heat[t_bid] += characs[n]["power_flex_delayed_heat"][t_bid + i] * (characs[n]["tau_delayed_heat"][t_bid] - i)
            # check whether data for the whole cycle exists, n_opt + tau_delayed must be within n_opts of the simulation
            if t_bid + int(characs[n]["tau_delayed_heat"][t_bid]) < max_step:
                # power_cycle_delayed is the delayed energy divided by the duration of the cycle
                # time of the cycle is sum of tau_delayed at n_opt and tau_forced at (n_opt + tau_delayed)
                try:
                    power_cycle_delayed_heat[t_bid] = energy_delayed_heat[t_bid] / (characs[n]["tau_delayed_heat"][t_bid] +
                                                                        characs[n]["tau_forced_heat"][t_bid +
                                                                        int(characs[n]["tau_delayed_heat"][t_bid])])
                    if math.isnan(power_cycle_delayed_heat[t_bid]):
                        power_cycle_delayed_heat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_delayed_heat[t_bid] = 0
            # if tau_forced at (n_opt + tau_delayed) doesn't exist because it exceeds the data,
            # tau_forced at n_opt instead of (n_opt + tau_delayed) is used
            else:
                try:
                    power_cycle_delayed_heat[t_bid] = energy_delayed_heat[t_bid] / (characs[n]["tau_delayed_heat"][t_bid] +
                                                                    characs[n]["tau_forced_heat"][t_bid])
                except ZeroDivisionError:
                    power_cycle_delayed_heat[t_bid] = 0
                    if math.isnan(power_cycle_delayed_heat[t_bid]):
                        power_cycle_delayed_heat[t_bid] = 0
            # power_avg_delayed is discharged energy (energy_delayed) divided by duration of discharging (tau_delayed)
            try:
                power_avg_delayed_heat[t_bid] = energy_delayed_heat[t_bid] / characs[n]["tau_delayed_heat"][t_bid]
            except ZeroDivisionError:
                power_avg_delayed_heat[t_bid] = 0
                if math.isnan(power_avg_delayed_heat[t_bid]):
                    power_avg_delayed_heat[t_bid] = 0

            # store all the calculated characs
            #characs[n]["power_avg_forced_heat"][t_bid] = power_avg_forced_heat[t_bid]
            #characs[n]["power_avg_delayed_heat"][t_bid] = power_avg_delayed_heat[t_bid]
            #characs[n]["power_cycle_delayed_heat"][t_bid] = power_cycle_delayed_heat[t_bid]
            #characs[n]["power_cycle_forced_heat"][t_bid] = power_cycle_forced_heat[t_bid]
            characs[n]["energy_forced_heat"][t_bid] = energy_forced_heat[t_bid]
            characs[n]["energy_delayed_heat"][t_bid] = energy_delayed_heat[t_bid]

        #characs[n]["power_bid_avg_forced_heat"] = np.mean(np.array(list(characs[n]["power_avg_forced_heat"].values())))
        #characs[n]["power_bid_avg_delayed_heat"] = np.mean(np.array(list(characs[n]["power_avg_delayed_heat"].values())))
        characs[n]["energy_bid_avg_forced_heat"] = np.mean(np.array(list(characs[n]["energy_forced_heat"].values())))
        characs[n]["energy_bid_avg_delayed_heat"] = np.mean(np.array(list(characs[n]["energy_delayed_heat"].values())))

            #beta_el_forced = energy_forced * par_rh["n_opt"] / (Q_SH + Q_DHW)
            #beta_el_delayed = energy_delayed * par_rh["n_opt"] / (Q_SH + Q_DHW)
            #characs[n]["beta_el_forced"][t_bid] = beta_el_forced
            #characs[n]["beta_el_delayed"][t_bid] = beta_el_delayed

        # ---- for bat ---- #
        power_avg_forced_bat = {}
        power_avg_delayed_bat = {}
        power_cycle_delayed_bat = {}
        power_cycle_forced_bat = {}
        energy_forced_bat = {}
        energy_delayed_bat = {}
        # calculate average and cycle power as well as energy flexibility for steps within block bid only
        for t_bid in block_bids_steps:

            # average and cycle power flexibility
            energy_forced_bat[t_bid] = 0  # energy that can the TES can be charged with
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_forced
            while i < characs[n]["tau_forced_bat"][t_bid] - 1:
                # add the energy that can be charged during that hour (power equals energy due to duration of 1 hour)
                # todo: dt ergänzen
                energy_forced_bat[t_bid] += characs[n]["power_flex_forced_bat"][t_bid + i]
                i += 1
                # check whether end of data is reached
                if t_bid + i >= max_step - 1:
                    break
            # add the energy charged during the remaining fraction of an hour, time is described by (tau_forced - i)
            energy_forced_bat[t_bid] += characs[n]["power_flex_forced_bat"][t_bid + i] * (
                            characs[n]["tau_forced_bat"][t_bid] - i)

            # cycle describes time frame of first charging and then discharging the storage afterwards and vice versa
            # check whether data for the whole cycle exists, n_opt + tau_forced must be within n_opts of the simulation
            if t_bid + int(characs[n]["tau_forced_bat"][t_bid]) < max_step:
                # power_cycle_forced is the forced energy divided by the duration of the cycle
                # time of the cycle is sum of tau_forced at n_opt and tau_delayed at (n_opt + tau_forced)
                try:
                    power_cycle_forced_bat[t_bid] = energy_forced_bat[t_bid] / (characs[n]["tau_forced_bat"][t_bid] +
                                                                        characs[n]["tau_delayed_bat"][t_bid +
                                                                        int(characs[n]["tau_forced_bat"][t_bid])])
                    if math.isnan(power_cycle_forced_bat[t_bid]):
                        power_cycle_forced_bat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_forced_bat[t_bid] = 0
            # if tau_delayed at (n_opt + tau_forced) doesn't exist because it exceeds the data,
            # tau_delayed at n_opt instead of (n_opt + tau_forced) is used
            else:
                try:
                    power_cycle_forced_bat[t_bid] = energy_forced_bat[t_bid] / (characs[n]["tau_forced_bat"][t_bid] +
                                                                                characs[n]["tau_delayed_bat"][t_bid])
                    if math.isnan(power_cycle_forced_bat[t_bid]):
                        power_cycle_forced_bat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_forced_bat[t_bid] = 0

            # power_average_forced is charged energy (energy_forced) divided by duration of charging (tau_forced)
            # check whether tau_forced > 0 to avoid division by zero
            if characs[n]["tau_forced_bat"][t_bid] > 0:
                power_avg_forced_bat[t_bid] = energy_forced_bat[t_bid] / characs[n]["tau_forced_bat"][t_bid]
            else:
                power_avg_forced_bat[t_bid] = 0

            energy_delayed_bat[t_bid] = 0  # energy that can be discharged by the TES
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_delayed
            while i < characs[n]["tau_delayed_bat"][t_bid] - 1:
                # add the energy that can be discharged during that hour (power equals energy due to duration of 1 hour)
                energy_delayed_bat[t_bid] += characs[n]["power_flex_delayed_bat"][t_bid + i]
                i += 1
                # check whether end of data is reached
                if t_bid + i >= max_step - 1:
                    break
            # add the energy discharged during the remaining fraction of an hour, time is described by (tau_delayed - i)
            energy_delayed_bat[t_bid] += characs[n]["power_flex_delayed_bat"][t_bid + i] * (
                            characs[n]["tau_delayed_bat"][t_bid] - i)
            # check whether data for the whole cycle exists, n_opt + tau_delayed must be within n_opts of the simulation
            if t_bid + int(characs[n]["tau_delayed_bat"][t_bid]) < max_step:
                # power_cycle_delayed is the delayed energy divided by the duration of the cycle
                # time of the cycle is sum of tau_delayed at n_opt and tau_forced at (n_opt + tau_delayed)
                try:
                    power_cycle_delayed_bat[t_bid] = energy_delayed_bat[t_bid]/ (characs[n]["tau_delayed_bat"][t_bid] +
                                                                                characs[n]["tau_forced_bat"][t_bid +
                                                                            int(characs[n]["tau_delayed_bat"][t_bid])])
                    if math.isnan(power_cycle_delayed_bat[t_bid]):
                        power_cycle_delayed_bat[t_bid] = 0
                except ZeroDivisionError:
                    power_cycle_delayed_bat[t_bid] = 0
            # if tau_forced at (n_opt + tau_delayed) doesn't exist because it exceeds the data,
            # tau_forced at n_opt instead of (n_opt + tau_delayed) is used
            else:
                try:
                    power_cycle_delayed_bat[t_bid] = energy_delayed_bat[t_bid] / (characs[n]["tau_delayed_bat"][t_bid] +
                                                                          characs[n]["tau_forced_bat"][t_bid])
                except ZeroDivisionError:
                    power_cycle_delayed_bat[t_bid] = 0
                    if math.isnan(power_cycle_delayed_bat[t_bid]):
                        power_cycle_delayed_bat[t_bid] = 0
            # power_avg_delayed is discharged energy (energy_delayed) divided by duration of discharging (tau_delayed)
            try:
                power_avg_delayed_bat[t_bid] = energy_delayed_bat[t_bid] / characs[n]["tau_delayed_bat"][t_bid]
            except ZeroDivisionError:
                #[t_bid] = 0
                #if math.isnan(power_avg_delayed_bat[t_bid]):
                power_avg_delayed_bat[t_bid] = 0

            # store all the calculated characs
            #characs[n]["power_avg_forced_bat"][t_bid] = power_avg_forced_bat[t_bid]
            #characs[n]["power_avg_delayed_bat"][t_bid] = power_avg_delayed_bat[t_bid]
            #characs[n]["power_cycle_delayed_bat"][t_bid] = power_cycle_delayed_bat[t_bid]
            #characs[n]["power_cycle_forced_bat"][t_bid] = power_cycle_forced_bat[t_bid]
            characs[n]["energy_forced_bat"][t_bid] = energy_forced_bat[t_bid]
            characs[n]["energy_delayed_bat"][t_bid] = energy_delayed_bat[t_bid]

        #characs[n]["power_bid_avg_forced_bat"] = np.mean(np.array(list(characs[n]["power_avg_forced_bat"].values())))
        #characs[n]["power_bid_avg_delayed_bat"] = np.mean(np.array(list(characs[n]["power_avg_delayed_bat"].values())))
        characs[n]["energy_bid_avg_forced_bat"] = np.mean(np.array(list(characs[n]["energy_forced_bat"].values())))
        characs[n]["energy_bid_avg_delayed_bat"] = np.mean(np.array(list(characs[n]["energy_delayed_bat"].values())))

            #print("Calculating flexibility. Finished building: " + str(n) + ", n_opt: " + str(t_bid) + ".")

        print("Calculating flexibility. Finished building " + str(n) + " finished.")

    # only save when calculated for a large amount of steps or all steps
    if start_step is None or block_length > 700:
        with open(options["path_results"] + "/P2P_characteristics/" + datetime.datetime.now().strftime("%m-%d-%H-%M") +
                  ".p", 'wb') as fp:
            pickle.dump(characs, fp)

    return characs
