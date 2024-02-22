from filip.clients.ngsi_v2 import QuantumLeapClient
import os
from dotenv import load_dotenv
from filip.models.base import FiwareHeader
import json
import matplotlib.pyplot as plt
import matplotlib as matplotlib

load_dotenv()
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
Ql_URL = os.getenv('QL_URL')

qlc_instance = QuantumLeapClient(url=Ql_URL, fiware_header=fiware_header)

# buildings_one_day_money = []
buildings_day_hour_money = {}
for building_number in range(20):
    buildings_day_hour_money[f"building{building_number}"] = {}
    # get trade results of building for 24 hours
    one_building_trade_results = qlc_instance.get_entity_attr_values_by_id(f"urn:ngsi-ld:Transaction:{building_number}",
                                                                           attr_name="tradeResults")
    # take the value of attributes out, the type of value is list
    one_building_one_day_trade_results = one_building_trade_results.attributes[0].values
    print(f"The number of results in one day: {len(one_building_one_day_trade_results)}")
    # calculate the amount of money of a building in one hour
    # one_building_one_day_sum = 0
    # separate day results into every hour
    for day_hour in range(len(one_building_one_day_trade_results)):
        one_building_one_hour_trade_results = one_building_one_day_trade_results[day_hour]
        print(f"The number of trading objects for building {building_number} in hour {day_hour}: {len(one_building_one_hour_trade_results)}")
        one_building_one_hour_money = 0
        # one_building_one_day_sum += one_building_one_hour_money
        # some results are empty shown as [], this situation won't be considered
        if one_building_one_hour_trade_results:
            # the content of list is string, convert them to dictionary
            one_building_one_hour_trade_result = [json.loads(item) for item in one_building_one_hour_trade_results]
            # if the building is a seller, its cash should be positive, otherwise is negative
            if one_building_one_hour_trade_result[0]["powerDirection"]["tradingObjectRole"] == "buyer":
                for n in range(len(one_building_one_hour_trade_result)):
                    one_building_one_hour_money += one_building_one_hour_trade_result[n]["realQuantity"]["quantity"] * \
                                                   one_building_one_hour_trade_result[n]["realPrice"]["price"]
            else:
                for n in range(len(one_building_one_hour_trade_result)):
                    one_building_one_hour_money -= one_building_one_hour_trade_result[n]["realQuantity"]["quantity"] * \
                                                   one_building_one_hour_trade_result[n]["realPrice"]["price"]
        # this dictionary can show the amount of money of the building for every hour
        buildings_day_hour_money[f"building{building_number}"][day_hour] = one_building_one_hour_money
    # this list can show the sum of building after one day
    # buildings_one_day_money.append(one_building_one_day_sum)
    # print(f"The amount of money for building {building_number} in day: {one_building_one_day_sum}")

# The sum of buildings should be
# print("The sum of buildings for every hour:")
# print(buildings_one_day_money)
print("The dictionary for money of all building for every hour:")
print(buildings_day_hour_money)

# Set the font size globally
fontsize = 18
font = {'family': 'serif',
        'weight': 'normal',
        'size': fontsize
        }
lines = {
    "linewidth": 1
}
mathtext = {'default': 'regular'}
matplotlib.rc('font', **font)
matplotlib.rc("lines", **lines)
matplotlib.rc("mathtext", **mathtext)

fig1, ax1 = plt.subplots(figsize=(12, 10))
# number = len(buildings_day_hour_money)
number_6 = [1, 2, 8, 9]
money = []
for building_number in number_6:
    hours = int(len(buildings_day_hour_money[f"building{building_number}"]))
    money_of_building = [buildings_day_hour_money[f"building{building_number}"][hour] for hour in range(hours)]
    money.append(money_of_building)
    if building_number in [8, 9]:
        ax1.plot(money_of_building, ":*", label=f"building{building_number}: MFH with CHP")
    else:
        ax1.plot(money_of_building, "-", label=f"building{building_number}: SFH without CHP")

ax1.set_xlabel("Time in Hour")
ax1.set_ylabel("The income of building in Euro")
ax1.grid()
ax1.legend()
ax1.set_title(f"Cash flow over time for buildings")
plt.show()
# Plotting the amount of money over time for building 0
# money_0 = list(buildings_day_hour_money['building0'].values())
# money_1 = list(buildings_day_hour_money['building1'].values())

# Plotting the bar plot
# fig, ax = plt.subplots()
# ax.plot(money_0, label='Building 0', color='red', linestyle='-', marker='o')
# ax.plot(money_1, label='Building 0', color='blue', linestyle='-', marker='o')

#plt.bar(time, money, color='red', edgecolor='black')
# Adding labels and title
# ax.set_xlabel('Time (h)')
# ax.set_ylabel('The amount of money (euro)')
# # plt.xlabel('Time (h)')
# # plt.ylabel('The amount of money (euro)')
# ax.set_title('Amount of Money over Time for Building 0')

number = len(buildings_day_hour_money)
# Sum the separate amount of money in dictionary
sum_money = []
for building_number in range(number):
    hours = int(len(buildings_day_hour_money[f"building{building_number}"]))
    total_money = 0
    for hour in range(hours):
        total_money += buildings_day_hour_money[f"building{building_number}"][hour]
    sum_money.append(total_money)
# Plotting the amount of money after 24 hours for all buildings
building_ID = [f"B_{i}" for i in range(number)]
# Plotting the bar plot
plt.bar(building_ID, sum_money, color=(0.8, 0, 0), edgecolor='black')
# Adding labels and title
plt.xlabel('Building')
plt.ylabel('Cash flow in Euro')
plt.title('Transactions clearing after one day')
# Set x-axis major locator to integer values only
# plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
plt.show()