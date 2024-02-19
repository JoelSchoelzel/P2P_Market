from data_model.data_model import PublishTransaction, CreatedDateTime, TradeResults, Price, Quantity, TradeInformation, \
    FIWAREPublishTransaction
import uuid
from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent
import os
from datetime import datetime
from filip.clients.ngsi_v2 import ContextBrokerClient, IoTAClient
from pydantic import ConfigDict
from filip.models.ngsi_v2.context import ContextEntity, NamedContextAttribute
from filip.models.ngsi_v2.iot import ServiceGroup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
APIKEY = os.getenv('APIKEY_Coordinator')
# Create a service group and add it to your devices
service_group = ServiceGroup(apikey=APIKEY,
                             resource="/iot/json")
# import from P2P_Market
import pandas as pd
fiware_header = FiwareHeader(service=os.getenv('Service'),
                             service_path=os.getenv('Service_path'))

CB_URL = os.getenv('CB_URL')
IOTA_URL = os.getenv('IOTA_URL')



# create a cleint in context broker and iot agent for all buildings
cbc_instance = ContextBrokerClient(url=CB_URL, fiware_header=fiware_header)
iotac_instance = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)

model_config = ConfigDict(extra="allow")

start_timestamp = 1443657600
start_datetime = datetime.utcfromtimestamp(start_timestamp)

transaction_entity_type = 'Transaction'

transactions = {}
TradeResults = []
transaction_to_publish = PublishTransaction(transactionID=str(uuid.uuid4()),
                                                 transactionCreatedDateTime=CreatedDateTime(
                                                     time=str(start_datetime)),
                                                 tradeResults=TradeResults,
                                                 refMarketParticipant=f"urn:ngsi-ld:Building:{0}")

fiwarePublishTransaction = FIWAREPublishTransaction(id=f"urn:ngsi-ld:Transaction:{0}",
                                                    type=transaction_entity_type,
                                                    transactionID=transaction_to_publish.transactionID,
                                                    transactionCreatedDateTime=transaction_to_publish.transactionCreatedDateTime,
                                                    tradeResults=transaction_to_publish.tradeResults,
                                                    refMarketParticipant=transaction_to_publish.refMarketParticipant
                                                    )

transaction_entity = fiwarePublishTransaction.model_dump()

cbc_instance.patch_entity(entity=ContextEntity(**transaction_entity))