import datetime
import pickle
import math

def calc_characs_single(nodes, block_length, bes_id, soc_state):

    EHG = ["hp35", "hp55", "chp", "bz"]

    # list of all heaters
    heaters = ["hp35", "hp55", "chp", "bz", "boiler"]

    start_hour = list(soc_state.keys())[0]
    max_step = start_hour + block_length
    data_steps = list(range(start_hour, max_step))

    n = bes_id

    if soc_state is not None:
        # use the SOC from optimization results if provided
        #soc_opti = {step: soc_state[step] for step in data_steps}
        soc_opti = soc_state
    else:
        # set to None if optimization results are not provided
        soc_opti = None

    # create dict to store the characs in
    characs = {
        "tau_forced": {},
        "tau_delayed": {},
        "power_flex_forced": {},
        "power_flex_delayed": {},
        "energy_forced": {},
        "energy_delayed": {},
    }

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
            max_charging = sum(nodes[n]["devs"][dev]["cap"] for dev in EHG) - nodes[n]["heat"][n_opt + tau_forced] - (
                        0.5 * nodes[n]["dhw"][n_opt + tau_forced])
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

        characs["tau_forced"][n_opt] = tau_forced

        # delayed flexibility, time until TES is fully discharged with no charging

        if soc_opti is not None:
            # use SOC from optimization results when provided
            charge = soc_opti[n_opt]

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

        characs["tau_delayed"][n_opt] = tau_delayed

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

        # store the calculated characs
        characs["power_flex_forced"][n_opt] = power_flex_forced
        characs["power_flex_delayed"][n_opt] = power_flex_delayed

    for n_opt in data_steps:

        energy_forced = 0  # energy that can the TES can be charged with
        i = 0  # variable to iterate through hours, represents whole hours
        # loop through the whole hours previously calculated as tau_forced
        while i < characs["tau_forced"][n_opt] - 1:
            # add the energy that can be charged during that hour (power equals energy due to duration of 1 hour)
            energy_forced += characs["power_flex_forced"][n_opt + i]
            i += 1
            # check whether end of data is reached
            if n_opt + i >= max_step - 1: #Abbruch check
                break
        # add the energy charged during the remaining fraction of an hour, time is described by (tau_forced - i)
        energy_forced += characs["power_flex_forced"][n_opt + i] * (characs["tau_forced"][n_opt] - i)

        energy_delayed = 0  # energy that can the TES can be discharged by
        i = 0  # variable to iterate through hours, represents whole hours
        # loop through the whole hours previously calculated as tau_delayed
        while i < characs["tau_delayed"][n_opt] - 1:
            # add the energy that can be discharged during that hour (power equals energy due to duration of 1 hour)
            energy_delayed += characs["power_flex_delayed"][n_opt + i]
            i += 1
            # check whether end of data is reached
            if n_opt + i >= max_step - 1:
                break
        # add the energy discharged during the remaining fraction of an hour, time is described by (tau_delayed - i)
        energy_delayed += characs["power_flex_delayed"][n_opt + i] * (characs["tau_delayed"][n_opt] - i)

        characs["energy_forced"][n_opt] = energy_forced
        characs["energy_delayed"][n_opt] = energy_delayed

    return characs["energy_delayed"][start_hour], characs["energy_forced"][start_hour]
