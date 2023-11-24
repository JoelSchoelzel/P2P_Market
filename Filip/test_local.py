# import pickle
#
# file_path1 = 'D:\jdu-zwu\P2P_Market\\results\P2P_mar_dict\scenario_test_alpha_el_flex_delayed.p'
# with open(file_path1, 'rb') as file:
#     data1 = pickle.load(file)
# print(data1)
#
# file_path2 = 'D:\jdu-zwu\P2P_Market\p2p_transaction.p'
# with open(file_path2, 'rb') as file:
#     data2 = pickle.load(file)
# print(data2)

import json
import os
from jsonschemaparser import JsonSchemaParser
# Initial entity instance


def extract_id_and_type(model, index):
    entity_json = {}
    for key, value in model.__fields__.items():
        if key == "id":
            entity_json["id"] = (
                value.default
                if value.default is not None
                else (model.__name__ + str(index))
            )
        elif key == "type":
            entity_json["type"] = model.__name__
    return entity_json


if __name__ == '__main__':

    # 10 bids entites
    bid_entities = []

    for i in range(10):

        entity_json = {"id": f"Bid:00{i}",
                       "type": "Bid"}

        with JsonSchemaParser() as parser:

            # with open('D:/jdu-zwu/P2P_Market/Filip/JSP/examples/entity_instance.json') as file:
            #     entity_json = json.load(file)

            # load json schema based data model
            parsed_schema = parser.parse_schema(schema="D:\jdu-zwu\P2P_Market\Filip\\test.json")
            data_model = parsed_schema.datamodel
            # entity_json = extract_id_and_type(data_model, i)

            # create a ContextEntity for each instance
            bid_entity = parser.create_context_entity(instance=entity_json)
            print('Instance of a FiLiP ContextEntity: \n' + bid_entity.json(indent=2) + '\n')

            bid_entities.append(bid_entity)
