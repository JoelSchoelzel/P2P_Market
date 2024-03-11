import sys
from pathlib import Path
from datamodel_code_generator import generate, InputFileType, DataModelType

# transform marketParticipant json schema to pydantic model
marketParticipant_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant'
                              '\\MarketParticipant_schema.json')
marketParticipant_name = 'MarketParticipant'
marketParticipant_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant\\MarketParticipant.py'
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

# transform marketParticipant json schema to pydantic model
fiwareMarketParticipant_path = Path('D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant'
                                    '\\FIWAREMarketParticipant_schema.json')
fiwareMarketParticipant_name = 'FiwareMarketParticipant'
fiwareMarketParticipant_dir = 'D:\\jdu-zwu\\P2P_Market\\Filip\\data_model\\MarketParticipant\\FIWAREMarketParticipant.py'
# make the temporary folder a module, by adding a corresponding file
with open(Path(fiwareMarketParticipant_dir), 'w'):
    pass

sys.path.append(fiwareMarketParticipant_dir)

# generate bid pydantic model
generate(input_=fiwareMarketParticipant_path, class_name=fiwareMarketParticipant_name,
         output=Path(fiwareMarketParticipant_dir),
         output_model_type=DataModelType.PydanticV2BaseModel,
         use_subclass_enum=True,
         input_file_type=InputFileType.JsonSchema,
         )
