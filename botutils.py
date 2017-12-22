import requests

from secret import key

class NotFound(Exception):
	pass

def get_city_id(city_name):
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

	r = requests.get(query_string(city_name)).json()

	try:
		return r['Places'][0]['CityId'][:-4]

	except IndexError:
		raise NotFound()