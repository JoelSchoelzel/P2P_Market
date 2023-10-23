#import from filip
from filip.clients.ngsi_v2 import ContextBrokerClient, IoTAClient
from filip.clients.mqtt import IoTAMQTTClient
from filip.models.base import FiwareHeader
from filip.models.ngsi_v2.iot import \
     Device, \
     DeviceAttribute, \
     ServiceGroup

#import form packages
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import pandas as pd
import time
import os
from dotenv import load_dotenv
import pickle

# Load environment variables from .env file
load_dotenv()
# Create a service group and add it to your devices
service_group = ServiceGroup(apikey=os.getenv('APIKEY'),
                             resource="/iot/json")

# Context Broker, IoT Agent and mqtt URL
CB_URL = os.getenv('CB_URL')
IOTA_URL = os.getenv('IOTA_URL')
MQTT_Broker_URL = os.getenv('MQTT_Broker_URL')

# Create the fiware header
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
print(CB_URL)
print(IOTA_URL)
print(MQTT_Broker_URL)
print(fiware_header)

class Building:

    def __init__(self, id):
        self.id = id
        self.bids = self.load_bid()
        self.device = self.building_device()
        self.initialization()
        self.mqtt_initialization()


    def publish_data(self, time_index):
        # publish the device and data
        self.mqttc.publish(device_id=self.building_device().device_id,
                           payload={"bidtime": time_index,
                                    "name": f"bes_{self.id}",
                                    "price": self.bids[f"bes_{self.id}"][0],
                                    "quantity": self.bids[f"bes_{self.id}"][1],
                                    "buyer": self.bids[f"bes_{self.id}"][2],
                                    "number": int(self.bids[f"bes_{self.id}"][3])})
        #wait for 1second before publishing next values
        time.sleep(1)


    def building_device(self):
        # create the  building's device, simulate time attribute, demand of building attribute and production of building attribute
        t_bidtime = DeviceAttribute(name='bidtime',
                                    object_id='t_bidtime',
                                    type="String")
        t_name = DeviceAttribute(name='name',
                                object_id='t_name',
                                type="String")
        t_price = DeviceAttribute(name='price',
                                object_id='t_price',
                                type='Number')
        t_quantity = DeviceAttribute(name='quantity',
                                object_id='t_quantity',
                                type='Number')
        t_buyer = DeviceAttribute(name='buyer',
                                     object_id='t_buyer',
                                     type='String')
        t_numer = DeviceAttribute(name='number',
                                     object_id='t_num',
                                     type='Number')

        building = Device(device_id=f"device:{self.id}",
                          entity_name=f"urn:ngsi-ld:Building:{self.id}",
                          entity_type="Building",
                          protocol='IoTA-JSON',
                          transport='MQTT',
                          apikey=os.getenv('APIKEY'),
                          attributes=[t_bidtime, t_name, t_price, t_quantity, t_buyer, t_numer],
                          commands=[])
        return building


    def initialization(self):
        # create the clients
        self.cbc = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
        self.iotac = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)


        # Provision service group and add it to your IOTAClient
        self.iotac.post_group(service_group=service_group, update=True)
        # Provision the devices at the Iota-agent
        self.iotac.post_device(device=self.device, update=True)
        # check in the context broker if the entities corresponding to the buildings
        print(self.cbc.get_entity(self.device.entity_name))




    def mqtt_initialization(self):
        # create an MQTTv5 Client
        self.mqttc = IoTAMQTTClient(protocol=mqtt.MQTTv5)

        # register service group for MQTTv5
        self.mqttc.add_service_group(service_group=service_group)
        # register the devices for MQTTv5 client
        self.mqttc.add_device(self.building_device())

        # connect to mqtt broker and subscribe the topic
        mqtt_url = urlparse(MQTT_Broker_URL)
        self.mqttc.connect(host=mqtt_url.hostname,
                           port=mqtt_url.port,
                           keepalive=60,
                           bind_address="",
                           bind_port=0,
                           clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
                           properties=None)

        # subcribe to the topics
        self.mqttc.subscribe()
        # create a non-blocking thread for mqtt communication
        self.mqttc.loop_start()



    def load_bid(self):
        # load the bid from mar_dict
        file_path = "D:/jdu-zwu/P2P_Market/results/P2P_mar_dict/scenario_test_price.p"
        with open(file_path, 'rb') as file:
            loaded_data = pickle.load(file)

        # get the bid of the buildings
        bids = loaded_data['bid'][0]
        return bids

