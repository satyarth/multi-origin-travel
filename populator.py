import requests
import json
from pymongo import MongoClient
from multiprocessing.dummy import Pool as ThreadPool
from ratelimit import rate_limited

from secret import key

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

@rate_limited(300, 60)
def process_quotes(response): # Expects dict, use response.json()
	quotes = response['Quotes']
	places = response['Places']
	place_details = {}

	for place in places:
	    place_details[place['PlaceId']] = place
	    
	for quote in quotes:
	    quote['InboundLeg']['OriginDetails'] = place_details[quote['InboundLeg']['OriginId']]
	    quote['InboundLeg']['DestinationDetails'] = place_details[quote['InboundLeg']['DestinationId']]
	    quote['OutboundLeg']['OriginDetails'] = place_details[quote['OutboundLeg']['OriginId']]
	    quote['OutboundLeg']['DestinationDetails'] = place_details[quote['OutboundLeg']['DestinationId']]

	return quotes

def process_city(city_id):
	query = build_query(city_id)
	r = requests.get(query).json()
	quotes = process_quotes(r)
	quotes_db.insert_many(quotes)


with open("../city_ids.json") as f:
	cities = json.load(f)

city_ids = [cities[city] for city in cities]

pool = ThreadPool(10)
pool.map(process_city, city_ids)
