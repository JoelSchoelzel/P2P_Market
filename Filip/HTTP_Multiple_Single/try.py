import os
from dotenv import load_dotenv
from filip.clients.ngsi_v2 import ContextBrokerClient
from filip.models.base import FiwareHeader

# Create the fiware header
load_dotenv()
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))
CB_URL = os.getenv('CB_URL')
Ql_URL = os.getenv('QL_URL')
load_dotenv()

cbc = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
transaction=cbc.get_entity_attributes(entity_id="urn:ngsi-ld:Transaction:1")
print(transaction)