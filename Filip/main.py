from Building import Building
from Coordinator import Coordinator
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
import os
import datetime

#import from P2P_Market
import config

#import for visual
import pandas as pd

# Create the fiware header
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
CB_URL = os.getenv('CB_URL')
IOTA_URL = os.getenv('IOTA_URL')
MQTT_Broker_URL = os.getenv('MQTT_Broker_URL')


if __name__ == '__main__':
    clear_context_broker(url=CB_URL, fiware_header=fiware_header)
    clear_iot_agent(url=IOTA_URL, fiware_header=fiware_header)

    #call Class Buidling
    buildings = [Building(id=i) for i in range(1)]  # TODO set the id properly
    #call Class Coordinator
    coordinator = Coordinator()

    time = datetime.datetime.now()
    time_index = time.strftime("%d/%m/%Y, %H:%M:%S")
        # Step 1

    nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options,
                                                                                        config.districtData)
    bids = []
    for n_opt in range(3):
        # TODO calculate and publish bids
        for building in buildings:
            building.formulate_bid(n_time=n_opt)
            building.publish_data(time_index)
            # TODO recieving bids
            # Get corresponding entities and add values to history
            building_entity = building.cbc.get_entity(building.device.entity_name)
            coordinator.get_bid(building_entity)
            bids.append(coordinator.bid.copy())
            print("bids:")
            print(bids)
        # TODo calculate sorted bids
        #coordinator.sort_bids()
        #print("sorted bids: ")
        #print(coordinator.sorted_bids)
        # TODO calculate transaction
        #coordinator.get_transactions()
        #print("transactions: ")
        #print(coordinator.transactions)

    df = pd.DataFrame(bids)
    print("df:")
    print(df)
    file_path = 'output0.csv'
    df.to_csv(file_path, index=False)


# close the mqtt listening thread
# building.mqttc.loop_stop()

# disconnect the mqtt device
# building.mqttc.disconnect()