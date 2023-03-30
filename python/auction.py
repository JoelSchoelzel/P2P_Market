

def single_round(bids):

    #as shown in chapter 2 in: Chen, 2019

    transactions = {}

    #k for k-pricing method
    k = 0.5

    if len(bids["sell"]) != 0 and len(bids["buy"]) != 0:
        #create indices
        i = 0  # position of seller
        j = 0  # position of buyer
        m = 0  # count of transaction

        #continue matching until no price matches can be found
        while bids["sell"][i]["price"] <= bids["buy"][j]["price"]:

            #determine transaction price using k-pricing method
            transaction_price = bids["buy"][j]["price"] + k * (bids["sell"][i]["price"] - bids["buy"][j]["price"])

            #quantity is minimum of both
            transaction_quantity = min(bids["sell"][i]["quantity"], bids["buy"][j]["quantity"])

            #add transaction
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