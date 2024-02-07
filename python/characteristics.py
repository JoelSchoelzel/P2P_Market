import datetime
import pickle


def calc_characs(nodes, options, par_rh, opti_res: dict = None, start: int = None, length: int = 3):
    """
    Calculate KPIs to evaluate different flexibilities of each building according to Stinner et al.
    "https://linkinghub.elsevier.com/retrieve/pii/S0306261916311424"

    If a optimization result is provided, the SOC of the result is used. Otherwise an empty storage is assumed for
    forced flexibility and a full storage is assumed for delayed flexibility.

    Args:
        nodes (dict):
        options (dict):
        par_rh (dict):
        opti_res: optimization result to get SOC, if not provided a empty/full SOC is assumed
        start: starting optimization step for which flexibility characs are calculated,
            if not provided all optimization steps are calculated
        length: amount of optimization steps to be calculated, only relevant when start is provided

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

        # DHW
        Q_DHW = sum(nodes[n]["dhw"][n_opt] for n_opt in range(par_rh["n_opt"]))

        n_hours = par_rh["n_opt"]

        # calculate beta_th
        beta_th = Q_stor_avg * n_hours / (Q_SH + Q_DHW)
        characs[n]["beta_th"] = beta_th

        # set step params
        if start is not None:
            # when a start step is provided, start and length is used:
            max_step = start + par_rh["n_hours"]  # set the starting step + 36 hours as the maximum step
            data_steps = list(range(start, max_step))  # use the data for 36 hours (optimization horizon)
            result_steps = list(range(start, start + length))  # only calculate results for the specified steps
        else:
            # when no start step is provided, all steps in par_rh are used
            max_step = par_rh["n_opt"]  # maximum step is end of data
            data_steps = list(range(par_rh["n_opt"]))  # use data of all steps
            result_steps = list(range(par_rh["n_opt"]))  # calculate results for all steps
        if opti_res is not None:
            # use the SOC from optimization results if provided
            soc_opti = {step: opti_res[start][n][3]["tes"][step] for step in data_steps}
        else:
            # set to None if optimization results are not provided
            soc_opti = None

        ### elec

        # calculate temporal and power flexibility for all data steps
        for n_opt in data_steps:

            ### temporal flexibility

            # forced flexibility, time until TES is fully charged with maximum charging

            if soc_opti is not None:
                # use SOC from optimization results when provided
                charge = soc_opti[n_opt]
            else:
                # TES assumed to be fully discharged at beginning if no SOC is provided
                charge = 0
            # tau_forced: time it takes to charge
            tau_forced = 0
            # loop until the TES is fully charged
            while charge < nodes[n]["devs"]["tes"]["cap"]:
                # check whether there are any heaters, break otherwise
                if sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) == 0:
                    break
                # maximal charging is difference between capacity of heaters and heat demand at (n_opt + tau_forced)
                max_charging = sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) - nodes[n]["heat"][n_opt + tau_forced] - (0.5 * nodes[n]["dhw"][n_opt + tau_forced])
                # check whether the TES can be charged by maximal charging without exceeding the capacity
                if charge + max_charging <= nodes[n]["devs"]["tes"]["cap"]:
                    # the charge is added and tau_forced incremented by an hour
                    charge += max_charging
                    tau_forced += 1
                # in case maximal charging would exceed the capacity:
                else:
                    # tau_forced is incremented by the fraction of the hour that charging is still possible
                    # constant rate of charging is assumed during the hour
                    tau_forced += (nodes[n]["devs"]["tes"]["cap"] - charge) / max_charging
                    # charge is set to the capacity
                    charge = nodes[n]["devs"]["tes"]["cap"]
                # check whether end of data is reached
                if n_opt + tau_forced >= max_step:
                    break

            characs[n]["tau_forced"][n_opt] = tau_forced

            # delayed flexibility, time until TES is fully discharged with no charging

            if soc_opti is not None:
                # use SOC from optimization results when provided
                charge = soc_opti[n_opt]
            else:
                # when SOC is not provided
                # check whether TES can be fully charged during preceding time steps
                # max heat production must be greater than heat demand in every considered timestep to be sure
                fully_charged = True
                # iterate through last few hours
                for i in range(24):
                    # set fully_charged to False if demand was greater the capacity of heaters
                    if (sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][n_opt - i] - (0.5 * nodes[n]["dhw"][n_opt - i])) < 0:
                        fully_charged = False
                charge = nodes[n]["devs"]["tes"]["cap"]
                # determine the maximum possible charge when demand was greater than max production at any point
                if not fully_charged:
                    # iterate through last few hours
                    for i in range(24):
                        # add maximum charging (difference between capacity of heaters and heat demand) to charge
                        charge += sum(nodes[n]["devs"][dev]["cap"] for dev in heaters) - nodes[n]["heat"][n_opt - i] - (0.5 * nodes[n]["dhw"][n_opt - i])
                        # make sure charge stays between the maximum and minimum value (between capacity and 0)
                        if charge >= nodes[n]["devs"]["tes"]["cap"]:
                            charge = nodes[n]["devs"]["tes"]["cap"]
                        elif charge < 0:
                            charge = 0

            # tau_delayed: time it takes to discharge
            tau_delayed = 0
            # loop until the storage is fully discharged
            while charge > 0:
                # maximum discharging is the heat demand at (n_opt + tau_delayed)
                discharging = nodes[n]["heat"][n_opt + tau_delayed] + (0.5 * nodes[n]["dhw"][n_opt + tau_delayed])
                # check whether there's enough charge remaining for maximum discharging
                if charge - discharging > 0:
                    # discharge is subtracted and tau_delayed incremented by an hour
                    charge -= discharging
                    tau_delayed += 1
                # in case not enough charge is remaining:
                else:
                    # tau_delayed is incremented by the fraction of the hour that discharging is still possible
                    # constant rate of discharging is assumed during the hour
                    tau_delayed += charge / discharging
                    charge = 0
                # check whether end of data is reached
                if n_opt + tau_delayed >= max_step:
                    break

            characs[n]["tau_delayed"][n_opt] = tau_delayed

            ### power flexibility

            # reference case: power required without use of flexibility
            # elec + power used by heatpumps
            if nodes[n]["devs"]["hp35"]["cap"] > 0:
                power_ref = nodes[n]["elec"][n_opt] + nodes[n]["heat"][n_opt] / nodes[n]["devs"]["COP_sh35"][n_opt]
            elif nodes[n]["devs"]["hp55"]["cap"] > 0:
                power_ref = nodes[n]["elec"][n_opt] + nodes[n]["heat"][n_opt] / nodes[n]["devs"]["COP_sh55"][n_opt]
            else:
                power_ref = nodes[n]["elec"][n_opt]

            # maximum power that can be generated
            power_max = nodes[n]["devs"]["chp"]["cap"] / nodes[n]["devs"]["chp"]["eta_th"] * nodes[n]["devs"]["chp"][
                "eta_el"]

            # minimum power that can be generated
            power_min = 0

            # power flexibility as difference between reference case and max/min power generation
            if power_max > 0:
                power_flex_forced = power_max - power_ref
            else:
                power_flex_forced = 0
            power_flex_delayed = power_ref - power_min

            # alpha_el_flex
            alpha_el_flex_forced = power_flex_forced / dQ_build_nom
            alpha_el_flex_delayed = power_flex_delayed / dQ_build_nom

            # store the calculated characs
            characs[n]["power_flex_forced"][n_opt] = power_flex_forced
            characs[n]["power_flex_delayed"][n_opt] = power_flex_delayed
            characs[n]["alpha_el_flex_forced"][n_opt] = alpha_el_flex_forced
            characs[n]["alpha_el_flex_delayed"][n_opt] = alpha_el_flex_delayed

        print("Part 1 finished.")

        # calculate average and cycle power as well as energy flexibility for result steps only
        for n_opt in result_steps:

            # average and cycle power flexibility

            energy_forced = 0  # energy that can the TES can be charged with
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_forced
            while i < characs[n]["tau_forced"][n_opt] - 1:
                # add the energy that can be charged during that hour (power equals energy due to duration of 1 hour)
                energy_forced += characs[n]["power_flex_forced"][n_opt + i]
                i += 1
                # check whether end of data is reached
                if n_opt + i >= max_step-1:
                    break
            # add the energy charged during the remaining fraction of an hour, time is described by (tau_forced - i)
            energy_forced += characs[n]["power_flex_forced"][n_opt + i] * (characs[n]["tau_forced"][n_opt] - i)

            # cycle describes time frame of first charging and then discharging the storage afterwards and vice versa
            # check whether data for the whole cycle exists, n_opt + tau_forced must be within n_opts of the simulation
            if n_opt + int(characs[n]["tau_forced"][n_opt]) < max_step:
                # power_cycle_forced is the forced energy divided by the duration of the cycle
                # time of the cycle is sum of tau_forced at n_opt and tau_delayed at (n_opt + tau_forced)
                try:
                    power_cycle_forced = energy_forced / (characs[n]["tau_forced"][n_opt] + characs[n]["tau_delayed"][n_opt + int(characs[n]["tau_forced"][n_opt])])
                except ZeroDivisionError:
                    power_cycle_forced = 0
            # if tau_delayed at (n_opt + tau_forced) doesn't exist because it exceeds the data,
            # tau_delayed at n_opt instead of (n_opt + tau_forced) is used
            else:
                try:
                    power_cycle_forced = energy_forced / (characs[n]["tau_forced"][n_opt] + characs[n]["tau_delayed"][n_opt])
                except ZeroDivisionError:
                    power_cycle_forced = 0

            # power_average_forced is charged energy (energy_forced) divided by duration of charging (tau_forced)
            # check whether tau_forced > 0 to avoid division by zero
            if characs[n]["tau_forced"][n_opt] > 0:
                power_avg_forced = energy_forced / characs[n]["tau_forced"][n_opt]
            else:
                power_avg_forced = 0

            energy_delayed = 0  # energy that can the TES can be discharged by
            i = 0  # variable to iterate through hours, represents whole hours
            # loop through the whole hours previously calculated as tau_delayed
            while i < characs[n]["tau_delayed"][n_opt] - 1:
                # add the energy that can be discharged during that hour (power equals energy due to duration of 1 hour)
                energy_delayed += characs[n]["power_flex_delayed"][n_opt + i]
                i += 1
                # check whether end of data is reached
                if n_opt + i >= max_step - 1:
                    break
            # add the energy discharged during the remaining fraction of an hour, time is described by (tau_delayed - i)
            energy_delayed += characs[n]["power_flex_delayed"][n_opt + i] * (characs[n]["tau_delayed"][n_opt] - i)
            # check whether data for the whole cycle exists, n_opt + tau_delayed must be within n_opts of the simulation
            if n_opt + int(characs[n]["tau_delayed"][n_opt]) < max_step:
                # power_cycle_delayed is the delayed energy divided by the duration of the cycle
                # time of the cycle is sum of tau_delayed at n_opt and tau_forced at (n_opt + tau_delayed)
                try:
                    power_cycle_delayed = energy_delayed / (characs[n]["tau_delayed"][n_opt] + characs[n]["tau_forced"][n_opt + int(characs[n]["tau_delayed"][n_opt])])
                except ZeroDivisionError:
                    power_cycle_delayed = 0
            # if tau_forced at (n_opt + tau_delayed) doesn't exist because it exceeds the data,
            # tau_forced at n_opt instead of (n_opt + tau_delayed) is used
            else:
                try:
                    power_cycle_delayed = energy_delayed / (characs[n]["tau_delayed"][n_opt] + characs[n]["tau_forced"][n_opt])
                except ZeroDivisionError:
                    power_cycle_delayed = 0
            # power_avg_delayed is discharged energy (energy_delayed) divided by duration of discharging (tau_delayed)
            try:
                power_avg_delayed = energy_delayed / characs[n]["tau_delayed"][n_opt]
            except ZeroDivisionError:
                power_avg_delayed = 0
            # store all the calculated characs
            characs[n]["power_avg_forced"][n_opt] = power_avg_forced
            characs[n]["power_avg_delayed"][n_opt] = power_avg_delayed
            characs[n]["power_cycle_delayed"][n_opt] = power_cycle_delayed
            characs[n]["power_cycle_forced"][n_opt] = power_cycle_forced
            characs[n]["energy_forced"][n_opt] = energy_forced
            characs[n]["energy_delayed"][n_opt] = energy_delayed

            beta_el_forced = energy_forced * par_rh["n_opt"] / (Q_SH + Q_DHW)
            beta_el_delayed = energy_delayed * par_rh["n_opt"] / (Q_SH + Q_DHW)

            characs[n]["beta_el_forced"][n_opt] = beta_el_forced
            characs[n]["beta_el_delayed"][n_opt] = beta_el_delayed

            print("Calculating flexibility. Finished building: " + str(n) + ", n_opt: " + str(n_opt) + ".")

        print("Building " + str(n) + " finished.")

    # only save when calculated for a large amount of steps or all steps
    if start is None or length > 700:
        with open(options["path_results"] + "/P2P_characteristics/" + datetime.datetime.now().strftime("%m-%d-%H-%M") +
                  ".p", 'wb') as fp:
            pickle.dump(characs, fp)

    return characs
