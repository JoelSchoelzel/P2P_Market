from HTTP_Building import Building
from HTTP_Coordinator import Coordinator
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_quantumleap
import os
from datetime import datetime, timedelta
from filip.clients.ngsi_v2 import ContextBrokerClient, QuantumLeapClient

# import from P2P_Market
import Filip.config as config
import pandas as pd

# Create the fiware header
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
CB_URL = os.getenv('CB_URL')
Ql_URL = os.getenv('QL_URL')

if __name__ == '__main__':
    clear_context_broker(url=CB_URL, fiware_header=fiware_header)
    clear_quantumleap(url=Ql_URL, fiware_header=fiware_header)

    # create a cleint in context broker and iot agent for all buildings
    cbc_instance = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
    qlc_instance = QuantumLeapClient(url=Ql_URL, fiware_header=fiware_header)

    # get the building number from scenario
    scenario = pd.read_csv(config.options["full_path_scenario"])
    building_number = scenario.size

    # call Class Building
    buildings = [Building(userID=str(i), buildingName=f"bes_{i}",
                          refTransaction="Test", refActiveBid="Test") for i in range(building_number)]

    # call Class Coordinator, the coordinator should have and its own information and buildings'
    coordinator = Coordinator(cbc=cbc_instance, qlc=qlc_instance, buildings=buildings)

    for building in buildings:
        building.add_fiware_interface(cbc=cbc_instance)
        building.initial_fiware_information()
        coordinator.platform_configuration(number_building=int(building.userID))

    # use timestamp to input the time
    start_timestamp = 1443657600
    start_datetime = datetime.utcfromtimestamp(start_timestamp)
    interval = timedelta(hours=1)
    # Step 1

    # Get the par_rh['n_opt'] input. This number now is 744h as 1 month
    nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options,
                                                                                        config.districtData)
    # f_bids = []  # todo
    # f_sorted_bids = []
    # f_transactions = []  # todo

    for n_opt in range(24):  # par_rh['n_opt'] is 744h in one Month
        print(f"n_opt = {n_opt}")
        print(str(start_datetime))
        # time_index = str(start_datetime)
        # calculate and publish bids
        for building in buildings:
            # building.p2p_bid(n_time=n_opt)
            building.formulate_bid(n_time=n_opt)
            building.publish_data(start_datetime)

        # recieving bids
        # Get corresponding entities and coordinator can get bids from entities
        # coordinator should know the market participants
        # implement get_bid in coordinator, which could fetch the data from platform
        # f_bids.append(coordinator.bid.copy()) #  todo validation
        # calculate sorted bids
        coordinator.get_bids()
        coordinator.sort_bids()
        # f_sorted_bids.append(coordinator.sorted_bids.copy()) # todo validation
        # calculate transaction
        # coordinator.calculate_transactions_multiple()
        coordinator.calculate_transactions_single()
        # f_transactions.append(coordinator.transactions.copy()) # todo validation
        # print(f'n_opt = {n_opt}')
        # print(f'transaction: {coordinator.transactions}') # todo validation
        #  move the sending transaction into a method of coordinator, like publish_transaction
        #  coordinator send transaction to context broker subscription
        # coordinator sends the transaction to context broker so that buildings can get transaction
        coordinator.reformat_publish_transaction(start_datetime)
        # building sends request to fiware to get transaction
        for building in buildings:
            building.receive_transaction()
        # clear sorted_bids and transactions so that these are empty for next hour
        # the next round begins in 1 hour
        start_datetime += interval

        # clear the transaction after 24 hours
        # if n_opt % 24 == 0:
        #     coordinator.get_historic_data()

    # df0 = pd.DataFrame(f_bids)
    # print("df0:")
    # print(df0)
    # file_path = 'output_bids.csv'
    # df0.to_csv(file_path, index=False)

    # df1 = pd.DataFrame(f_sorted_bids)
    # print("df1:")
    # print(df1)
    # file_path = 'output_sortedbids.csv'
    # df1.to_csv(file_path, index=False)

    # df2 = pd.DataFrame(f_transactions)
    # print("df2:")
    # print(df2)
    # file_path = 'output_transactions.csv'
    # df2.to_csv(file_path, index=False)

# close the mqtt listening thread
# building.mqttc.loop_stop()

# disconnect the mqtt device
# building.mqttc.disconnect()
