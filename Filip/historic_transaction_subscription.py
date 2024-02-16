import json

subscription_template = {
    "description": "QuantumLeap Subscription",
    "subject": {
        "entities": [
            {
                "id": "ID",
                "type": "TYPE"
            }
        ],
        "condition": {
            "attrs": ["..."],
        }
    },
    "notification": {
        "onlyChangedAttrs": False,
        "http": {
            "url": "http://quantumleap:8668/v2/notify"
        },
        "metadata": [
            "dateCreated",
            "dateModified",
            "TimeInstant",
            "timestamp"
        ]
    },
    "throttling": 0
}

file_path = 'historic_transaction_subscription.json'
with open(file_path, 'w') as json_file:
    json.dump(subscription_template, json_file, indent=2)
