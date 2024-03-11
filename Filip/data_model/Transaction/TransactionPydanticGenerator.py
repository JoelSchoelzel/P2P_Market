import sys
from pathlib import Path
from datamodel_code_generator import generate, InputFileType, DataModelType


# transform transaction json schema to pydantic model
transaction_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Transaction\\PublishTransaction_schema.json')
transaction_name = 'publishTransaction'
transaction_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Transaction\\PublishTransaction.py'
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

# transform fiware transaction json schema to pydantic model
fiware_transaction_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Transaction\\FIWAREPublishTransaction_schema.json')
fiware_transaction_name = 'fiwarePublishTransaction'
fiware_transaction_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\Transaction\\FIWAREPublishTransaction.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(fiware_transaction_dir), 'w'):
    pass

sys.path.append(fiware_transaction_dir)

# generate transaction pydantic model
generate(input_=fiware_transaction_path, class_name=fiware_transaction_name,
         output=Path(fiware_transaction_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )

