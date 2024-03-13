# import from filip
from filip.clients.ngsi_v2 import ContextBrokerClient
from filip.models.ngsi_v2.context import ContextEntity

# import form packages
import os
from dotenv import load_dotenv
import numpy as np
from pydantic import ConfigDict
import uuid
from enum import Enum
import requests
import json

# import from P2P_Market
import Filip.config as config

# import for data model
from Filip.data_model.Bid.PublishBid import PublishBid, CreatedDateTime, Price, Quantity
from Filip.data_model.Bid.FIWAREPublishBid import FiwarePublishBid, \
    CreatedDateTime as CDT, Price as Pr, Quantity as Qu, MarketRole as MR
from Filip.data_model.MarketParticipant.MarketParticipant import MarketParticipant
from Filip.data_model.MarketParticipant.FIWAREMarketParticipant import FiwareMarketParticipant

# Load environment variables from .env file
load_dotenv()

fiware_headers_bid = {
    'fiware-service': os.getenv('Service'),
    'fiware-servicepath': os.getenv('Service_path'),
    'Content-Type': 'application/json'}

fiware_headers_transaction = {
    'fiware-service': os.getenv('Service'),
    'fiware-servicepath': os.getenv('Service_path')}

# class Building:
class Building(MarketParticipant):
    model_config = ConfigDict(extra="allow")

    # def __init__(self, cbc: ContextBrokerClient, iotac: IoTAClient, id):
    # def __init__(self, cbc: ContextBrokerClient, iotac: IoTAClient, **data: Any):
    #     super().__init__(**data)
    #     self.cbc = cbc
    #     self.iotac = iotac
    # self.bid1 = {}  # todo (validation) get the bid from p2p market

    def add_fiware_interface(self, cbc: ContextBrokerClient):
        self.cbc = cbc

    def initial_fiware_information(self):
        # building entity id and type
        self.id = f"urn:ngsi-ld:Building:{self.userID}"
        self.type = "Building"
        # bid entity id and type
        self.bid_entity_id = f"urn:ngsi-ld:Bid:{self.userID}"
        self.bid_entity_type = "Bid"
        # transaction entity id and type
        self.transaction_entity_id = f"urn:ngsi-ld:Transaction:{self.userID}"
        # self.transaction_entity_type = "Transaction"
        self.transaction_topic = f"/v2/transactions/urn:ngsi-ld:Transaction:{self.userID}/attrs"
        # building entity
        self.building_entity_dict = self.create_building_entity()
        # bid entity
        self.bid_entity_dict = self.create_bid_entity()
        self.platform_configuration()
        self.bid = {}
        self.init_val = {}

    def publish_data(self, time_index):
        bid_to_publish = PublishBid(bidID=str(uuid.uuid4()),
                                    bidCreatedDateTime=CreatedDateTime(time=str(time_index)),
                                    expectedPrice=Price(price=self.bid[f"bes_{self.userID}"][0]),
                                    expectedQuantity=Quantity(quantity=self.bid[f"bes_{self.userID}"][1]),
                                    marketRole=self.bid[f"bes_{self.userID}"][2],
                                    refMarketParticipant=self.id)
        # data_to_publish = {"createdDateTime": time_index,
        #                    "bidround": n_opt,
        #                    "price": self.bid[f"bes_{self.id}"][0],
        #                    "quantity": self.bid[f"bes_{self.id}"][1],
        #                    "role": self.bid[f"bes_{self.id}"][2],
        #                    # "building_id": int(self.bid[f"bes_{self.id}"][3])
        #                    }

        # todo send the data from p2p market
        # data_to_publish = {"timestamp": time_index,
        #                    "name": f"bes_{self.id}",
        #                    "price": self.bid1[f"bes_{self.id}"][0],
        #                    "quantity": self.bid1[f"bes_{self.id}"][1],
        #                    "buyer": self.bid1[f"bes_{self.id}"][2],
        #                    "number": int(self.bid1[f"bes_{self.id}"][3])}
        # json_data = bid_schema(**data_to_publish)
        bid_dict = bid_to_publish.model_dump()
        json_bid = json.dumps(bid_dict)
        url = f"http://134.130.166.184:1026/v2/entities/urn:ngsi-ld:Bid:{self.userID}/attrs?options=keyValues"
        response = requests.request("PATCH", url, headers=fiware_headers_bid, data=json_bid)
        print(response.text)

    def create_building_entity(self):
        building_entity = FiwareMarketParticipant(id=self.id,
                                                  type=self.type,
                                                  buildingName=self.buildingName,
                                                  userID=self.userID,
                                                  refActiveBid=self.bid_entity_id,
                                                  refTransaction=self.transaction_entity_id
                                                  )
        # building_entity = ContextEntity(id=self.id,
        #                                 type=self.type
        #                                 )
        # building_name = NamedContextAttribute(name='buildingName',
        #                                       type="String",
        #                                       value=self.buildingName)
        # building_id = NamedContextAttribute(name='userID',
        #                                     type='String',
        #                                     value=self.userID)
        # building_bid = NamedContextAttribute(name='refActiveBid',
        #                                      type='Relationship',
        #                                      value=self.bid_entity_id)
        # building_transaction = NamedContextAttribute(name='refTransaction',
        #                                              type='Relationship',
        #                                              value=self.transaction_entity_id)
        # building_entity.add_attributes([building_name, building_id, building_bid, building_transaction])
        building_entity_pydantic_dict = building_entity.model_dump()
        building_entity_dict = self.utils_schema2fiware(building_entity_pydantic_dict)
        return building_entity_dict

    def create_bid_entity(self):
        bid_entity = FiwarePublishBid(id=self.bid_entity_id,
                                      type=self.bid_entity_type,
                                      bidID='Test',
                                      bidCreatedDateTime=CDT(time='Test'),
                                      expectedPrice=Pr(price=0),
                                      expectedQuantity=Qu(quantity=0),
                                      marketRole=MR.buyer,
                                      refMarketParticipant=self.id)

        # bid_entity = ContextEntity(id=self.bid_entity_id,
        #                            type=self.bid_entity_type)
        #
        # bid_id = NamedContextAttribute(name='bidID',
        #                                type="String")
        # bid_created_time = NamedContextAttribute(name='bidCreatedDateTime',
        #                                          type="String")
        # bid_price = NamedContextAttribute(name='expectedPrice',
        #                                   type='Float')
        # bid_quantity = NamedContextAttribute(name='expectedQuantity',
        #                                      type='Float')
        # bid_role = NamedContextAttribute(name='marketRole',
        #                                  type='String')
        # bid_building = NamedContextAttribute(name='refMarketParticipant',
        #                                      type='Relationship',
        #                                      value=self.id)
        # bid_entity.add_attributes([bid_id, bid_created_time, bid_price, bid_quantity, bid_role, bid_building])
        bid_entity_pydantic_dict = bid_entity.model_dump()
        bid_entity_dict = self.utils_schema2fiware(bid_entity_pydantic_dict)
        return bid_entity_dict

    def utils_schema2fiware(self, json_dict):
        # TODO turn plain value to structured value
        """
        input
        ------
        {
        'id': 'urn:ngsi-ld:Building:0',
        'type': 'Building'
        'buildingName': 'bes_0',
         ...
         ...
        }
        ----

        output
        {
        'id': 'urn:ngsi-ld:Building:0',
        'type': 'Building'
        'buildingName': {
                "type": "Text",
                "value": "bes_0"
        },
         ...
         ...
        }

        :param json_dict:
        :return:
        """
        entity_dict = {'id': json_dict['id'], 'type': json_dict['type']}  # Initialize entity_dict with id and type
        for key, attr in json_dict.items():
            if key not in ["type", "id"]:
                if isinstance(attr, Enum):
                    entity_dict[key] = {
                        "type": "Text",
                        "value": attr.value  # Get the string representation of the enum member
                    }
                elif isinstance(attr, str):  # Check if the attribute is a string
                    entity_dict[key] = {
                        "type": "Text",
                        "value": attr
                    }
                elif isinstance(attr, float):
                    entity_dict[key] = {
                        "type": "Float",
                        "value": attr
                    }
                elif isinstance(attr, dict):  # Check if the attribute is a dictionary
                    attr_list = list(attr.values())
                    attr_value = attr_list[0]
                    if isinstance(attr_value, str):  # Check if the inner attribute is a string
                        entity_dict[key] = {
                            "type": "Text",
                            "value": attr_value
                        }
                    elif isinstance(attr_value, float):
                        entity_dict[key] = {
                            "type": "Float",
                            "value": attr_value
                        }

        return entity_dict

    def platform_configuration(self):
        # create building and bid entities in context broker so that the device can send the payloads to match the
        # entities
        self.building_entity = ContextEntity(**self.building_entity_dict)
        self.cbc.post_entity(entity=self.building_entity)
        self.bid_entity = ContextEntity(**self.bid_entity_dict)
        self.cbc.post_entity(entity=self.bid_entity)

        # check in the context broker if the entities corresponding to the buildings
        print(self.cbc.get_entity(self.id))
        print(self.cbc.get_entity(self.bid_entity_id))

    def receive_transaction(self):
        # url = f"http://134.130.166.184:1026/v2/entities/urn:ngsi-ld:Transaction:{self.userID}/attrs?options=keyValues"
        # transaction = requests.get(url, headers=fiware_headers_transaction)
        # print(transaction.text)
        transaction = self.cbc.get_entity_attributes(entity_id=self.transaction_entity_id)
        print(transaction)

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

        # TODO optimize energy usage? also create a new class ComputeVolumes?
        if n_time == 0:
            print("Starting optimization: n_time: " + str(n_time) + ", building:" + str(self.userID) + ".")
            self.init_val[n_time]["building_" + str(self.userID)] = {}
            opti_res[n_time][self.userID] = config.decentral_operation(nodes[int(self.userID)], params, par_rh,
                                                                       building_params,
                                                                       self.init_val[n_time][
                                                                           "building_" + str(self.userID)],
                                                                       n_time,
                                                                       config.options)
            self.init_val[n_time + 1]["building_" + str(self.userID)] = config.init_val_decentral_operation(
                opti_res[n_time][self.userID],
                par_rh, n_time)
        else:
            opti_res[n_time][self.userID] = config.decentral_operation(nodes[int(self.userID)], params, par_rh,
                                                                       building_params,
                                                                       self.init_val[n_time][
                                                                           "building_" + str(self.userID)],
                                                                       n_time,
                                                                       config.options)
            if n_time < par_rh["n_hours"] - 1:
                self.init_val[n_time + 1]["building_" + str(self.userID)] = config.init_val_decentral_operation(
                    opti_res[n_time][self.userID], par_rh, n_time)
            else:
                self.init_val[n_time + 1] = 0

        # compute bids
        self.bid = ComputeBids(params).filip_compute_bids(opti_res[n_time], par_rh, n_time, config.options, self.userID)
        print("Finished optimization " + str(n_time) + ". " + str((n_time + 1) / par_rh["n_hours"] * 100) +
              "% of optimizations processed.")

        print("self.init_val:")
        print(self.init_val)

        print("self.bid:")
        print(self.bid)

    # send bid from p2p market to check the validation
    # def p2p_bid(self, n_time):
    #     # data from P2P_Market
    #     file_path1 = 'D:\jdu-zwu\P2P_Market\p2p_transaction.p'
    #     with open(file_path1, 'rb') as file:
    #         data1 = pickle.load(file)
    #     self.bid1[f'bes_{self.id}'] = data1['bid'][n_time][f'bes_{self.id}']
    #     print(f'p2p bid: {self.bid1}')


class ComputeBids:
    def __init__(self, params):
        # range of prices
        self.p_max = params["eco"]["pr", "el"]
        self.p_min = params["eco"]["sell_chp"]

    def compute_hp_bids(self, p_imp, n, bid_strategy):

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
            q = p_imp
            q_2 = 0
            p_2 = 0

        role = str("buyer")
        # p = np.around(p, decimals=4)
        # p_2 = np.around(p_2, decimals=4)

        return [p, q, role, n]

    def compute_chp_bids(self, chp_sell, n, bid_strategy):

        q = chp_sell
        role = str("seller")

        # compute bids with zero-intelligence
        if bid_strategy == "zero":
            # create random price between p_min and p_max
            p = np.random.randint(self.p_min * 100, self.p_max * 100) / 100
        p = np.around(p, decimals=6)

        return [p, q, role, n]

    def compute_empty_bids(self, n):

        p = 0
        q = 0
        role = str("buyer")

        return [p, q, role, n]

    def filip_compute_bids(self, opti_res, pars_rh, n_opt, options, n):

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
