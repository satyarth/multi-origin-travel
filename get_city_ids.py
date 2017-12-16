import requests
import json
from time import sleep

from secret import key

def query_string(city_name):
    locale = 'en-GB'
    country = 'UK'
    query = "Moscow"
    currency = "GBP"
    
    return "http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/" + \
                country + "/" + \
                currency+ "/" + \
                locale + \
                "?query=" + city_name + \
                "&apiKey=" + key

with open('cities.txt', 'r') as f:
    cities =  f.readlines()
    
cities = [city.strip() for city in cities]

city_ids = {}

for city in cities:
    print(city)
    r = requests.get(query_string(city)).json()
    city_ids[city] = r['Places'][0]['PlaceId']
    sleep(.1)

with open('city_ids.json', 'w') as f:
    json.dump(city_ids, f)