from pydantic import BaseModel, Field, schema_json_of
from filip.models.base import DataType, FiwareRegex
from typing import Union, Optional, Annotated
from aenum import Enum

import json

from pydantic.schema import model_schema
# Identify buildings
class BuildingName(BaseModel):
    """
    To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
    according to their name.
    """

    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type: Optional[Union[DataType, str]] = Field(
        default=str,
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        default=None,
        title="Attribute value",
        description="the role of building in transaction"
    )


# Identify buildings
class BuildingID(BaseModel):
    """
    To identify every building who submits the bid to coordinator, and coordinator can send the relevant transaction
    according to their ID number.
    """

    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type: Optional[Union[DataType, str]] = Field(
        default=DataType.NUMBER,
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        default=None,
        title="Attribute value",
        description="the role of building in transaction"
    )


class ParticipantType(str, Enum):
    """
    Participant type is to specify a limited set of options for the 'value' field in class Role. 'buyer' and 'seller'
    will be claimed in the bids, so that the coordinator can match the appropriate seller and buyer. Some buyer or
    seller may not be able to transact with others for variety of reasons, so they will be set as 'not participant'
    in transaction.
    """
    Buyer = 'buyer'
    Seller = 'seller'
    NotParticipant = 'not participant'



class Role(BaseModel):
    """
    The Role of 'buyer' and 'seller' will be used both in bids and transactions, 'not participant' only be used in
    transaction
    """
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  Optional[str] = Field(
        default=DataType.TEXT,
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: ParticipantType = Field(
        default=None,
        title="Attribute value",
        description="the role of building in transaction"
    )



class Time(BaseModel):
    """
    The time of prediction for next hour, it can also identify the bids or transactions in hours.
    """
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  Optional[Union[DataType, str]] = Field(
        default=DataType.TEXT,
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        default=None,
        title="Attribute value",
        description="the running time of transaction"
    )


class Price(BaseModel):
    """
    The price of the buying or selling will be at first in bids provided from every building. But the final transacted
    price will be by coordinator with multiple trading round determined.
    """
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  Optional[Union[DataType, str]] = Field(
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        default=None,
        title="Attribute value",
        description="the price of transaction"
    )


class Quantity(BaseModel):
    """
    Quantity will be at first in bids provided. After matching among buyers and sellers, appropriate matches will have
    a certain quantity to exchange. One seller can sell its energy to one or more buyers.
    """
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  Optional[Union[DataType, str]] = Field(
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        title="Attribute value",
        description="the quantity of transaction"
    )


# class Bid(BaseModel):
#     timestamp: Time
#     name: BuildingName
#     price: Price
#     quantity: Quantity
#     buyer: Role
#     number: BuildingID
Bid = Annotated[Time, BuildingName, Price, Quantity, Role, BuildingID]
# convert pydantic model to json schema
bid_schema = schema_json_of(Bid, indent=2)
with open('bid_schema.json', 'w') as f:
    json.dump(bid_schema, f, indent=2)

class Responds(BaseModel):
    """
    There will be 3 types of final transaction: 'buy', 'sell' and 'not participate'. For the buy and sell type, respond
    should contain id, role, time, price and quantity. But for 'not participate' type, respond should id, role, time and
    the message 'No Transaction'.
    """
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type: Union[DataType, str] = Field(
        default=DataType.NUMBER,
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: Union[DataType, str] = Field(
        default=None,
        title="Attribute value",
        description="the responds from coordinator to buildings"
    )
