#import from filip
from filip.clients.ngsi_v2 import ContextBrokerClient, IoTAClient
from filip.clients.mqtt import IoTAMQTTClient
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
from filip.models.ngsi_v2.iot import \
     Device, \
     DeviceAttribute, \
     ServiceGroup

#import form packages
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import pandas as pd
import json
import matplotlib.pyplot as plt
import time

#verschiedene URL
CB_URL = "http://134.130.166.184:1026"
IOTA_URL = "http://134.130.166.184:4041"
MQTT_Broker_URL ="mqtt://134.130.166.184:1883"

#database
Service = 'lem_test'
Service_path = '/'
APIKEY = 'jdu-zwu'

#simulation time
t_start = 0
t_end = 23
t_step = 1

if __name__ == '__main__':
    #create a fiware header
    fiware_header = FiwareHeader(service=Service,
                                 service_path=Service_path)

    #clear the state of context broker and iot agent
    clear_context_broker(url=CB_URL, fiware_header=fiware_header)
    clear_iot_agent(url=IOTA_URL, fiware_header=fiware_header)


    #create the clients
    cbc = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
    iotac = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)

    #define lists to store historical data
    history_demand = []
    history_production = []

    # Create a service group and add it to your devices
    service_group = ServiceGroup(apikey=APIKEY,
                                 resource="/iot/json")

    # create the 6 buildings devices, simulate time attribute, demand of building attribute and production of building attribute
    t_sim = DeviceAttribute(name='simtime',
                            object_id='t_sim',
                            type="Number")
    t_dem = DeviceAttribute(name='demand',
                            object_id='t_dem',
                            type='Number')
    t_pro = DeviceAttribute(name='production',
                            object_id='t_pro',
                            type='Number')

    building_000 = Device(device_id="device:000",
                          entity_name="urn:ngsi-ld:Building:000",
                          entity_type="Building",
                          protocol='IoTA-JSON',
                          transport='MQTT',
                          apikey=APIKEY,
                          attributes=[t_sim, t_dem, t_pro],
                          commands=[])

    #Provision service group and add it to your IOTAClient
    iotac.post_group(service_group=service_group, update=True)
    #Provision the devices at the Iota-agent
    iotac.post_device(device=building_000, update=True)

    #check in the context broker if the entities corresponding to the buildings
    print(cbc.get_entity(building_000.entity_name).json(indent=2))

    #get the energy data of the buildings
    b0_df = pd.read_csv("T:\jdu-zwu\Test Buildings\operations_1h/building0.csv")
    demand_000 = list(b0_df["res_load"])
    production_000 = list(b0_df["res_inj"])

    #b1_df = pd.read_csv("T:\jdu-zwu\Test\operations_1h/building1.csv")
    #b2_df = pd.read_csv("T:\jdu-zwu\Test\operations_1h/building2.csv")
    #b3_df = pd.read_csv("T:\jdu-zwu\Test\operations_1h/building3.csv")
    #b4_df = pd.read_csv("T:\jdu-zwu\Test\operations_1h/building4.csv")
    #b5_df = pd.read_csv("T:\jdu-zwu\Test\operations_1h/building5.csv")



    #create an MQTTv5 Client
    mqttc= IoTAMQTTClient(protocol=mqtt.MQTTv5)

    #register service group for MQTTv5
    mqttc.add_service_group(service_group=service_group)
    #register the devices for MQTTv5 client
    mqttc.add_device(building_000)

    #connect to mqtt broker and subscribe the topic
    mqtt_url = urlparse(MQTT_Broker_URL)
    mqttc.connect(host=mqtt_url.hostname,
                  port=mqtt_url.port,
                  keepalive=60,
                  bind_address="",
                  bind_port=0,
                  clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
                  properties=None)

    #subcribe to the topics
    mqttc.subscribe()
    # create a non-blocking thread for mqtt communication
    mqttc.loop_start()

    #create a loop that publishes the energydata every hour to the context broker
    for t_sim in range(int(t_start), int(t_end), int(t_step)):
        mqttc.publish(device_id=building_000.device_id,
                      payload={"simtime": t_sim,
                               "demand": demand_000[t_sim],
                               "production": production_000[t_sim]})

        #wait for 1second before publishing next values
        time.sleep(1)

        #Get corresponding entities and add values to history
        building_000_entity = cbc.get_entity(entity_id=building_000.entity_name,
                                             entity_type=building_000.entity_type)
        #append the data to history
        history_demand.append({"simtime": building_000_entity.simtime.value,
                               "demand": building_000_entity.demand.value})
        history_production.append({"simtime": building_000_entity.simtime.value,
                                   "production": building_000_entity.production.value})
    #close the mqtt listening thread
    mqttc.loop_stop()

    #disconnect the mqtt device
    mqttc.disconnect()

    #plot results
    fig, ax = plt.subplots()
    t_simulation = [item["simtime"] for item in history_demand]
    demand = [item["demand"] for item in history_demand]
    ax.plot(t_simulation, demand)
    ax.set_xlabel('time in hour')
    ax.set_ylabel('demand in kwh')

    fig2, ax2 = plt.subplots()
    t_simulation = [item["simtime"] for item in history_production]
    production = [item["production"] for item in history_production]
    ax2.plot(t_simulation, production)
    ax2.set_xlabel('time in hour')
    ax2.set_ylabel('production in kwh')

    plt.show()

    clear_context_broker(url=CB_URL, fiware_header=fiware_header)
    clear_iot_agent(url=IOTA_URL, fiware_header=fiware_header)