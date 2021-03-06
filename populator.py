import requests
import json
from pymongo import MongoClient
from multiprocessing.dummy import Pool as ThreadPool
from ratelimit import rate_limited
from util import process_quotes

from secret import key, mongo_uri

if mongo_uri:
    client = MongoClient(mongo_uri)
else:
    client = MongoClient()

db = client.quotes
quotes_db = db.quotes

def build_query(origin_city_id):
        base_url = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/'
        country = 'RU'
        locale = 'en-US'
        currency = 'RUB'
        destination = 'Anywhere'
        outbound = inbound = '2018-01'
        
        return base_url + "/" +\
                     country + "/" +\
                     currency + "/" +\
                     locale + "/" +\
                     origin_city_id + "/" +\
                     destination + "/" +\
                     outbound + "/" +\
                     inbound + "/" +\
                     "?apiKey=" + key

def truncate_roundtrip_quote(quote):
    return {
        'Origin': quote['OutboundLeg']['OriginDetails']['CityId'],
        'Destination': quote['OutboundLeg']['DestinationDetails']['CityId'],
        'OutboundDate': quote['OutboundLeg']['DepartureDate'],
        'InboundDate': quote['InboundLeg']['DepartureDate'],
        'MinPrice': quote['MinPrice']
        }

def process_city(city_id, govnokod=False):
    query = build_query(city_id)
    r = requests.get(query).json()
    quotes = process_quotes(r)
    if govnokod:
        return quotes
    quotes_db.insert_many(map(truncate_roundtrip_quote, quotes))

with open("city_ids.json") as f:
    cities = json.load(f)

city_ids = [cities[city] for city in cities]

pool = ThreadPool(10)
pool.map(process_city, city_ids)