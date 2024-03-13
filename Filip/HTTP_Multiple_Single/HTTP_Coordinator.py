#  import from P2P_Market
import Filip.config as config
import python.characteristics as characs
from filip.models.ngsi_v2.context import ContextEntity
# from filip.models.base import FiwareHeader
from filip.clients.ngsi_v2 import ContextBrokerClient, QuantumLeapClient
from filip.models.ngsi_v2.subscriptions import Subscription
import os
from dotenv import load_dotenv
from Filip.data_model.Transaction.PublishTransaction import PublishTransaction, CreatedDateTime, TradeInformation, \
    Price, Quantity, PowerDirection
from Filip.data_model.Transaction.FIWAREPublishTransaction import FiwarePublishTransaction, CreatedDateTime as CDT, \
    TradeInformation as TI, \
    Price as Pr, Quantity as Qu, PowerDirection as Po
import uuid
import json
import requests

# Load environment variables from .env file
load_dotenv()

# fiware_header = FiwareHeader(service=os.getenv('Service'),
#                              service_path=os.getenv('Service_path'))
fiware_headers = {
    'fiware-service': os.getenv('Service'),
    'fiware-servicepath': os.getenv('Service_path'),
    'Content-Type': 'application/json'}


class Coordinator:

    def __init__(self, cbc: ContextBrokerClient, qlc: QuantumLeapClient, buildings):
        self.transaction_entity: ContextEntity
        self.cbc = cbc
        self.qlc = qlc
        self.buildings = buildings
        self.building_entity = {}
        self.bid_entity = {}
        self.bid = {}
        self.sorted_bids = {}
        self.transactions = {}
        self.transactions2 = {}
        self.transaction_entity_id = None
        self.transaction_entity_type = "Transaction"
        self.transaction_to_publish = None

    def platform_configuration(self, number_building):
        # Provision service group and add it to IOTAClient
        self.transaction_entity_dict = self.create_transaction_attributes(number_building)
        self.post_transaction_entities()
        with open('historic_transaction_subscription.json') as f:
            historic_transaction_subscription_dict = json.load(f)
            historic_transaction_subscription_dict['subject']['entities'][0][
                'id'] = f"urn:ngsi-ld:Transaction:{number_building}"
            historic_transaction_subscription_dict['subject']['entities'][0]['type'] = self.transaction_entity_type
            historic_transaction_subscription_dict['subject']['condition']['attrs'] = 'transactionID'
            historic_transaction_subscription = Subscription(**historic_transaction_subscription_dict)
        self.cbc.post_subscription(subscription=historic_transaction_subscription)

    def create_transaction_attributes(self, number_building):
        transaction_entity = FiwarePublishTransaction(id=f"urn:ngsi-ld:Transaction:{number_building}",
                                                      type=self.transaction_entity_type,
                                                      transactionID='Test',
                                                      transactionCreatedDateTime=CDT(time='Test'),
                                                      tradeResults=[],
                                                      refMarketParticipant='Test')
        # transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{number_building}",
        #                                    type=self.transaction_entity_type)
        # transaction_id = NamedContextAttribute(name='transactionID',
        #                                        type='Text')
        # transaction_created_time = NamedContextAttribute(name='transactionCreatedDateTime',
        #                                                  type='DateTime')
        # transaction_results = NamedContextAttribute(name='tradeResults',
        #                                             type='StructuredValue')
        # transaction_building = NamedContextAttribute(name='refMarketParticipant',
        #                                              type='Text')
        # transaction_entity.add_attributes(
        #     [transaction_id, transaction_created_time, transaction_results, transaction_building])
        transaction_entity_pydantic_dict = transaction_entity.model_dump()
        transaction_entity_dict = self.utils_schema2fiware(transaction_entity_pydantic_dict)
        return transaction_entity_dict

    def utils_schema2fiware(self, json_dict):
        entity_dict = {'id': json_dict['id'], 'type': json_dict['type']}  # Initialize entity_dict with id and type
        for key, attr in json_dict.items():
            if key not in ["type", "id"]:
                if isinstance(attr, list):
                    entity_dict[key] = {
                        "type": "StructuredValue",
                        "value": attr  # Get the list of the trading results
                    }
                elif isinstance(attr, str):  # Check if the attribute is a string
                    entity_dict[key] = {
                        "type": "Text",
                        "value": attr
                    }
                elif isinstance(attr, float):  # Check if the attribute is a float
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

    def post_transaction_entities(self):
        self.transaction_entity = ContextEntity(**self.transaction_entity_dict)
        self.cbc.post_entity(entity=self.transaction_entity)

    def get_bids(self):
        for i in range(len(self.buildings)):
            self.building_entity = self.cbc.get_entity(self.buildings[i].id)
            self.bid_entity = self.cbc.get_entity(self.building_entity.refActiveBid.value)
            attributes = [self.bid_entity.expectedPrice.value['price'],
                          self.bid_entity.expectedQuantity.value['quantity'],
                          self.bid_entity.marketRole.value, int(self.building_entity.userID.value)]
            self.bid[self.building_entity.buildingName.value] = attributes

    def sort_bids(self):
        nodes, building_params, params, devs_pre_opti, net_data, par_rh = config.get_inputs(config.par_rh,
                                                                                            config.options,
                                                                                            config.districtData)
        characteristics = characs.calc_characs(nodes, config.options, par_rh)

        buy_list = {}
        sell_list = {}

        # sort by buy or sell
        for n in range(len(self.bid)):

            # don't consider bids with zero quantity
            if float(self.bid["bes_" + str(n)][1]) != 0.0:

                # add buying bids to buy_list
                if self.bid["bes_" + str(n)][2] == "buyer":
                    i = len(buy_list)
                    buy_list[i] = {
                        "price": self.bid["bes_" + str(n)][0],
                        "quantity": self.bid["bes_" + str(n)][1],
                        "building": self.bid["bes_" + str(n)][3]
                    }

                # add selling bids to sell_list
                if self.bid["bes_" + str(n)][2] == "seller":
                    i = len(sell_list)
                    sell_list[i] = {
                        "price": self.bid["bes_" + str(n)][0],
                        "quantity": self.bid["bes_" + str(n)][1],
                        "building": self.bid["bes_" + str(n)][3]
                    }

        if config.options["crit_prio"] == "price":
            # sort lists by price
            if config.options["descending"]:
                # highest paying and lowest asking first
                sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"], reverse=True)
                sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"])
            else:
                # lowest paying and highest asking first
                sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["price"])
                sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["price"], reverse=True)

        else:
            for i in range(len(buy_list)):
                buy_list[i]["crit"] = characteristics[buy_list[i]["building"]][config.options["crit_prio"]]
            for i in range(len(sell_list)):
                sell_list[i]["crit"] = characteristics[sell_list[i]["building"]][config.options["crit_prio"]]

            if config.options["descending"]:
                sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"], reverse=True)
                sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"], reverse=True)
            else:
                sorted_buy_list = sorted(buy_list.items(), key=lambda x: x[1]["crit"])
                sorted_sell_list = sorted(sell_list.items(), key=lambda x: x[1]["crit"])
        self.sorted_bids = {
            "buy": {},
            "sell": {}
        }

        for i in range(len(sorted_buy_list)):
            self.sorted_bids["buy"][i] = sorted_buy_list[i][1]
        for i in range(len(sorted_sell_list)):
            self.sorted_bids["sell"][i] = sorted_sell_list[i][1]

        print(self.sorted_bids)

    def get_transactions2(self, max_rounds):
        """
        Runs auction with multiple trading rounds.
        Buying and selling bids are matched based on position. If the price of the buying bid is greater than the price of
        the selling bid, the minimum quantity of both bids is traded. This is done for all matches.
        Afterwards all bids that haven't been fully fulfilled are added to the next trading round. The prices of buying bids
        are increased and selling bids are decreased by a specified factor.
        This is repeated until no buying or selling bids remain or the maximum number of trading rounds is reached.

        Returns:
            transactions (dict): Dictionary with all transactions made.
            bids (dict): Bids with remaining quantities and changed prices.
        """

        count_trans = 0  # count of transaction

        # k for k-pricing method
        kappa = 0.5

        # factor to change price each round by
        f_buy = 1.05
        f_sell = 0.95

        n = 0  # round of trading

        # if max_rounds has been set to 0 for unlimited trading rounds, 1000 is used to prevent a never ending loop
        if max_rounds == 0:
            max_rounds = 1000

        # create dict for first trading round using bids from dict "sorted bids"
        bids = {n: self.sorted_bids}

        # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
        while len(bids[n]["sell"]) > 0 and len(bids[n]["buy"]) > 0 and n < max_rounds:

            # iterate through the previously sorted bids, prio is the position the bids are in
            for prio in range(min(len(bids[n]["sell"]), len(bids[n]["buy"]))):

                # check whether the buying and selling bid in the same position can be matched
                if bids[n]["buy"][prio]["price"] >= bids[n]["sell"][prio]["price"]:
                    # determine transaction price using k-pricing method
                    transaction_price = bids[n]["buy"][prio]["price"] + kappa * (bids[n]["sell"][prio]["price"] -
                                                                                 bids[n]["buy"][prio]["price"])

                    # quantity is minimum of both
                    transaction_quantity = min(bids[n]["sell"][prio]["quantity"], bids[n]["buy"][prio]["quantity"])

                    # add transaction to the dict to keep record
                    self.transactions2[count_trans] = {
                        "buyer": bids[n]["buy"][prio]["building"],
                        "seller": bids[n]["sell"][prio]["building"],
                        "price": transaction_price,
                        "quantity": transaction_quantity,
                        "trading_round": (n + 1)
                    }
                    count_trans += 1

                    # subtract quantity that has been traded from the bids
                    bids[n]["sell"][prio]["quantity"] -= transaction_quantity
                    bids[n]["buy"][prio]["quantity"] -= transaction_quantity

            # create dicts for next trading round
            bids[n + 1] = {"buy": {}, "sell": {}}

            # add unsatisfied buying bids to next trading round and multiply price by factor f_buy to increase it
            p_buy = 0
            for i in range(len(bids[n]["buy"])):
                if bids[n]["buy"][i]["quantity"] > 0:
                    bids[n + 1]["buy"][p_buy] = bids[n]["buy"][i].copy()
                    bids[n + 1]["buy"][p_buy]["price"] = bids[n]["buy"][i]["price"] * f_buy
                    p_buy += 1

            # add unsatisfied selling bids to next trading round and multiply price by factor f_sell to decrease it
            p_sell = 0
            for i in range(len(bids[n]["sell"])):
                if bids[n]["sell"][i]["quantity"] > 0:
                    bids[n + 1]["sell"][p_sell] = bids[n]["sell"][i].copy()
                    bids[n + 1]["sell"][p_sell]["price"] = bids[n]["sell"][i]["price"] * f_sell
                    p_sell += 1

            # go to next trading round
            n += 1

    def calculate_transactions_multiple(self):
        count_trans = 0  # count of transaction

        # k for k-pricing method
        kappa = 0.5

        # amount to change price each round
        dp_buy = 0.05
        dp_sell = -0.05

        n = 0  # round of trading

        # create dict for first trading round with sorted bids
        bids = {n: self.sorted_bids}

        # start new round of trading while potential buyers and sellers exist and maximum number of rounds isn't reached
        while len(bids[n]["sell"]) != 0 and len(bids[n]["buy"]) != 0 and n < 5:

            # iterate through priorities
            for prio in range(max(len(bids[n]["sell"]), len(bids[n]["buy"]))):

                # check whether buyer on position "prio" exists and finds match
                if prio < len(bids[n]["buy"]) and bids[n]["buy"][prio]["quantity"] > 0:
                    # iterate through potential sellers
                    for k in range(len(bids[n]["sell"])):
                        # check whether trade is possible
                        if bids[n]["buy"][prio]["price"] >= bids[n]["sell"][k]["price"] and bids[n]["sell"][k][
                            "quantity"] > 0:
                            # determine transaction price using k-pricing method
                            transaction_price = bids[n]["buy"][prio]["price"] + kappa * (
                                    bids[n]["sell"][k]["price"] - bids[n]["buy"][prio]["price"])

                            # quantity is minimum of both
                            transaction_quantity = min(bids[n]["sell"][k]["quantity"], bids[n]["buy"][prio]["quantity"])

                            # add transaction
                            self.transactions[count_trans] = {
                                "buyer": bids[n]["buy"][prio]["building"],
                                "seller": bids[n]["sell"][k]["building"],
                                "price": transaction_price,
                                "quantity": transaction_quantity
                            }
                            count_trans += 1

                            # subtract quantity and break loop when buyer is satisfied
                            bids[n]["sell"][k]["quantity"] -= transaction_quantity
                            bids[n]["buy"][prio]["quantity"] -= transaction_quantity
                            if bids[n]["buy"][prio]["quantity"] == 0:
                                break

                # check whether seller on position "prio" exists and finds match
                if prio < len(bids[n]["sell"]) and bids[n]["sell"][prio]["quantity"] > 0:
                    # iterate through potential buyers
                    for k in range(len(bids[n]["buy"])):
                        # check whether trade is possible
                        if bids[n]["buy"][k]["price"] >= bids[n]["sell"][prio]["price"] and bids[n]["buy"][k][
                            "quantity"] > 0:

                            # determine transaction price using k-pricing method
                            transaction_price = bids[n]["buy"][k]["price"] + kappa * (
                                    bids[n]["sell"][prio]["price"] - bids[n]["buy"][k]["price"])

                            # quantity is minimum of both
                            transaction_quantity = min(bids[n]["sell"][prio]["quantity"], bids[n]["buy"][k]["quantity"])

                            # add transaction
                            self.transactions[count_trans] = {
                                "buyer": bids[n]["buy"][k]["building"],
                                "seller": bids[n]["sell"][prio]["building"],
                                "price": transaction_price,
                                "quantity": transaction_quantity
                            }
                            count_trans += 1

                            # subtract quantity and break loop when seller is satisfied
                            bids[n]["sell"][prio]["quantity"] -= transaction_quantity
                            bids[n]["buy"][k]["quantity"] -= transaction_quantity
                            if bids[n]["sell"][prio]["quantity"] == 0:
                                break

            # add unsatisfied bids to next trading round and change price

            p_buy = 0
            bids[n + 1] = {"buy": {}, "sell": {}}
            for i in range(len(bids[n]["buy"])):
                if bids[n]["buy"][i]["quantity"] > 0:
                    bids[n + 1]["buy"][p_buy] = bids[n]["buy"][i].copy()
                    bids[n + 1]["buy"][p_buy]["price"] = bids[n]["buy"][i]["price"] + dp_buy
                    p_buy += 1

            p_sell = 0
            for i in range(len(bids[n]["sell"])):
                if bids[n]["sell"][i]["quantity"] > 0:
                    bids[n + 1]["sell"][p_sell] = bids[n]["sell"][i].copy()
                    bids[n + 1]["sell"][p_sell]["price"] = bids[n]["sell"][i]["price"] + dp_sell
                    p_sell += 1

            # go to next trading round
            n += 1

    def calculate_transactions_single(self):

        # as shown in chapter 2 in: Chen, 2019

        # k for k-pricing method
        k = 0.5

        if len(self.sorted_bids["sell"]) != 0 and len(self.sorted_bids["buy"]) != 0:
            # create indices
            i = 0  # position of seller
            j = 0  # position of buyer
            m = 0  # count of transaction

            # continue matching until no price matches can be found
            while self.sorted_bids["sell"][i]["price"] <= self.sorted_bids["buy"][j]["price"]:

                # determine transaction price using k-pricing method
                transaction_price = self.sorted_bids["buy"][j]["price"] + k * (self.sorted_bids["sell"][i]["price"] - self.sorted_bids["buy"][j]["price"])

                # quantity is minimum of both
                transaction_quantity = min(self.sorted_bids["sell"][i]["quantity"], self.sorted_bids["buy"][j]["quantity"])

                # add transaction
                self.transactions[m] = {}
                self.transactions[m]["buyer"] = self.sorted_bids["buy"][j]["building"]
                self.transactions[m]["seller"] = self.sorted_bids["sell"][i]["building"]
                self.transactions[m]["price"] = transaction_price
                self.transactions[m]["quantity"] = transaction_quantity
                m += 1
                self.sorted_bids["sell"][i]["quantity"] = self.sorted_bids["sell"][i]["quantity"] - transaction_quantity
                if self.sorted_bids["sell"][i]["quantity"] == 0:
                    i += 1
                self.sorted_bids["buy"][j]["quantity"] = self.sorted_bids["buy"][j]["quantity"] - transaction_quantity
                if self.sorted_bids["buy"][j]["quantity"] == 0:
                    j += 1
                if i == len(self.sorted_bids["sell"]) or j == len(self.sorted_bids["buy"]):
                    break

    def reformat_publish_transaction(self, start_datetime):
        # add the relevant information from transaction to the corresponding building entity
        # once the transaction entity is created, it will be published to context broker
        for cleints in range(len(self.buildings)):
            # Build buy and sell dictionary from the transaction
            buyer_dic = {}
            seller_dic = {}
            transaction_list = []
            transaction = {}
            # if the transactions are not empty
            if self.transactions:
                for n in range(len(self.transactions)):
                    buyer_dic[n] = {}
                    buyer_dic[n] = self.transactions[n]['buyer']
                    seller_dic[n] = {}
                    seller_dic[n] = self.transactions[n]['seller']

                # if the building hasn't transaction neither the buyer nor seller
                if cleints not in buyer_dic.values() and cleints not in seller_dic.values():
                    # self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                         type=self.transaction_entity_type)
                    TradeResults = []
                    self.transaction_to_publish = PublishTransaction(transactionID=str(uuid.uuid4()),
                                                                     transactionCreatedDateTime=CreatedDateTime(
                                                                         time=str(start_datetime)),
                                                                     tradeResults=TradeResults,
                                                                     refMarketParticipant=f"urn:ngsi-ld:Building:{cleints}")
                    # transaction_dict = self.transaction_to_publish.dict()
                    # json_transaction = json.dumps(transaction_dict)

                    # attribute_test = NamedContextAttribute(
                    #     name="my_attributes",
                    #     type="StructuredValue",
                    #     value={
                    #         "time": str(n_opt),
                    #         "result": "No Transaction",
                    #     })
                    # self.transaction_entity.add_attributes([transaction_dict])
                    # self.cbc.update_attribute_value(entity_id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                 attr_name='transactionID',
                    #                                 value=str(uuid.uuid4()))
                    # self.cbc.update_attribute_value(entity_id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                 attr_name='transactionCreatedDateTime',
                    #                                 value=CreatedDateTime(time=str(n_opt)))
                    # self.cbc.update_attribute_value(entity_id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                 attr_name='tradeResults',
                    #                                 value=None)
                    # self.cbc.update_attribute_value(entity_id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                 attr_name='refMarketParticipant',
                    #                                 value=f"urn:ngsi-ld:Building:{cleints}")
                # if the building is a buyer
                if cleints in buyer_dic.values():
                    for key, value in buyer_dic.items():
                        if value == cleints:
                            transaction['Price'] = self.transactions[key]['price']
                            transaction['Quantity'] = self.transactions[key]['quantity']
                            transaction['Seller'] = self.transactions[key]['seller']
                            transaction_list.append(transaction.copy())

                    TradeResults = [TradeInformation(realPrice=Price(price=transaction_item['Price']),
                                                     realQuantity=Quantity(quantity=transaction_item['Quantity']),
                                                     powerDirection=PowerDirection(tradingObjectRole='seller',
                                                                                   tradingObjectID=f"{transaction_item['Seller']}"))
                                    for transaction_item in transaction_list]
                    # self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                         type=self.transaction_entity_type)
                    self.transaction_to_publish = PublishTransaction(transactionID=str(uuid.uuid4()),
                                                                     transactionCreatedDateTime=CreatedDateTime(
                                                                         time=str(start_datetime)),
                                                                     tradeResults=TradeResults,
                                                                     refMarketParticipant=f"urn:ngsi-ld:Building:{cleints}")
                    # attribute_test = NamedContextAttribute(
                    #     name="my_attributes",
                    #     type="StructuredValue",
                    #     value={
                    #         "time": str(n_opt),
                    #         "buyer": f"{cleints}",
                    #         # "seller": "Zehao",
                    #         "transaction": transaction_list
                    #     })
                    # self.transaction_entity.add_attributes([attribute_test])
                    transaction_list.clear()
                    # self.cbc.patch_entity(entity=self.transaction_entity)

                    # if the building is a seller
                else:
                    for key, value in seller_dic.items():
                        if value == cleints:
                            transaction['Price'] = self.transactions[key]['price']
                            transaction['Quantity'] = self.transactions[key]['quantity']
                            transaction['Buyer'] = self.transactions[key]['buyer']
                            transaction_list.append(transaction.copy())

                    TradeResults = [TradeInformation(realPrice=Price(price=transaction_item['Price']),
                                                     realQuantity=Quantity(quantity=transaction_item['Quantity']),
                                                     powerDirection=PowerDirection(tradingObjectRole='buyer',
                                                                                   tradingObjectID=f"{transaction_item['Buyer']}"))
                                    # f"buyer: {transaction_item['Buyer']}")
                                    for transaction_item in transaction_list]

                    self.transaction_to_publish = PublishTransaction(transactionID=str(uuid.uuid4()),
                                                                     transactionCreatedDateTime=CreatedDateTime(
                                                                         time=str(start_datetime)),
                                                                     tradeResults=TradeResults,
                                                                     refMarketParticipant=f"urn:ngsi-ld:Building:{cleints}")
                    # self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                    #                                         type=self.transaction_entity_type)
                    # attribute_test = NamedContextAttribute(
                    #     name="my_attributes",
                    #     type="StructuredValue",
                    #     value={
                    #         "time": str(n_opt),
                    #         # "buyer": "Junsong",
                    #         "seller": f"{cleints}",
                    #         "transaction": transaction_list
                    #     })
                    # self.transaction_entity.add_attributes([attribute_test])
                    transaction_list.clear()
                    # self.cbc.patch_entity(entity=self.transaction_entity)

            # if the transactions are empty
            else:
                TradeResults = []
                self.transaction_to_publish = PublishTransaction(transactionID=str(uuid.uuid4()),
                                                                 # transactionCreatedDateTime=str(start_datetime),
                                                                 transactionCreatedDateTime=CreatedDateTime(
                                                                     time=str(start_datetime)),
                                                                 tradeResults=TradeResults,
                                                                 refMarketParticipant=f"urn:ngsi-ld:Building:{cleints}")
                # self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                #                                         type=self.transaction_entity_type)
                # attribute_test = NamedContextAttribute(
                #     name="my_attributes",
                #     type="StructuredValue",
                #     value={
                #         "time": str(n_opt),
                #         "result": "No Transaction",
                #     })
                # self.transaction_entity.add_attributes([attribute_test])
            # self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
            #                                         type=self.transaction_entity_type)
            transaction_dict = self.transaction_to_publish.model_dump()

            # TODO try request
            url = f"http://134.130.166.184:1026/v2/entities/urn:ngsi-ld:Transaction:{cleints}/attrs?options=keyValues"
            payload = json.dumps(transaction_dict)
            # res = ....post(url=url,  # todo .../entities/id/attrs
            #                 headers=fiware_header,
            #                 json=transaction_dict,
            #                 params=params)
            response = requests.request("PATCH", url, headers=fiware_headers, data=payload)
            print(response.text)
            # self.transaction_entity.add_attributes(transaction_dict)

            # transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
            #                                    type=self.transaction_entity_type
            #                                    )
            # transaction_id = NamedContextAttribute(name='transactionID',
            #                                        type='Text',
            #                                        value=transaction_dict["transactionID"]
            #                                        )
            # transaction_created_time = NamedContextAttribute(name='transactionCreatedDateTime',
            #                                                  type='DateTime',
            #                                                  value=transaction_dict["transactionCreatedDateTime"]
            #                                                  )
            # transaction_results = NamedContextAttribute(name='tradeResults',
            #                                             type='StructuredValue',
            #                                             value=transaction_dict["tradeResults"]
            #                                             )
            # transaction_building = NamedContextAttribute(name='refMarketParticipant',
            #                                              type='Text',
            #                                              value=transaction_dict["refMarketParticipant"]
            #                                              )
            # TODO transaction_entity = self.transaction_to_publish.model_dump()
            # fiwarePublishTransaction = FIWAREPublishTransaction(id=f"urn:ngsi-ld:Transaction:{0}",
            #                                                     type=self.transaction_entity_type,
            #                                                     transactionID=self.transaction_to_publish.transactionID,
            #                                                     transactionCreatedDateTime=self.transaction_to_publish.transactionCreatedDateTime,
            #                                                     tradeResults=self.transaction_to_publish.tradeResults,
            #                                                     refMarketParticipant=self.transaction_to_publish.refMarketParticipant
            #                                                     )
            # transaction_entity['id'] = f"urn:ngsi-ld:Transaction:{cleints}"
            # transaction_entity['type'] = self.transaction_entity_type
            # transaction_entity = {"id": f"urn:ngsi-ld:Transaction:{cleints}", "type": self.transaction_entity_type}
            # transaction_entity = fiwarePublishTransaction.model_dump()
            # transaction_entity.update({transaction_id.name: {
            #     "type": transaction_id.type,
            #     "value": transaction_id.value
            # }})
            # transaction_entity.update({transaction_created_time.name: {
            #     "type": transaction_created_time.type,
            #     "value": transaction_created_time.value
            # }})
            # transaction_entity.update({transaction_results.name: {
            #     "type": transaction_results.type,
            #     "value": transaction_results.value
            # }})
            # transaction_entity.update({transaction_building.name: {
            #     "type": transaction_building.type,
            #     "value": transaction_building.value
            # }})
            # self.cbc.update_entity(entity=ContextEntity(**transaction_entity))

            # transaction_entity.add_attributes(
            #     [transaction_id, transaction_created_time, transaction_results, transaction_building])
            # self.transaction_entity.update_attribute([])
            # self.cbc.update_existing_entity_attributes()
            # self.cbc.update_entity(entity=transaction_entity)
            # self.cbc.patch_entity(entity=self.transaction_entity)
            # self.cbc.update_existing_entity_attributes(entity_id=f"urn:ngsi-ld:Transaction:{cleints}",
            #                                            entity_type=self.transaction_entity_type,
            #                                            attrs=[transaction_dict])
            # clear the transaction payload for next transaction
            self.transaction_to_publish = None
        # the sorted bids and transactions should be cleared, so that it won't affect the next trading
        self.sorted_bids.clear()
        self.transactions.clear()

    def get_historic_data(self):
        # historic_transactions = {}
        for i in range(len(self.buildings)):
            historic_transaction = self.qlc.get_entity_by_id(
                entity_id=f"urn:ngsi-ld:Transaction:{i}",
                entity_type=self.transaction_entity_type,
                last_n=10000
            )
            historic_transaction = historic_transaction.to_pandas()
            historic_transaction = historic_transaction.replace('', 0)
            print(historic_transaction)
