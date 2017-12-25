from datetime import datetime, timedelta
from time import time
from solution import Solution
import json
from util import min_roundtrip_price, search_quotes, random_date, SkyscannerInteractor, FORMAT
from numpy.random import choice, rand
from multiprocessing.dummy import Pool as ThreadPool

class GASolver:
    def __init__(self, interactor, origins, date_from, date_to, min_days=3, population_size=20):
        self.interactor = interactor
        self.destinations = interactor.cities
        self.date_from = date_from
        self.date_to = date_to
        self.min_days = min_days
        self.origins = origins
        self.population_size = population_size
        self.population = [self.get_random_solution() for _ in range(self.population_size)]
        self.new = round(self.population_size*0.25)
        self.crossed = round(self.population_size*0.70)
        self.old = self.population_size - self.new - self.crossed
        self.costs = {}
    
    def assign_cost(self, solution):
        price = interactor.get_price(solution)
        self.costs[solution] = price
                           
    def assign_costs(self):
        self.costs = {}
        pool=ThreadPool(self.population_size)
        pool.map(self.assign_cost, self.population)
        self.population = sorted(self.population, key=lambda s: self.costs[s])
        
    
    def get_random_solution(self):
        destination = choice(self.destinations)
        days_gap = timedelta(days=self.min_days)
        outbound = random_date(self.date_from, self.date_to - days_gap)
        inbound = random_date(outbound + days_gap, self.date_to)
        return Solution(destination, outbound, inbound)
    
    def choose(self, s1, s2):
        if rand() > s1.price/(s1.price + s2.price):
            return s1
        
        return s2
    
    def cross_date(self, s1, s2):
        r = rand()
        if r < 0.25:
            return s1
        
        elif r < 0.5:
            return s2
        
        elif r < 0.75:
            return Solution(s1.destination, s1.date_come + (s2.date_come-s1.date_come)/2, s1.date_leave + (s2.date_leave-s1.date_leave)/2)
            
        else:
            return self.get_random_solution()
    
    def crossover(self, solution_pair):
        (s1, s2) = solution_pair
        
        s_date = self.cross_date(s1, s2)
        
        if rand() < 0.6:
            s_destination = self.choose(s1, s2)
        
        else:
            s_destination = self.get_random_solution()
        
        s = Solution(s_destination.destination, s_date.date_come, s_date.date_leave)
        return s
    
    def iterate(self):
        population = self.population
        population[-self.new:] = [self.get_random_solution() for _ in range(self.new)]
        
        pairs = [(choice(population[:self.old+self.crossed]), choice(population[:self.old+self.crossed])) for _ in range(self.crossed)]
        crossed = [self.crossover(pair) for pair in pairs]
        population[self.old:self.old + self.crossed] = crossed
        
        self.population = population

if __name__ == '__main__':
	origins = ["LON", "PARI", "BERL"]

	FORMAT = "%Y-%m-%d"
	date_from = datetime.strptime("2018-01-01", FORMAT)
	date_to = datetime.strptime("2018-01-15", FORMAT)

	from populator import process_city

	good_cities = []
	for origin in origins:
	    quotes = process_city(origin, govnokod=True)
	    quotes = sorted(quotes, key=lambda q: q['MinPrice'])

	    for q in quotes[:20]:
	        good_cities.append(q['OutboundLeg']['DestinationDetails']['CityId'])
	        
	interactor = SkyscannerInteractor(good_cities, origins)
	solver = GASolver(interactor, origins, date_from, date_to)

	while True:
	    start = time()
	    solver.assign_costs()
	    for i in range(5):
		    print(solver.population[i].price, solver.population[i].destination)
		    
	    print(time()-start)
	    solver.iterate()