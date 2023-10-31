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
import time
import os
from dotenv import load_dotenv


#import from P2P_Market
import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import config

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


class Building:

    def __init__(self, id):
        self.id = id
        self.device = self.building_device()
        self.initialization()
        self.mqtt_initialization()


    def publish_data(self, time_index, bid):
        # publish the device and data
        self.mqttc.publish(device_id=self.building_device().device_id,
                           payload={"bidtime": time_index,
                                    "name": f"bes_{self.id}",
                                    "price": bid[f"bes_{self.id}"][0],
                                    "quantity": bid[f"bes_{self.id}"][1],
                                    "buyer": bid[f"bes_{self.id}"][2],
                                    "number": int(bid[f"bes_{self.id}"][3])})
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



    def formulate_bid(self, n_opt):
        nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh, config.options, config.districtData)
        bid_strategy = "zero"

        # range of prices
        p_max = params["eco"]["pr", "el"]
        p_min = params["eco"]["sell_chp"]

        # compute market agents for prosumer
        mar_agent_bes = []
        for n in range(config.options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh))

        # needed bid dictioanry
        bid = {}
        # Run rolling horizon
        init_val = {}  # not needed for first optimization, thus empty dictionary
        opti_res = {}  # to store the results of the bes optimization
        # Start optimizations
        for n_hours in range(par_rh["n_hours"]):
            opti_res[n_hours] = {}
            init_val[0] = {}
            init_val[n_hours+1] = {}

            if n_hours == 0:
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" +str(self.id) + ".")
                    init_val[n_hours]["building_" + str(self.id)] = {}
                    opti_res[n_hours][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                              building_params,
                                                              init_val[n_hours]["building_" + str(self.id)], n_opt, config.options)
                    init_val[n_hours + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(opti_res[n_hours][self.id],
                                                                                         par_rh, n_opt)
                    print(f"init_val_0: {init_val}")
            else:
                    print("Starting optimization: n_opt: " + str(n_opt) + ", building:" + str(self.id) + ".")
                    opti_res[n_hours][self.id] = config.decentral_operation(nodes[self.id], params, par_rh, building_params,
                                                             init_val[n_hours]["building_" + str(self.id)], n_opt, config.options)
                    if n_hours < par_rh["n_hours"] - 1:
                        init_val[n_hours + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(opti_res[n_hours][self.id], par_rh, n_opt)
                    else:
                        init_val[n_hours + 1] = 0
                    print(f"init_val: {init_val}")
            print("Finished optimization " + str(n_opt) + ". " + str((n_opt + 1) / par_rh["n_hours"] * 100) + "% of optimizations processed.")

            # compute bids
            bid[n_hours] = mar_pre.compute_bids(opti_res[n_hours], par_rh, mar_agent_bes, n_opt, config.options, self.id)

        print("bid: ")
        print(bid)
        print(bid[0])
        return bid[0]

