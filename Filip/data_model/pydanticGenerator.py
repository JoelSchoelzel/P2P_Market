import sys
from pathlib import Path
from datamodel_code_generator import generate, InputFileType, DataModelType

# transform bid json schema to pydantic model
bid_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\PublishBid_schema.json')
bid_name = 'publishBid'
bid_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\PublishBid.py'
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

# transform transaction json schema to pydantic model
transaction_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\PublishTransaction_schema.json')
transaction_name = 'publishTransaction'
transaction_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\PublishTransaction.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(transaction_dir), 'w'):
    pass

sys.path.append(transaction_dir)

# generate transaction pydantic model
generate(input_=transaction_path, class_name=transaction_name,
         output=Path(transaction_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )

# transform marketParticipant json schema to pydantic model
marketParticipant_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant_schema.json')
marketParticipant_name = 'MarketParticipant'
marketParticipant_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(marketParticipant_dir), 'w'):
    pass

sys.path.append(marketParticipant_dir)

# generate bid pydantic model
generate(input_=marketParticipant_path, class_name=marketParticipant_name,
         output=Path(marketParticipant_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )