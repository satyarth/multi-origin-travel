import pickle
from vadim_interactor import *
from solution import Solution
import math

with open('best_dests.pickle', 'rb') as b:
    best_dests = pickle.load(b)

def solve_informed_exhaustion(outbound, inbound, origins, solution_callback=None, stop_callback=None):
    best_solution = Solution('anywhere', 'anytime', 'anytime')
    best_solution.price = math.inf
    
    for dest in best_dests:
        if stop_callback and stop_callback():
            return
        
        basic_routes = [next(iter(search_quotes(origin, dest, outbound, inbound)), None) for origin in origins]
        if not all(basic_routes):
            continue
            
        for outbound_date, inbound_date in all_dates(*basic_routes):
            routes = [next(iter(search_quotes(origin, dest, outbound_date, inbound_date)), None) for origin in origins]

            if not all(routes):
                continue
            
            price = sum(route['MinPrice'] for route in routes)
            if price < best_solution.price:
                best_solution = Solution(place_ids(dest)[0], 
                                         as_python_date(outbound_date), 
                                         as_python_date(inbound_date))
                best_solution.routes = routes
                best_solution.price = price

                if solution_callback:
                    solution_callback(best_solution)
            
    return best_solution