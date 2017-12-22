from solution import Solution
from datetime import datetime
from vadim_interactor import place_ids, as_python_date, search_quotes

def as_date(date_time):
    return date_time.rsplit('T')[0]

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

def all_destinations(* quotes):
    return [quote['OutboundLeg']['DestinationDetails'] for quote in quotes]
def all_outbound_dates(* quotes):
    return [quote['OutboundLeg']['DepartureDate'] for quote in quotes]
def all_inbound_dates(* quotes):
    return [quote['InboundLeg']['DepartureDate'] for quote in quotes]
def all_dates(* quotes):
    return [(quote['OutboundLeg']['DepartureDate'], quote['InboundLeg']['DepartureDate']) for quote in quotes]

def feasible_solution(* quotes):
    destinations = all_destinations(*quotes)
    outbounds = all_outbound_dates(*quotes)
    inbounds = all_inbound_dates(*quotes)
    
    feasible = True
    feasible &= all([same_city(dest1, dest2) for dest1 in destinations for dest2 in destinations])
    feasible &= outbounds[1:] == outbounds[:-1] # all outbound dates are identical
    feasible &= inbounds[1:]  == inbounds[:-1]  # all inbound  dates are identical
    
    solution = None
    
    if feasible:
        solution = Solution(place_ids(destinations[0])[0], as_python_date(outbounds[0]), as_python_date(inbounds[0]))
        solution.routes = quotes
        solution.price = sum(quote['MinPrice'] for quote in quotes)
    
    return solution

def lower_bound(origins, dates=('anytime', 'anytime'), destination='anywhere', 
                tabu_destinations=[], tabu_dates=[]):
    def allowed(quote):
        allowed = True
        allowed &= not any([same_city(tabu, quote['OutboundLeg']['DestinationDetails']) for tabu in tabu_destinations])
        allowed &= not any([date_inside(quote['OutboundLeg']['DepartureDate'], tabu_outbound) and
                            date_inside(quote['InboundLeg']['DepartureDate'], tabu_inbound)
                            for tabu_outbound, tabu_inbound in tabu_dates])
        return allowed
    
    if not allowed({'OutboundLeg': {'DestinationDetails': destination, 'DepartureDate': dates[0]},
                    'InboundLeg':  {'OriginDetails': destination, 'DepartureDate': dates[1]}}):
        raise Exception('Infeasible. Constraints contradict each other')
    
    price = 0
    solution = []
    
    for origin in origins:
        quotes = search_quotes(origin, destination, dates[0], dates[1])
        quotes = list(filter(allowed, quotes))
        
        if len(quotes) == 0:
            return float('inf'), None
        
        best_quote = quotes[0] # they are pre-sorted, see search_quotes()
        solution.append(best_quote)
        price += best_quote['MinPrice']
            
    return price, solution

def solve_branch_and_bound(outbd, inbd, origins, solution_callback=None, stop_callback=None):
    required_dates = (outbd, inbd)
    leaf_solutions = []
    best_feasible_solution = [Solution('anywhere', 'anytime', 'anytime')]
    best_feasible_solution[0].price = float('inf')
    
    def tryConstraints(dates=('anytime', 'anytime'), destination='anywhere', 
                       tabu_destinations=[], tabu_dates=[]):
        price, quotes = lower_bound(origins, dates, destination, tabu_destinations, tabu_dates)
        
        leaf_solutions.append({
            'price': price,
            'quotes': quotes,
            'destination': destination,
            'tabu_destinations': tabu_destinations,
            'tabu_dates': tabu_dates
        })
        
        if price < best_feasible_solution[0].price:
            feasible_sol = feasible_solution(*quotes)
            
            if feasible_sol:
                best_feasible_solution[0] = feasible_sol

                if solution_callback:
                    solution_callback(best_feasible_solution[0])
            
    tryConstraints()
    
    while not (stop_callback and stop_callback()):
        print("NEW ITERATION", stop_callback())
        best_solution = min(leaf_solutions, key=lambda solution: solution['price'])
        leaf_solutions.remove(best_solution)
        
        if best_solution['price'] >= best_feasible_solution[0].price:
            return best_feasible_solution[0]
        
        destinations = all_destinations(*best_solution['quotes'])
        date_pairs = all_dates(*best_solution['quotes'])
        
        for destination, tabu_destinations in zip(destinations + ['anywhere'],
                                                  [[] for d in destinations] + 
                                                  [best_solution['tabu_destinations'] + destinations]):
            for date_pair, tabu_date_pairs in zip(date_pairs + [required_dates],
                                                  [[] for d in date_pairs] + 
                                                  [best_solution['tabu_dates'] + date_pairs]):             
                tryConstraints(date_pair, destination, tabu_destinations, tabu_date_pairs)