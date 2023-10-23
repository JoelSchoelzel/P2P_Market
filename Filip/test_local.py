import requests

# url = 'http://134.130.166.184:1026/v2/entities/urn:ngsi-ld:Building:0?options=normalized'
url = 'http://134.130.166.184:1026/v2/entities'
params = {'options': 'normalized'}
headers = {'fiware-service': 'lem_test', 'fiware-servicepath': '/'}


res = requests.get(url=url, params=params, headers=headers)
