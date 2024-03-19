import json


subscription = {
    "description": "Subscription to receive MQTT-Notification about urn:ngsi-ld:Transaction:id",
    "subject": {
        "entities": [
            {
                "id": "urn:ngsi-ld:Transaction:id",
                "type": "Transaction"
            }
        ]
    },
    "notification": {
        "mqtt": {
            "url": 'MQTT_Broker_URL',
            "topic": "/v2/transactions/urn:ngsi-ld:Transaction:id/attrs"
        }
    }
}
file_path = "transaction_subscription.json"
with open(file_path, 'w') as json_file:
    json.dump(subscription, json_file, indent=2)