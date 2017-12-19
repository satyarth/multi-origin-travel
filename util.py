from skyscanner.skyscanner import FlightsCache
from ratelimit import rate_limited
import math

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
    roundtrips = filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' in quote, quotes)
    outbounds = filter(lambda quote: 'InboundLeg' not in quote and 'OutboundLeg' in quote, quotes)
    inbounds = filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' not in quote, quotes)
    
    # Stupid hack to avoid minima of empty lists
    multiticket_cost = min([math.inf] + [o['MinPrice'] + i['MinPrice'] for o in outbounds for i in inbounds])
    roundtrip_cost = min([math.inf] + [trip['MinPrice'] for trip in roundtrips])
    
    return min(multiticket_cost, roundtrip_cost)
#
# qs = search_quotes("LOND-sky", "PMO-sky", "2018-01-03", "2018-01-06")
# print(qs)