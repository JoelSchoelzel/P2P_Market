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

    #create a cleint in context broker and iot agent for all buildings
    cbc_instance = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
    iotac_instance = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)
    # call Class Buidling
    buildings = [Building(id=i, cbc=cbc_instance, iotac=iotac_instance) for i in range(4)]  # TODO set the id properly
    # call Class Coordinator
    coordinator = Coordinator()

    timestamp = datetime.utcnow()
    time_index = str(datetime.utcfromtimestamp(timestamp.timestamp()))
    # Step 1

    # Get the par_rh['n_opt'] input
    nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options,
                                                                                        config.districtData)
    f_bids = []  # todo
    #f_sorted_bids = []
    f_transactions = []  # todo

    for n_opt in range(20):  # par_rh['n_opt'] replaced by validation
        print(f"nopt = {n_opt}")
        # TODO calculate and publish bids
        for building in buildings:
            building.p2p_bid(n_time=n_opt) #todo validate the transaction with same bid from p2p market
            #building.formulate_bid(n_time=n_opt)
            building.publish_data(time_index)
            # TODO recieving bids
            # Get corresponding entities and add values to history
            building_entity = building.cbc.get_entity(building.device.entity_name)
            print(building_entity)
            coordinator.get_bid(building_entity)
            #f_bids.append(coordinator.bid.copy())

        f_bids.append(coordinator.bid.copy())
        # TODo calculate sorted bids
        coordinator.sort_bids()
        #f_sorted_bids.append(coordinator.sorted_bids.copy())
        # TODO calculate transaction
        coordinator.get_transactions()
        f_transactions.append(coordinator.transactions.copy())  # todo
        print(f'nopt = {n_opt}')
        print(f'transaction p2p: {coordinator.transactions}')  # todo
        # TODO coordinator send transaction to context broker subscription
        for i in range(4): #TODO repeat the order of buildings
            coordinator.get_transaction_entity(cleints=i, n_opt=n_opt)
            #buildings[3].cbc.patch_entity(entity=coordinator.transaction_entity)
            buildings[3].cbc.patch_entity(entity=coordinator.transaction_entity)
        # TODO clear the self.initial
        coordinator.sorted_bids.clear()
        coordinator.transactions.clear()

    df0 = pd.DataFrame(f_bids)
    print("df0:")
    print(df0)
    file_path = 'output_bids.csv'
    df0.to_csv(file_path, index=False)

    #df1 = pd.DataFrame(f_sorted_bids)
    #print("df1:")
    #print(df1)
    #file_path = 'output_sortedbids.csv'
    #df1.to_csv(file_path, index=False)

    df2 = pd.DataFrame(f_transactions)
    print("df2:")
    print(df2)
    file_path = 'output_transactions.csv'
    df2.to_csv(file_path, index=False)

# close the mqtt listening thread
# building.mqttc.loop_stop()

# disconnect the mqtt device
# building.mqttc.disconnect()
