from solution import Solution
from datetime import datetime
from vadim_interactor import *

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
        solution.destination_city = destinations[0]['CityName']
    
    return solution

class ContradictingConstraints(Exception):
    pass

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
        raise ContradictingConstraints('Infeasible. Constraints contradict each other')
    
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

def solve_branch_and_bound( origins, 
                            dates=('anytime', 'anytime'), 
                            destination='anywhere',
                            tabu_dates=[],
                            tabu_destinations=[], 
                            solution_callback=None, 
                            stop_callback=None ):

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
            
    tryConstraints(dates, destination, tabu_destinations, tabu_dates)
    
    while not (stop_callback and stop_callback()):
        best_solution = min(leaf_solutions, key=lambda solution: solution['price'])
        leaf_solutions.remove(best_solution)
        
        if best_solution['price'] >= best_feasible_solution[0].price:
            return best_feasible_solution[0]
        
        found_destinations = all_destinations(*best_solution['quotes'])
        found_date_pairs = all_dates(*best_solution['quotes'])
        
        for dest, tabu_destinations in zip(found_destinations + [destination],
                                            [[] for d in found_destinations] + 
                                            [best_solution['tabu_destinations'] + found_destinations]):
            for date_pair, tabu_date_pairs in zip(found_date_pairs + [dates],
                                                  [[] for d in found_date_pairs] + 
                                                  [best_solution['tabu_dates'] + found_date_pairs]):
                try:       
                    tryConstraints(date_pair, dest, tabu_destinations, tabu_date_pairs)
                except ContradictingConstraints:
                    return best_feasible_solution[0]