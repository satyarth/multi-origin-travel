import requests

from secret import key

class NotFound(Exception):
	pass

def query_string(query):
	    locale = 'en-GB'
	    country = 'UK'
	    currency = "GBP"
	    
	    return "http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/" + \
	                country + "/" + \
	                currency+ "/" + \
	                locale + \
	                "?query=" + query + \
	                "&apiKey=" + key

def get_place(query):
	r = requests.get(query_string(query)).json()

	try:
		return r['Places'][0]

	except IndexError:
		raise NotFound()

def get_city_id(city_name):
	return get_place(city_name)['CityId'][:-4]