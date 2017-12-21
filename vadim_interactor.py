from util import process_quotes

def roundtrip_quote(outbound_quote, inbound_quote):
    return {
        'OutboundLeg': outbound_quote['OutboundLeg'] or outbound_quote['InboundLeg'],
        'InboundLeg': inbound_quote['InboundLeg'] or outbound_quote['OutboundLeg'],
        'MinPrice': outbound_quote['MinPrice'] + inbound_quote['MinPrice'],
        'MultiTicket': True
    }

def roundtrips(quotes):
    roundtrips = filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' in quote, quotes)
    outbounds = filter(lambda quote: 'InboundLeg' not in quote and 'OutboundLeg' in quote, quotes)
    inbounds = filter(lambda quote: 'InboundLeg' in quote and 'OutboundLeg' not in quote, quotes)
    
    return list(roundtrips) + [roundtrip_quote(outbound, inbound) for outbound in outbounds for inbound in inbounds]

def memoized(f):
    table = {}
    
    def memoized_f(*args):
        subtable = table
        last_arg = None
        for arg in args:     
            if last_arg:
                if last_arg not in subtable:
                    subtable[last_arg] = {}
                subtable = subtable[last_arg]
            last_arg = arg
            
        if last_arg not in subtable:
            subtable[last_arg] = f(*args)
        return subtable[last_arg]
    
    return memoized_f

@rate_limited(490, 60)
@memoized
def skyscanner_search(origin, destination, outbound, inbound):
    skyscanner_response = pricer.get_cheapest_quotes(
        market='RU',
        currency='RUB',
        locale='en-GB',
        originplace=origin,
        destinationplace=destination,
        outbounddate=outbound,
        inbounddate=inbound,
        adults=1).parsed
    return skyscanner_response

def as_date(date_time):
    return date_time.rsplit('T')[0]

def search_quotes(origin, destination, outbound, inbound):
    origin = place_ids(origin)[0]
    destination = place_ids(destination)[0]
    outbound = as_date(outbound)
    inbound = as_date(inbound)
    
    quotes = skyscanner_search(origin, destination, outbound, inbound)
    quotes = process_quotes(quotes)
    quotes = roundtrips(quotes)
    quotes = sorted(quotes, key=lambda quote: quote['MinPrice'])
    
    return quotes

def same_city(place1, place2):
    place1ids = place_ids(place1)
    place2ids = place_ids(place2)
    
    for id1 in place1ids:
        if id1 in place2ids:
            return True
        
    return False

def date_inside(candidate_date, containing_date):
    if containing_date == 'anytime':
        return True
    
    return candidate_date.startswith(containing_date)