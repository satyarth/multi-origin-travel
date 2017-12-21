import numpy as np
from util import min_roundtrip_price, search_quotes
import json
import datetime, time
import math
from multiprocessing.dummy import Pool as ThreadPool
from search import SearchModel
from solution import Solution

FORMAT = "%Y-%m-%d"


class SkyscannerInteractor:
    def __init__(self, cities, sources):
        self.cities = cities
        self.sources = sources


    def get_price(self, solution):
        price = [0,]
        routes = []

        destination_code = self.cities[solution.destination]
        date_come_str = datetime.datetime.strftime(solution.date_come, FORMAT)
        date_leave_str = datetime.datetime.strftime(solution.date_leave, FORMAT)

        def fetch_price(source):
            quotes = search_quotes(self.cities[source], destination_code, date_come_str, date_leave_str)
            min_price, route = min_roundtrip_price(quotes)
            routes.append(route)
            price[0] = price[0] + min_price

        pool = ThreadPool(len(self.sources))
        pool.map(fetch_price, self.sources)

        solution.price = price[0]
        solution.routes = routes

        return price[0]


class SimAnnSolver:
    def __init__(self, date_from, date_to, interactor, newbest_callback, min_days=0):

        self.interactor = interactor
        self.date_range = (date_from, date_to)
        self.destinations = np.array(list(interactor.cities.keys()))
        self.min_days=min_days
        self.newbest_callback = newbest_callback



    def random_date(self, start, end):
        prop = np.random.random()
        ptime = start + prop * (end - start)
        ptime = ptime.replace(hour=0, minute=0, second=0, microsecond=0)
        return ptime

    def random_solution(self):
        dest = np.random.choice(self.destinations)
        date_come = self.random_date(*self.date_range)
        date_leave = self.random_date(date_come, self.date_range[1])

        out = Solution(dest, date_come, date_leave)

        return out

    def random_neighbour(self, solution):
        dest = solution.destination
        date_come = solution.date_come
        date_leave = solution.date_leave

        chance = np.random.random()
        days_gap = datetime.timedelta(days=self.min_days)

        if chance < 1./3:
            dest = np.random.choice(self.destinations)
        elif chance < 2./3:
            date_come = self.random_date(self.date_range[0], date_leave-days_gap)
        else:
            date_leave = self.random_date(date_come+days_gap, self.date_range[1])

        return Solution(dest, date_come, date_leave)

    def solve(self, max_iter=500, T_0=5000.0, T_min=0.1, cooling_frequency=10, exp_gamma=0.99):

        T = T_0
        solution_curr = self.random_solution()
        obj_curr = self.interactor.get_price(solution_curr)



        solution_best, obj_best = solution_curr, obj_curr

        st = time.time()

        for i in range(max_iter):
            solution_neighbour = self.random_neighbour(solution_curr)
            obj_neighbour = self.interactor.get_price(solution_neighbour)

            obj_delta = obj_neighbour-obj_curr

            # print(obj_delta)

            if np.random.random() < np.exp(-obj_delta / T):
                obj_curr, solution_curr = obj_neighbour, solution_neighbour

                if obj_curr < obj_best:
                    obj_best, solution_best = obj_curr, solution_curr
                    self.newbest_callback(solution_best)

            if i % cooling_frequency == 0 and T > T_min:
                T *= exp_gamma



        return solution_best, obj_best


np.random.seed(57)

with open("city_ids.json") as f:
    cities = json.load(f)

# sources = list(cities.keys())[18:21]
sources = ["Berlin", "Brussels", "London"]

print(sources)

date_from = datetime.datetime.strptime("2018-01-01", FORMAT)
date_to = datetime.datetime.strptime("2018-01-15", FORMAT)

jcb = lambda s: print()
nbcb = lambda s: print("New best solution: {0}".format(s))


interactor = SkyscannerInteractor(cities, sources)
solver = SimAnnSolver(date_from, date_to, interactor, newbest_callback=nbcb, min_days=3)
solution, price = solver.solve(T_0 = 5000, max_iter=400)

print(solution)
