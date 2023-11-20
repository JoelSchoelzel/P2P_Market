# import from filip
from filip.clients.ngsi_v2 import ContextBrokerClient, IoTAClient
from filip.models.ngsi_v2.subscriptions import Subscription
from filip.models.ngsi_v2.context import NamedContextAttribute, ContextEntity
from filip.models.base import FiwareHeader
from filip.models.ngsi_v2.iot import \
    Device, \
    DeviceAttribute, \
    ServiceGroup

# import form packages
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import time
import os
from dotenv import load_dotenv

# import from P2P_Market
import python.market_preprocessing as mar_pre
import python.bidding_strategies as bd
import config

# import for data model
import json

# Load environment variables from .env file
load_dotenv()
APIKEY = os.getenv('APIKEY')
# Create a service group and add it to your devices
service_group = ServiceGroup(apikey=APIKEY,
                             resource="/iot/json")

# Context Broker, IoT Agent and mqtt URL
CB_URL = os.getenv('CB_URL')
IOTA_URL = os.getenv('IOTA_URL')
MQTT_Broker_URL = os.getenv('MQTT_Broker_URL')

# Create the fiware header
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))



class Building:

    def __init__(self, id, cbc: ContextBrokerClient, iotac: IoTAClient):
        self.cbc = cbc
        self.iotac = iotac
        self.id = id
        self.device_id = f"device:{self.id}"
        self.entity_id = f"urn:ngsi-ld:Building:{self.id}"
        self.entity_type = "Building"
        self.device = self.building_device()
        self.building_entity = self.building_entity()
        self.initialization()
        self.mqtt_initialization()
        self.bid = {}
        self.init_val = {}

    def publish_data(self, time_index):
        with open('bid_schema.json', 'r') as f:
            bid_schema = json.load(f)

        data_to_publish = {"timestamp": time_index,
                           "name": f"bes_{self.id}",
                           "price": self.bid[f"bes_{self.id}"][0],
                           "quantity": self.bid[f"bes_{self.id}"][1],
                           "buyer": self.bid[f"bes_{self.id}"][2],
                           "number": int(self.bid[f"bes_{self.id}"][3])}

        json_data = bid_schema(**data_to_publish)
        # publish the device and data
        self.mqttc.publish(topic=f"/json/{APIKEY}/device:{self.id}/attrs",
                           payload=json_data)
        # wait for 0.1 second before publishing next values
        time.sleep(0.1)

    def building_entity(self):
        # TODO reasonable entity id and type
        building_entity = ContextEntity(id=self.entity_id,
                                        type=self.entity_type)

        t_bidtime = NamedContextAttribute(name='bidtime',
                                          type="String")
        t_name = NamedContextAttribute(name='name',
                                       type="String")
        t_price = NamedContextAttribute(name='price',
                                        type='Number')
        t_quantity = NamedContextAttribute(name='quantity',
                                           type='Number')
        t_buyer = NamedContextAttribute(name='buyer',
                                        type='String')
        t_numer = NamedContextAttribute(name='number',
                                        type='Number')
        building_entity.add_attributes([t_bidtime, t_name, t_price, t_quantity, t_buyer, t_numer])
        return building_entity

    def building_device(self):
        building = Device(device_id=self.device_id,
                          entity_name=self.entity_id,
                          entity_type="Building",
                          protocol='IoTA-JSON',
                          transport='MQTT',
                          apikey=os.getenv('APIKEY'),
                          commands=[])
        return building

    def initialization(self):
        # Subscription in context broker so that the transaction can be received by mqtt clients
        subscription = {
            "description": "Subscription to receive MQTT-Notification about "
                           f"urn:ngsi-ld:Transaction:{self.id}",
            "subject": {
                "entities": [
                    {
                        "id": f"urn:ngsi-ld:Transaction:{self.id}",
                        "type": "Transaction"
                    }
                ]
            },
            "notification": {
                "mqtt": {
                    "url": MQTT_Broker_URL,
                    "topic": f"/v2/transactions/urn:ngsi-ld:Transaction:{self.id}/attrs"
                }
            }
        }
        subscription = Subscription(**subscription)
        self.cbc.post_subscription(subscription=subscription)
        # create bids entities in context broker so that the device can send the payloads to match the entities
        self.cbc.post_entity(entity=self.building_entity)
        # Provision service group and add it to IOTAClient
        self.iotac.post_group(service_group=service_group, update=True)
        # Provision the devices at the Iota-agent
        self.iotac.post_device(device=self.device, update=True)
        # check in the context broker if the entities corresponding to the buildings
        print(self.cbc.get_entity(self.device.entity_name))

    def mqtt_initialization(self):
        # create an MQTTv5 Client
        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"/json/{APIKEY}/device:{self.id}/attrs")
            print("Connected with result code" + str(rc))

        def on_message(client, userdata, msg):
            print(msg.topic + " " + str(msg.payload))

        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = on_connect
        self.mqttc.on_message = on_message

        self.mqttc.connect("134.130.166.184", 1883, 60)

        self.mqttc.loop_start()

    def formulate_bid(self, n_time):
        nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh,
                                                                                            config.options,
                                                                                            config.districtData)
        bid_strategy = "zero"

        # range of prices
        p_max = params["eco"]["pr", "el"]
        p_min = params["eco"]["sell_chp"]

        # compute market agents for prosumer
        mar_agent_bes = []
        for n in range(config.options["nb_bes"]):
            mar_agent_bes.append(bd.mar_agent_bes(p_max, p_min, par_rh))

        # Run rolling horizon
        init_val = {}  # not needed for first optimization, thus empty dictionary
        opti_res = {}  # to store the results of the bes optimization

        bid = {}

        # Start optimizations
        if n_time == 0:
            for n_opt in range(par_rh["n_hours"]):
                opti_res[n_opt] = {}
                init_val[0] = {}
                init_val[n_opt + 1] = {}

                if n_opt == 0:
                    print("Starting optimization: n_opt: " + str(n_time) + ", building:" + str(self.id) + ".")
                    init_val[n_opt]["building_" + str(self.id)] = {}
                    opti_res[n_opt][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                          building_params,
                                                                          init_val[n_opt]["building_" + str(self.id)],
                                                                          n_opt,
                                                                          config.options)
                    init_val[n_opt + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                        opti_res[n_opt][self.id],
                        par_rh, n_opt)
                else:
                    opti_res[n_opt][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                          building_params,
                                                                          init_val[n_opt]["building_" + str(self.id)],
                                                                          n_opt,
                                                                          config.options)
                    if n_opt < par_rh["n_hours"] - 1:
                        init_val[n_opt + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                            opti_res[n_opt][self.id], par_rh, n_opt)
                    else:
                        init_val[n_opt + 1] = 0
                    # compute bids
                bid[n_opt] = mar_pre.filip_compute_bids(opti_res[n_opt], par_rh, mar_agent_bes, n_opt, config.options,
                                                        self.id)
                print("Finished optimization " + str(n_opt) + ". " + str(
                    (n_opt + 1) / par_rh["n_hours"] * 100) + "% of optimizations processed.")

        else:
            for n_opt in range(n_time, par_rh["n_hours"] + n_time):
                opti_res[n_opt] = {}
                init_val[n_time] = {}
                init_val[n_opt + 1] = {}
                if n_opt == n_time:
                    print("Starting optimization: n_opt: " + str(n_time) + ", building:" + str(self.id) + ".")
                    init_val[n_time]["building_" + str(self.id)] = self.init_val
                    opti_res[n_opt][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                          building_params,
                                                                          init_val[n_time]["building_" + str(self.id)],
                                                                          n_opt, config.options)
                    init_val[n_opt + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                        opti_res[n_opt][self.id], par_rh, n_opt)
                else:
                    opti_res[n_opt][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                          building_params,
                                                                          init_val[n_opt]["building_" + str(self.id)],
                                                                          n_opt, config.options)
                    if n_opt < par_rh["n_hours"] + n_time - 1:
                        init_val[n_opt + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                            opti_res[n_opt][self.id], par_rh, n_opt)
                    else:
                        init_val[n_opt + 1] = 0
                    # compute bids
                bid[n_opt] = mar_pre.filip_compute_bids(opti_res[n_opt], par_rh, mar_agent_bes, n_opt, config.options,
                                                        self.id)
                print("Finished optimization " + str(n_opt) + ". " + str(
                    (n_opt + 1) / par_rh["n_hours"] * 100) + "% of optimizations processed.")

        self.init_val = init_val[n_time + 1]["building_" + str(self.id)]
        self.bid = bid[n_time]
        print("init_val")
        print(init_val)
        print("init_:")
        print("self.init_val")
        print(self.init_val)
        print("bid: ")
        print(bid)
        print("self.bid:")
        print(self.bid)
