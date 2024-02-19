import filip.models.ngsi_v2.context
from pydantic import BaseModel, Field, schema_json_of
from filip.models.base import DataType
from typing import Union, Optional, Annotated, List
from aenum import Enum
from datetime import datetime
from uuid import UUID
import json
from decimal import Decimal


# class EntityID(Field):
#     ...

# class EntityID(BaseModel):
#     """To identify every entity in the data platform"""
#     id: str
#
#
# class EntityType(BaseModel):
#     """
#     The Type of entity
#     """
#     type: # str
#
#
# class RefEntityID(BaseModel):
#     """To link the other entity's ID"""
#     refID: str


# Identify buildings
# class BuildingName(BaseModel):
#     """
#     To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
#     according to their name.
#     """
#     name: str


# Identify buildings
# class BuildingID(BaseModel):
#     """
#     To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
#     according to their ID number.
#     """
#     id: str


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


class MarketRole(str, Enum):
    """
    This version of Role is currently only for implementing in bid
    """
    buyer = 'buyer'
    seller = 'seller'


class CreatedDateTime(BaseModel):
    """
    The time of prediction for next hour, it can also identify the bids or transactions in hours.
    """
    time: str


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


class CoordinatorGateTime(BaseModel):
    """
    Coordinator has time schedule for the whole trading. The pertinent activity can only be conducted in permitted time.
    """
    gate: datetime

class PowerDirection(BaseModel):
    tradingObjectRole: MarketRole
    tradingObjectID: str = Field(description='...')


class TradeInformation(BaseModel):
    """
    The results of transaction
    """
    realPrice: Price = Field(description='...')
    realQuantity: Quantity = Field(description='...')
    powerDirection: PowerDirection = Field(description='...')


class TradeResults(BaseModel):
    tradeResults: List[TradeInformation]


# class MarketType(str, Enum):
#     marketType = 'HAM'


# class RoundTime(BaseModel):
#     """
#     In P2P_Market run the programm in 744h, the round time is for every hour of 744, it will be displayed in bid
#     entity.
#     """
#     round: int


# todo main model
class MarketParticipant(BaseModel):
    id: str = Field(description="Entity ID of MarketParticipant")
    type: str = Field(description="Entity type of MarketParticipant")
    buildingName: str = Field(description="Building's name")
    userID: str = Field(description='The user name for the Building')
    refActiveBid: str = Field(description="Entity ID of relevant active bid")
    refTransaction: str = Field(description="Entity ID of relevant Transaction result")

    class Config:
        title = 'MarketParticipant'


# print(MarketParticipant.schema_json(indent=2))
class PublishBid(BaseModel):
    bidID: str = Field(description='...')
    bidCreatedDateTime: CreatedDateTime = Field(description='Date and time that this Bid was created')
    expectedPrice: Price
    expectedQuantity: Quantity
    marketRole: MarketRole = Field(
        description='An identification of a party acting in a electricity market business process')
    refMarketParticipant: str = Field(description="...")


# class Bid(BaseModel):
#     """
#     Represents  bid to purchase or sell energy in electricity market
#     """
#     id: str = Field(description="...")
#     type: # str = Field(description="...")
#     bidID: str = Field(description='...')
#     transactionCreatedDateTime: CreatedDateTime = Field(description='Date and time that this Bid was created')
#     price: Price
#     quantity: Quantity
#     marketRole: MarketRole = Field(description='An identification of a party acting in a electricity market business process')
#     refMarketparticipant: str = Field(description="...")
#
#     class Config:
#         title = 'Bid'

class Coordinator(BaseModel):
    id: str = Field(description="...")
    type: str = Field(description="...")
    marketType: str = 'Hour Ahead Market'
    bidStartTime: CoordinatorGateTime = Field(description="Start time and date for bid applies.")
    bidStopTime: CoordinatorGateTime = Field(description="")
    transactionStartTime: CoordinatorGateTime = Field(description="Start time and date for bid applies.")
    transactionStopTime: CoordinatorGateTime = Field(description="")


# print(Bid.schema_json(indent=2))


class PublishTransaction(BaseModel):
    """
    Represents transaction of power direction and negotiated price and quantity
    """
    transactionID: str = Field(description='...')
    transactionCreatedDateTime: CreatedDateTime = Field(description='Date and time that this Bid was created')
    tradeResults: Union[TradeResults, list] = Field(default=None, description='...')
    refMarketParticipant: str = Field(description="...")


class FIWAREPublishTransaction(PublishTransaction):
    id: str = Field(description="...")
    type:  str = Field(description="...")
    # publishTransaction: PublishTransaction = Field(description='...')

# print(PublishTransaction.schema_json(indent=2))
#
#
# class Coordinator(BaseModel):
#     """
#     This class is used to identify the electricty market type and regulate bidding and trading time
#     """
#     marketType: MarketType = Field(description='Hour Ahead Market')
#     bidStartTime: Time = Field(description='Start time and date for bid applies')
#     bidStopTime: Time = Field(description='Stop time and date for which bid is applicable')
#     transactionStartTime: Time = Field(description='Start time and date for transaction applies')
#     transactionStopTime: Time = Field(description='Stop time and date for which transaction is applicable')
#
#
# print(Coordinator.schema_json(indent=2))


# class MarketParticipant(BaseModel):
#     name: BuildingName
#     refBid: RefBid
#     refTransaction: RefTransaction
#
#
# class MarketParticipantFIWARE(MarketParticipant):
#     id: BuildingID


# todo convert pydantic model to json schema
# bid_schema = schema_json_of(Bid, indent=2)
# print(bid_schema)

# with open('bid_schema.json', 'w') as f:
#     f.write(bid_schema)
# bid_schema_dict = json.loads(bid_schema)
# json.dump(bid_schema_dict, f, indent=2)
