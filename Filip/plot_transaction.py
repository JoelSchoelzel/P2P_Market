from filip.clients.ngsi_v2 import QuantumLeapClient
import os
from dotenv import load_dotenv
from filip.models.base import FiwareHeader
import json

load_dotenv()
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
Ql_URL = os.getenv('QL_URL')

qlc_instance = QuantumLeapClient(url=Ql_URL, fiware_header=fiware_header)

for i in range(20):
    # get trade results of building for 24 hours
    building_trade_results = qlc_instance.get_entity_attr_values_by_id(f"urn:ngsi-ld:Transaction:{i}", attr_name="tradeResults")
    # take the value of attributes out, the type of value is list
    day_trade_results = building_trade_results.attributes[0].values
    print(f"The number of results: {len(day_trade_results)}")
    # separate day results into every hour
    for j in range(len(day_trade_results)):
        hour_trade_results = day_trade_results[i]
        print(len(hour_trade_results))
        # some results are empty shown as [], this situation won't be considered
        if hour_trade_results:
            # the content of list is string, convert them to dictionary
            hour_trade_results = [json.loads(item) for item in hour_trade_results]
            hour_cash = 0
            # if the building is a seller, its cash should be positive, otherwise is negative
            if hour_trade_results[0]["powerDirection"].key == "buyer":
                for n in range(len(hour_trade_results)):
                    hour_cash += hour_trade_results[n]["realQuantity"]["quantity"] * hour_trade_results[n]["realPrice"]["price"]

