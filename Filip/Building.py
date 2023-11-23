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
import time
import os
from dotenv import load_dotenv
import numpy as np
import pickle
# import from P2P_Market
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
        self.bid1 = {} #todo get the bid from p2p market

    def publish_data(self, time_index):
        # with open('bid_schema.json', 'r') as f:
        #     bid_schema = json.load(f)

        # data_to_publish = {"timestamp": time_index,
        #                    "name": f"bes_{self.id}",
        #                    "price": self.bid[f"bes_{self.id}"][0],
        #                    "quantity": self.bid[f"bes_{self.id}"][1],
        #                    "buyer": self.bid[f"bes_{self.id}"][2],
        #                    "number": int(self.bid[f"bes_{self.id}"][3])}

        #todo send the data from p2p market
        data_to_publish = {"timestamp": time_index,
                           "name": f"bes_{self.id}",
                           "price": self.bid1[f"bes_{self.id}"][0],
                           "quantity": self.bid1[f"bes_{self.id}"][1],
                           "buyer": self.bid1[f"bes_{self.id}"][2],
                           "number": int(self.bid1[f"bes_{self.id}"][3])}
        # json_data = bid_schema(**data_to_publish)
        json_data = json.dumps(data_to_publish)
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
        # Get following inputs from config
        nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh,
                                                                                            config.options,
                                                                                            config.districtData)
        bid_strategy = "zero"

        # Run rolling horizon
        opti_res = {n_time: {}}  # to store the results of the bes optimization

        self.init_val[0] = {}
        self.init_val[n_time + 1] = {}

        if n_time == 0:
            print("Starting optimization: n_time: " + str(n_time) + ", building:" + str(self.id) + ".")
            self.init_val[n_time]["building_" + str(self.id)] = {}
            opti_res[n_time][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                   building_params,
                                                                   self.init_val[n_time]["building_" + str(self.id)],
                                                                   n_time,
                                                                   config.options)
            self.init_val[n_time + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                opti_res[n_time][self.id],
                par_rh, n_time)
        else:
            opti_res[n_time][self.id] = config.decentral_operation(nodes[self.id], params, par_rh,
                                                                   building_params,
                                                                   self.init_val[n_time]["building_" + str(self.id)],
                                                                   n_time,
                                                                   config.options)
            if n_time < par_rh["n_hours"] - 1:
                self.init_val[n_time + 1]["building_" + str(self.id)] = config.init_val_decentral_operation(
                    opti_res[n_time][self.id], par_rh, n_time)
            else:
                self.init_val[n_time + 1] = 0

        # compute bids
        self.bid = Compute_Bids(params=params).filip_compute_bids(opti_res[n_time], par_rh, n_time, config.options, self.id)
        print("Finished optimization " + str(n_time) + ". " + str((n_time + 1) / par_rh["n_hours"] * 100) +
              "% of optimizations processed.")

        print("self.init_val:")
        print(self.init_val)

        print("self.bid:")
        print(self.bid)

    # send bid from p2p market to check the validation
    def p2p_bid(self, n_time):
        # data from P2P_Market
        file_path1 = 'D:\jdu-zwu\P2P_Market\p2p_transaction.p'
        with open(file_path1, 'rb') as file:
            data1 = pickle.load(file)
        self.bid1[f'bes_{self.id}'] = data1['bid'][n_time][f'bes_{self.id}']
        print(f'p2p bid: {self.bid1}')

class Compute_Bids:

    def __init__(self, params):
        # range of prices
        self.p_max = params["eco"]["pr", "el"]
        self.p_min = params["eco"]["sell_chp"]

    def compute_hp_bids(self, p_imp, n, bid_strategy):

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100 #TODO set the price
            q = p_imp
            q_2 = 0
            p_2 = 0

        buying = str("True")
        #p = np.around(p, decimals=4)
        #p_2 = np.around(p_2, decimals=4)

        return [p, q, buying, n]


    def compute_chp_bids(self, chp_sell, n, bid_strategy):


        q = chp_sell
        buying = str("False")

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100 #TODO set the
        p = np.around(p, decimals=6)

        return [p, q, buying, n]


    def compute_empty_bids(self, n):

        p = 0
        q = 0
        buying = str("True")

        return [p, q, buying, n]

    def filip_compute_bids(self, opti_res, pars_rh, n_opt, options, n):  # TODO This one refers to Filip

        bid = {}

        # for n in range(len(opti_res)):
        # get parameters for bidding
        t = pars_rh["time_steps"][n_opt][0]
        p_imp = opti_res[n][4][t]
        chp_sell = opti_res[n][8]["chp"][t]
        bid_strategy = options["bid_strategy"]

        # compute bids
        if p_imp > 0.0:
            bid["bes_" + str(n)] = self.compute_hp_bids(p_imp=p_imp, n=n, bid_strategy=bid_strategy)
            # a = bd.compute_hp_bids()
            # bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = bid["bes_" + str(n)][1]

        elif chp_sell > 0:
            bid["bes_" + str(n)] = self.compute_chp_bids(chp_sell, n, bid_strategy)
            # bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = 0

        else:
            bid["bes_" + str(n)] = self.compute_empty_bids(n)
            # bes[n]["hp_dem"][n_opt, t-pars_rh["hour_start"][n_opt]] = 0

        return bid