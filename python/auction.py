

def single_round(bids):

    # as shown in chapter 2 in: Chen, 2019

    transactions = {}

    # k for k-pricing method
    k = 0.5

    if len(bids["sell"]) != 0 and len(bids["buy"]) != 0:
        # create indices
        i = 0  # position of seller
        j = 0  # position of buyer
        m = 0  # count of transaction

        # continue matching until no price matches can be found
        while bids["sell"][i]["price"] <= bids["buy"][j]["price"]:

            # determine transaction price using k-pricing method
            transaction_price = bids["buy"][j]["price"] + k * (bids["sell"][i]["price"] - bids["buy"][j]["price"])

            # quantity is minimum of both
            transaction_quantity = min(bids["sell"][i]["quantity"], bids["buy"][j]["quantity"])

            # add transaction
            transactions[m] = {}
            transactions[m]["buyer"] = bids["buy"][j]["building"]
            transactions[m]["seller"] = bids["sell"][i]["building"]
            transactions[m]["price"] = transaction_price
            transactions[m]["quantity"] = transaction_quantity
            m += 1
            bids["sell"][i]["quantity"] = bids["sell"][i]["quantity"] - transaction_quantity
            if bids["sell"][i]["quantity"] == 0:
                i += 1
            bids["buy"][j]["quantity"] = bids["buy"][j]["quantity"] - transaction_quantity
            if bids["buy"][j]["quantity"] == 0:
                j += 1
            if i == len(bids["sell"]) or j == len(bids["buy"]):
                break

    return transactions, bids


def multi_round(sorted_bids):

    transactions = {}
    count_trans = 0  # count of transaction

    # k for k-pricing method
    kappa = 0.5

    # amount to change price each round
    dp_buy = 0.05
    dp_sell = -0.05

    n = 0  # round of trading

    # create dict for first trading round with sorted bids
    bids = {n: sorted_bids}

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
                        transaction_price = bids[n]["buy"][prio]["price"] + kappa * (bids[n]["sell"][k]["price"] - bids[n]["buy"][prio]["price"])

                        # quantity is minimum of both
                        transaction_quantity = min(bids[n]["sell"][k]["quantity"], bids[n]["buy"][prio]["quantity"])

                        # add transaction
                        transactions[count_trans] = {
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
                        transaction_price = bids[n]["buy"][k]["price"] + kappa * (bids[n]["sell"][prio]["price"] - bids[n]["buy"][k]["price"])

                        # quantity is minimum of both
                        transaction_quantity = min(bids[n]["sell"][prio]["quantity"], bids[n]["buy"][k]["quantity"])

                        # add transaction
                        transactions[count_trans] = {
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
        bids[n+1] = {"buy": {}, "sell": {}}
        for i in range(len(bids[n]["buy"])):
            if bids[n]["buy"][i]["quantity"] > 0:
                bids[n+1]["buy"][p_buy] = bids[n]["buy"][i].copy()
                bids[n+1]["buy"][p_buy]["price"] = bids[n]["buy"][i]["price"] + dp_buy
                p_buy += 1

        p_sell = 0
        for i in range(len(bids[n]["sell"])):
            if bids[n]["sell"][i]["quantity"] > 0:
                bids[n + 1]["sell"][p_sell] = bids[n]["sell"][i].copy()
                bids[n + 1]["sell"][p_sell]["price"] = bids[n]["sell"][i]["price"] + dp_sell
                p_sell += 1

        # go to next trading round
        n += 1

    return transactions, bids
