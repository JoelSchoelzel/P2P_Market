#import from P2P_Market
import config
import python.characteristics as characs
from filip.models.ngsi_v2.context import ContextEntity, NamedContextAttribute


class Coordinator:

    def __init__(self):
        self.bid = {}
        self.sorted_bids = {}
        self.transactions = {}
        self.transaction_entity = None


    def get_bid(self, building_entity):
        attributes = [building_entity.price.value, building_entity.quantity.value,
                      building_entity.buyer.value, int(building_entity.number.value)]
        self.bid[building_entity.name.value] = attributes

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
                if self.bid["bes_" + str(n)][2] == "True":
                    i = len(buy_list)
                    buy_list[i] = {
                        "price": self.bid["bes_" + str(n)][0],
                        "quantity": self.bid["bes_" + str(n)][1],
                        "building": self.bid["bes_" + str(n)][3]
                    }

                # add selling bids to sell_list
                if self.bid["bes_" + str(n)][2] == "False":
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

    def get_transactions(self):
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
                        if bids[n]["buy"][prio]["price"] >= bids[n]["sell"][k]["price"] and bids[n]["sell"][k]["quantity"] > 0:
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
                        if bids[n]["buy"][k]["price"] >= bids[n]["sell"][prio]["price"] and bids[n]["buy"][k]["quantity"] > 0:

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
                            bids[n]["buy"][ k]["quantity"] -= transaction_quantity
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

    def get_transaction_entity(self, cleints, n_opt):# TODO Set the number of buildings, time of running hour
        # Build buy and sell dictionary from the transaction
        buyer_dic = {}
        seller_dic = {}
        transaction_list = []
        transaction = {}
        # add the relevant information from transaction to the corresponding building
        # if the transactions is not empty
        if self.transactions:
            for n in range(len(self.transactions)):
                buyer_dic[n] = {}
                buyer_dic[n] = self.transactions[n]['buyer']
                seller_dic[n] = {}
                seller_dic[n] = self.transactions[n]['seller']


            # if the building hasn't transaction not the buyer or seller
            if cleints not in buyer_dic.values() and cleints not in seller_dic.values():
                self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                                                        type="Transaction")
                attribute_test = NamedContextAttribute(
                        name="my_attributes",
                        type="StructuredValue",
                        value={
                            "time": str(n_opt),
                            "result": "No Transaction",
                        })
                self.transaction_entity.add_attributes([attribute_test])

            # if the building is a buyer
            if cleints in buyer_dic.values():
                for key, value in buyer_dic.items():
                    if value == cleints:
                        transaction['Price'] = self.transactions[key]['price']
                        transaction['Quantity'] = self.transactions[key]['quantity']
                        transaction_list.append(transaction.copy())

                self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                                                        type="Transaction")
                attribute_test = NamedContextAttribute(
                        name="my_attributes",
                        type="StructuredValue",
                        value={
                            "time": str(n_opt),
                            "buyer": f"{cleints}",
                            # "seller": "Zehao",
                            "transaction": transaction_list
                        })
                self.transaction_entity.add_attributes([attribute_test])
                transaction_list.clear()

                # if the building is a seller
            else:
                for key, value in seller_dic.items():
                    if value == cleints:
                            transaction['Price'] = self.transactions[key]['price']
                            transaction['Quantity'] = self.transactions[key]['quantity']
                            transaction_list.append(transaction.copy())

                self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                                                        type="Transaction")
                attribute_test = NamedContextAttribute(
                        name="my_attributes",
                        type="StructuredValue",
                        value={
                            "time": str(n_opt),
                            # "buyer": "Junsong",
                            "seller": f"{cleints}",
                            "transaction": transaction_list
                        })
                self.transaction_entity.add_attributes([attribute_test])
                transaction_list.clear()

        # if the transaction is empty
        else:
            self.transaction_entity = ContextEntity(id=f"urn:ngsi-ld:Transaction:{cleints}",
                                                    type="Transaction")
            attribute_test = NamedContextAttribute(
                    name="my_attributes",
                    type="StructuredValue",
                    value={
                        "time": str(n_opt),
                        "result": "No Transaction",
                    })
            self.transaction_entity.add_attributes([attribute_test])
