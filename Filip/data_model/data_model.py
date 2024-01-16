import filip.models.ngsi_v2.context
from pydantic import BaseModel, Field, schema_json_of
from filip.models.base import DataType, FiwareRegex
from typing import Union, Optional, Annotated
from aenum import Enum
from datetime import datetime
from uuid import UUID
import json


# Identify buildings
class BuildingName(BaseModel):
    """
    To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
    according to their name.
    """
    name: str


# Identify buildings
class BuildingID(BaseModel):
    """
    To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
    according to their ID number.
    """
    id: str


# class Role(str, Enum):
#     """
#     Participant type is to specify a limited set of options for the 'value' field in class Role. 'buyer' and 'seller'
#     will be claimed in the bids, so that the coordinator can match the appropriate seller and buyer. Some buyer or
#     seller may not be able to transact with others for variety of reasons, so they will be set as 'not participant'
#     in transaction.
#     """
#     Buyer = 'buyer'
#     Seller = 'seller'
#     NotParticipant = 'not participant'
class ProductID(BaseModel):
    productID: UUID


class MarketRole(str, Enum):
    """This version of Role is currently only for implementing in bid"""
    buyer = 'buyer'
    seller = 'seller'


class Time(BaseModel):
    """
    The time of prediction for next hour, it can also identify the bids or transactions in hours.
    """
    time: datetime


class Price(BaseModel):
    """
    The price of the buying or selling will be at first in bids provided from every building. But the final transacted
    price will be by coordinator with multiple trading round determined.
    """
    price: float


class Quantity(BaseModel):
    """
    Quantity will be at first in bids provided. After matching among buyers and sellers, appropriate matches will have
    a certain quantity to exchange. One seller can sell its energy to one or more buyers.
    """
    quantity: float


class PowerDirection(BaseModel):
    """
    There will be 3 types of final transaction: 'buy', 'sell' and 'not participate'. For the buy and sell type, respond
    should contain id, role, time, price and quantity. But for 'not participate' type, respond should id, role, time and
    the message 'No Transaction'.
    """
    powerDirection: str


class MarketType(str, Enum):
    marketType = 'HAM'


class RoundTime(BaseModel):
    """In P2P_Market run the programm in 744h, the round time is for every hour of 744, it will be displayed in bid
    entity. """
    round: int




class MarketBuilding(BaseModel):
    name: BuildingName = Field(description="Building's name")
    userID: BuildingID = Field(description='The user name for the Building')
    bidID: ProductID = Field(description='The user name for the Bid')
    transactionID: ProductID = Field(description='The user name for the Transaction')

    class Config:
        title = 'Bid'


print(MarketBuilding.schema_json(indent=2))


class Bid(BaseModel):
    """Represents  bid to purchase or sell energy in electricity market"""
    bidID: ProductID = Field(description='The user name for the Bid')
    createdDateTime: Time = Field(description='Date and time that this Transaction was created')
    price: Price = Field(description='A number of monetary units specified in a unit of currency')
    quantity: Quantity = Field(description='The quantity value.')
    marketRole: MarketRole = Field(description='An identification of a party acting in a electricity market business process')
    userID: BuildingID = Field(description='The user name for the Building')

    class Config:
        title = 'Bid'


print(Bid.schema_json(indent=2))

# class BidFiware(Bid):
#     bidround: RoundTime


class Transaction(BaseModel):
    """Represents transaction of power direction and negotiated price and quantity"""
    transactionID: ProductID = Field(description='The user name for the Transaction')
    createdDateTime: Time = Field(description='Date and time that this Transaction was created')
    price: Price = Field(description='A number of monetary units specified in a unit of currency')
    quantity: Quantity = Field(description='The quantity value.')
    powerDirection: PowerDirection = Field(description='Both parties involved in the transaction')
    userID: BuildingID = Field(description='The user name for the Building')

    class Config:
        title = 'Transaction'


print(Transaction.schema_json(indent=2))


class Coordinator(BaseModel):
    """This class is used to identify the electricty market type and regulate bidding and trading time"""
    marketType: MarketType = Field(description='Hour Ahead Market')
    bidStartTime: Time = Field(description='Start time and date for bid applies')
    bidStopTime: Time = Field(description='Stop time and date for which bid is applicable')
    transactionStartTime: Time = Field(description='Start time and date for transaction applies')
    transactionStopTime: Time = Field(description='Stop time and date for which transaction is applicable')


print(Coordinator.schema_json(indent=2))



# class MarketParticipant(BaseModel):
#     name: BuildingName
#     refBid: RefBid
#     refTransaction: RefTransaction
#
#
# class MarketParticipantFIWARE(MarketParticipant):
#     id: BuildingID




# todo convert pydantic model to json schema
#bid_schema = schema_json_of(Bid, indent=2)
#print(bid_schema)

# with open('bid_schema.json', 'w') as f:
#     f.write(bid_schema)
    # bid_schema_dict = json.loads(bid_schema)
    # json.dump(bid_schema_dict, f, indent=2)

