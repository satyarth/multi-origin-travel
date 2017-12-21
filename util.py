from skyscanner.skyscanner import FlightsCache, Flights
from ratelimit import rate_limited
from datetime import datetime
import math
import numpy as np
from multiprocessing.dummy import Pool as ThreadPool

from secret import key

pricer = FlightsCache(key)

def process_quotes(response): # Expects dict, use response.json()
    quotes = response['Quotes']
    places = response['Places']
    place_details = {}

    for place in places:
        place_details[place['PlaceId']] = place
        
    for quote in quotes:
        if 'InboundLeg' in quote:
            quote['InboundLeg']['OriginDetails'] = place_details[quote['InboundLeg']['OriginId']]
            quote['InboundLeg']['DestinationDetails'] = place_details[quote['InboundLeg']['DestinationId']]
        
        if 'OutboundLeg' in quote:
            quote['OutboundLeg']['OriginDetails'] = place_details[quote['OutboundLeg']['OriginId']]
            quote['OutboundLeg']['DestinationDetails'] = place_details[quote['OutboundLeg']['DestinationId']]

    return quotes

@rate_limited(490, 60)
def search_quotes(origin, destination, outbound, inbound):
    skyscanner_response = pricer.get_cheapest_quotes(
            market='RU',
            currency='RUB',
            locale='en-GB',
            originplace=origin,
            destinationplace=destination,
            outbounddate=outbound,
            inbounddate=inbound,
            adults=1).parsed
    
    return process_quotes(skyscanner_response)

def min_roundtrip_price(quotes):
    roundtrips = list(filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' in quote, quotes))
    outbounds = list(filter(lambda quote: 'InboundLeg' not in quote and 'OutboundLeg' in quote, quotes))
    inbounds = list(filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' not in quote, quotes))
    
    # Stupid hack to avoid minima of empty lists

    min_cost = math.inf
    cheapest_route = {}

    for o in outbounds:
        for i in inbounds:
            cost = o['MinPrice'] + i['MinPrice']
            if cost < min_cost:
                min_cost = cost
                cheapest_route['InboundLeg'] = i['InboundLeg']
                cheapest_route['OutboundLeg'] = o['OutboundLeg']
                cheapest_route['MinPrice'] = cost
                cheapest_route['MultiTicket'] = True

    for r in roundtrips:
        cost = r['MinPrice']
        if cost < min_cost:
            min_cost = cost
            cheapest_route['InboundLeg'] = r['InboundLeg']
            cheapest_route['OutboundLeg'] = r['OutboundLeg']
            cheapest_route['MinPrice'] = cost
            cheapest_route['MultiTicket'] = False


    return min_cost, cheapest_route

def get_cheapest_link(origin, destination, outbounddate, inbounddate=None):


    def get_live_quotes(origin, destination, outbounddate, inbounddate=None):
        pricer = Flights(key)
        suffix = '-sky'

        origin = origin+suffix
        destination = destination+suffix

        if not inbounddate:
            response = pricer.get_result(
                country='RU',
                currency='RUB',
                locale='en-GB',
                originplace=origin,
                destinationplace=destination,
                outbounddate=outbounddate,
                adults=1).parsed
        else:
            response = pricer.get_result(
                country='RU',
                currency='RUB',
                locale='en-GB',
                originplace=origin,
                destinationplace=destination,
                outbounddate=outbounddate,
                inbounddate=inbounddate,
                adults=1).parsed

        return response

    def cheapest_link(response):
        itinerary = response['Itineraries'][0]
        link = ''
        cost = np.inf

        for popt in itinerary['PricingOptions']:
            if popt['Price'] < cost:
                cost = popt['Price']
                link = popt['DeeplinkUrl']

        return link

    quotes = get_live_quotes(origin, destination, outbounddate, inbounddate)
    link = cheapest_link(quotes)

    return link

def random_date(start, end):
    prop = np.random.random()
    ptime = start + prop * (end - start)
    ptime = ptime.replace(hour=0, minute=0, second=0, microsecond=0)
    return ptime


class SkyscannerInteractor:
    def __init__(self, cities, origins):
        self.cities = cities
        self.origins = origins


    def get_price(self, solution):
        price = [0,]
        routes = []

        destination_code = solution.destination
        date_come_str = datetime.strftime(solution.date_come, FORMAT)
        date_leave_str = datetime.strftime(solution.date_leave, FORMAT)

        def fetch_price(source):
            quotes = search_quotes(source, destination_code, date_come_str, date_leave_str)
            min_price, route = min_roundtrip_price(quotes)
            routes.append(route)
            price[0] = price[0] + min_price

        pool = ThreadPool(len(self.origins))
        pool.map(fetch_price, self.origins)

        solution.price = price[0]
        solution.routes = routes

        return price[0]

FORMAT = "%Y-%m-%d"


