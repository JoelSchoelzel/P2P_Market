
# def trade_dvs_block_bids(self, n, bid_strategy, strategies, weights):



def single_round(bids):
    """
    Runs auction with a single trading round.
    This uses an algorithm show in chapter 2 in Chen, 2019 "https://doi.org/10.1016/j.apenergy.2019.03.094".
    It iterates through buying and selling bids until no more matches can be found. This only works properly, if the
    bids are sorted by price.

    Returns:
        transactions (dict): Dictionary with all transactions made.
        bids (dict): Bids with remaining quantities.
    """

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


def multi_round(sorted_bids, max_rounds):
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

    transactions = {}
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
    bids = {n: sorted_bids}

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
                transactions[count_trans] = {
                    "buyer": bids[n]["buy"][prio]["building"],
                    "seller": bids[n]["sell"][prio]["building"],
                    "price": transaction_price,
                    "quantity": transaction_quantity,
                    "trading_round": (n+1)
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

    return transactions, bids


# multi_round2 is a more complex version of multi round trading, that is not used at the moment
def multi_round2(sorted_bids):

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

def devices_blockbids_negotiation(bes_list, block_bids, options, nodes, init_val, propensities, strategies):
    """
    Implements the negotiation process between BESs.

    :param bes_list: List of BuildingEnergySystem objects
    :param block_bids: Dictionary of block bids for each BES
    :return: Dictionary of block bids for each BES after negotiation
    """

    # create dictionary for transactions
    transactions = {}

    # create dictionary for bids
    bids = {}

    # create dictionary for sorted bids
    sorted_bids = {}

    # create dictionary for unflexible bids
    unflex = {}

