from pydantic import BaseModel, Field
from filip.models.base import DataType, FiwareRegex
from typing import Union, Optional
from aenum import Enum


# Identify buildings
class BuildingID(BaseModel):
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
        description="the role of building in transaction"
    )


# participant type is to specify a limited set of options for the 'value' field in class Role
class ParticipantType(str, Enum):
    Buyer = 'buyer'
    Seller = 'seller'
    NotParticipant = 'not participant'


# The role of buildings in the transaction
class Role(BaseModel):
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  str = Field(
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


# The running time of process
class Time(BaseModel):
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  Union[DataType, str] = Field(
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


# The price in the transaction
class Price(BaseModel):
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  DataType.FLOAT = Field(
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: float = Field(
        default=None,
        title="Attribute value",
        description="the price of transaction"
    )


# The quantity of the transaction
class Quantity(BaseModel):
    name: Optional[str] = Field(
        titel="Attribute name",
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )

    type:  DataType.FLOAT = Field(
        max_length=256,
        min_length=1,
        regex=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )

    value: float = Field(
        title="Attribute value",
        description="the quantity of transaction"
    )


# It exists responds for different conditions
class Responds(BaseModel):
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
