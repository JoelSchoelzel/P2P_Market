from Building import Building
import Coordinator as C
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
import os
import datetime

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
    for n_opt in list(...):
        # TODO calculate and publish bids
        .compute_bids()
        # TODo recieving bids
        .sort_bids()
        # TODO calculate transaction
        .compute_transaction()
    for building in buildings:

            building.publish_data(time_index)

            #Get corresponding entities and add values to history
            building_entity = building.cbc.get_entity(building.device.entity_name)
            coordinator.get_bid(building_entity)

            # close the mqtt listening thread
            #building.mqttc.loop_stop()

            # disconnect the mqtt device
            #building.mqttc.disconnect()

    sorted_bids = coordinator.sorted_bids(C.bid)
    transactions = coordinator.get_transactions(sorted_bids=sorted_bids)
    print("sorted bids: ")
    print(sorted_bids)
    print("transactions: ")
    print(transactions)