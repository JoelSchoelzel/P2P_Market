from Building import Building
from Coordinator import Coordinator
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
import os
from datetime import datetime
from filip.clients.ngsi_v2 import ContextBrokerClient, IoTAClient


# import from P2P_Market
import config
import pandas as pd

# Create the fiware header
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
CB_URL = os.getenv('CB_URL')
IOTA_URL = os.getenv('IOTA_URL')

if __name__ == '__main__':
    clear_context_broker(url=CB_URL, fiware_header=fiware_header)
    clear_iot_agent(url=IOTA_URL, fiware_header=fiware_header)

    # create a cleint in context broker and iot agent for all buildings
    cbc_instance = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
    iotac_instance = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)

    # get the building number from scenario
    scenario = pd.read_csv(config.options["full_path_scenario"])
    building_number = scenario.size

    # set the id properly
    # call Class Building
    buildings = [Building(id=i, cbc=cbc_instance, iotac=iotac_instance) for i in range(building_number)]
    # call Class Coordinator, the coordinator should have and its own information and buildings'
    coordinator = Coordinator(cbc=cbc_instance, iotac=iotac_instance, buildings=buildings)

    # use timestamp to input the time
    timestamp = datetime.utcnow()
    time_index = str(datetime.utcfromtimestamp(timestamp.timestamp()))
    # Step 1

    # Get the par_rh['n_opt'] input. This number now is 744h as 1 month
    nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options,
                                                                                        config.districtData)
    #f_bids = []  # todo
    #f_sorted_bids = []
    #f_transactions = []  # todo

    for n_opt in range(par_rh['n_opt']):  # par_rh['n_opt'] is 744h in ein Monat
        print(f"n_opt = {n_opt}")
        # calculate and publish bids
        for building in buildings:
            #building.p2p_bid(n_time=n_opt)
            building.formulate_bid(n_time=n_opt)
            building.publish_data(time_index)
            # recieving bids
            # Get corresponding entities and coordinator can get bids from entities
            # TODO coordinator should know the market participants
            # TODO implement get_bid in coordinator, which should fetch the data from platform
            #coordinator.get_bid()
            #f_bids.append(coordinator.bid.copy())

        #f_bids.append(coordinator.bid.copy())
        # calculate sorted bids
        coordinator.get_bids()
        coordinator.sort_bids()
        #f_sorted_bids.append(coordinator.sorted_bids.copy())
        # calculate transaction
        coordinator.calculate_transactions()  # TODO rename this method to clear_market or calculate_transaction?
        #f_transactions.append(coordinator.transactions.copy())  # todo validation
        #print(f'n_opt = {n_opt}')
        #print(f'transaction: {coordinator.transactions}')  # todo validation
        # TODO move the sending transaction into a method of coordinator, like publish_transaction
        # TODO coordinator send transaction to context broker subscription

        # coordinator sends the transaction to context broker so that buildings can get transaction
        for i in range(building_number):
            coordinator.get_transaction_entity(cleints=i, n_opt=n_opt)
            coordinator.publish_transaction()
        # TODO move following code into a method of coordinator, like clear_data / reset_data etc.
        #  and this method can be called inside the publish_transaction method
        # clear sorted_bids and transactions so that these are empty for next hour
        coordinator.clear_data()

    # df0 = pd.DataFrame(f_bids)
    # print("df0:")
    # print(df0)
    # file_path = 'output_bids.csv'
    # df0.to_csv(file_path, index=False)

    #df1 = pd.DataFrame(f_sorted_bids)
    #print("df1:")
    #print(df1)
    #file_path = 'output_sortedbids.csv'
    #df1.to_csv(file_path, index=False)

    # df2 = pd.DataFrame(f_transactions)
    # print("df2:")
    # print(df2)
    # file_path = 'output_transactions.csv'
    # df2.to_csv(file_path, index=False)

# close the mqtt listening thread
# building.mqttc.loop_stop()

# disconnect the mqtt device
# building.mqttc.disconnect()
