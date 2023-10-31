from Building import Building
import Coordinator as C
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
import os
import datetime

import config

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
    buildings = [Building(id=i) for i in range(4)]  # TODO set the id properly
    #call Class Coordinator
    coordinator = C.Coordinator()

    time = datetime.datetime.now()
    time_index = time.strftime("%d/%m/%Y, %H:%M:%S")
        # Step 1

    nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options,
                                                                                        config.districtData)

    for n_opt in range(par_rh["n_opt"]):
        # TODO calculate and publish bids
        for building in buildings:
            bid = building.formulate_bid(n_opt=n_opt)
            building.publish_data(time_index, bid)
            # TODO recieving bids
            # Get corresponding entities and add values to history
            building_entity = building.cbc.get_entity(building.device.entity_name)
            coordinator.get_bid(building_entity)

        # TODo calculate sorted bids
        sorted_bids = coordinator.sorted_bids(C.bid)
        print("sorted bids: ")
        print(sorted_bids)
        # TODO calculate transaction
        transactions = coordinator.get_transactions(sorted_bids=sorted_bids)
        print("transactions: ")
        print(transactions)





# close the mqtt listening thread
# building.mqttc.loop_stop()

# disconnect the mqtt device
# building.mqttc.disconnect()