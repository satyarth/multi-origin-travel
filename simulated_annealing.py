import numpy as np
from util import min_roundtrip_price, search_quotes
import json
import datetime
import math
from multiprocessing.dummy import Pool as ThreadPool

FORMAT = "%Y-%m-%d"


class SkyscannerInteractor:
    def __init__(self, cities, sources):
        self.cities = cities
        self.sources = sources

    def get_price(self, solution):
        self.price = 0

        destination_code = self.cities[solution.destination]
        date_come_str = datetime.datetime.strftime(solution.date_come, FORMAT)
        date_leave_str = datetime.datetime.strftime(solution.date_leave, FORMAT)

        def fetch_price(source):
            quotes = search_quotes(self.cities[source], destination_code, date_come_str, date_leave_str)
            min_price = min_roundtrip_price(quotes)
            self.price += min_price

        pool = ThreadPool(len(self.sources))
        pool.map(fetch_price, self.sources)


        # for s in self.sources:
        #     # print(self.cities[s], destination_code, date_come_str, date_leave_str)
        #     quotes = search_quotes(self.cities[s], destination_code, date_come_str, date_leave_str)
        #     min_price = min_roundtrip_price(quotes)
        #     self.price += min_price

        return self.price



class Solution:
    def __init__(self, destination, date_come, date_leave):
        self.destination = destination
        self.date_come = date_come
        self.date_leave = date_leave

    def __repr__(self):
        out = "TO: {0},\tCOME: {1},\tLEAVE: {2}"
        return out.format(self.destination, self.date_come, self.date_leave)


class SimAnnSolver:
    def __init__(self, date_from, date_to, interactor):

        self.interactor = interactor
        self.date_range = (date_from, date_to)
        self.destinations = np.array(list(interactor.cities.keys()))



    def random_date(self, start, end):
        prop = np.random.random()
        ptime = start + prop * (end - start)
        ptime = ptime.replace(hour=0, minute=0, second=0, microsecond=0)
        return ptime

    def random_solution(self):
        print(type(self.destinations))
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

        if chance < 1./3:
            dest = np.random.choice(self.destinations)
        elif chance < 2./3:
            date_come = self.random_date(self.date_range[0], date_leave)
        else:
            date_leave = self.random_date(date_come, self.date_range[1])

        return Solution(dest, date_come, date_leave)

    def solve(self, max_iter=4000, T_0=1.0, T_min=0.1, cooling_frequency=200, exp_gamma=0.99):

        T = T_0
        solution_curr = self.random_solution()
        obj_curr = self.interactor.get_price(solution_curr)



        solution_best, obj_best = solution_curr, obj_curr

        for i in range(max_iter):
            solution_neighbour = self.random_neighbour(solution_curr)
            obj_neighbour = self.interactor.get_price(solution_neighbour)

            obj_delta = obj_neighbour-obj_curr

            print(obj_delta)

            if np.random.random() < np.exp(-obj_delta / T):
                obj_curr, solution_curr = obj_neighbour, solution_neighbour

                if obj_curr < obj_best:
                    obj_best, solution_best = obj_curr, solution_curr

            if i % cooling_frequency == 0 and T > T_min:
                T *= exp_gamma
            print(solution_neighbour, obj_neighbour)
            print(solution_curr, obj_curr)



        return solution_best, obj_best


# with open("city_ids.json") as f:
#     cities = json.load(f)
#
# sources = list(cities.keys())[30:32]
#
# print(sources)
#
# date_from = datetime.datetime.strptime("2018-01-01", FORMAT)
# date_to = datetime.datetime.strptime("2018-01-20", FORMAT)
#
# interactor = SkyscannerInteractor(cities, sources)
# solver = SimAnnSolver(date_from, date_to, interactor)
# solver.solve(T_0 = 1000)
#
#
# print(solver.random_solution())