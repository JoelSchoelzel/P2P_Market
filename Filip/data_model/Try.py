import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Union, Any, Mapping, Dict, Literal, get_origin, get_args
from urllib.error import HTTPError
from urllib.parse import ParseResult
import logging
import unittest

from pydantic import ValidationError
import sys
sys.path.append("D:\\jdu-zwu\\jsonschemaparser\\jsonschemaparser\\parser.py")
from jsonschemaparser import JsonSchemaParser
from jsonschemaparser import NormalizedModel


parser = JsonSchemaParser()
bid_id = parser.parse_schema(schema='D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\FIWAREPublishBid_schema.json',
                             model_class=NormalizedModel,
                             )
print(bid_id)

bid_instance = {'id': 'bid:001', "type": "Bid"}

bid_model = parser.create_context_entity(identifier=bid_id, instance=bid_instance)
print(bid_model)
