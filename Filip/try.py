from data_model.Bid.PublishBid import PublishBid, CreatedDateTime, Price, Quantity, MarketRole
import json
# bid_to_publish = PublishBid(bidID='2342',
#                             bidCreatedDateTime=CreatedDateTime(time=str(25)),
#                             expectedPrice=Price(price=0.25),
#                             expectedQuantity=Quantity(quantity=0.8),
#                             marketRole='buyer',
#                             refMarketParticipant="self.id")
bid_to_publish = PublishBid(bidID='2342',
                            bidCreatedDateTime=CreatedDateTime(time=str(25)),
                            expectedPrice=0.25,
                            expectedQuantity=0.8,
                            marketRole='buyer',
                            refMarketParticipant="self.id")

bid_dict = bid_to_publish.model_dump()
json_data = json.dumps(bid_dict)
