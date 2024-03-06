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

import requests
from datamodel_code_generator import generate, InputFileType, DataModelType
from pydantic.fields import FieldInfo

tem_path = Path('D:\\jdu-zwu\\jsonschemaparser\\bid_schema.json')
# util.parse_with_dmcg(input_=tem_path, name='temperaturesensor')

name = 'bid'
temp_dir = 'D:\\jdu-zwu\\jsonschemaparser\\bid.py'
# make the temporary folder a module, by adding an __init__.py file
with open(Path(temp_dir), 'w'):
    pass

sys.path.append(temp_dir)

# generate pydantic model
generate(input_=tem_path, class_name=name,
         output=Path(temp_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )
# import the whole module
# module = importlib.import_module(name)

# tem_model = parser.parse_schema(schema='D:\\jdu-zwu\\jsonschemaparser\\tests\\inputs\\temperaturesensor.json',
#                              model_class=NormalizedModel,
#                              )
# bid_model = parser[bid_id]
# print(bid_id)
#
# bid_instance = {'id': 'temperaturesensor:002', "type": "TemperatureSensor"}
#
# bid_model = parser.create_context_entity(identifier=bid_id, instance=bid_instance)
# print(bid_model)
#
# bid_dict = bid_model.model_dump()
# print(bid_dict)




