import sys
from pathlib import Path
from datamodel_code_generator import generate, InputFileType, DataModelType

# transform bid json schema to pydantic model
bid_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Bid\\PublishBid_schema.json')
bid_name = 'publishBid'
bid_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Bid\\PublishBid.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(bid_dir), 'w'):
    pass

sys.path.append(bid_dir)

# generate bid pydantic model
generate(input_=bid_path, class_name=bid_name,
         output=Path(bid_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )

# transform fiware bid json schema to pydantic model
fiware_bid_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Bid\\FIWAREPublishBid_schema.json')
fiware_bid_name = 'fiwarePublishBid'
fiware_bid_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Bid\\FIWAREPublishBid.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(fiware_bid_dir), 'w'):
    pass

sys.path.append(fiware_bid_dir)

# generate bid pydantic model
generate(input_=fiware_bid_path, class_name=fiware_bid_name,
         output=Path(fiware_bid_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )