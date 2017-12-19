import numpy as np
import json
import datetime
import math


# class SkyscannerInteractor:
#     def __init__(self, cities, sources):
#         self.cities = cities
#         self.sources = sources
#
#     def


class Solution:
    def __init__(self, destination, date_come, date_leave, sources):
        self.destination = destination
        self.date_come = date_come
        self.date_leave = date_leave
        self.sources = sources

    def price(self):
        self.quotes = []

        for source in self.sources:
            pass

        return np.random.random()*1000

    def __repr__(self):
        out = "TO: {0},\tCOME:{1},\tLEAVE:{2}"
        return out.format(self.destination, self.date_come, self.date_leave)


class SimAnnSolver:
    def __init__(self, destinations, date_from, date_to, sources):
        self.sources = sources
        self.destinations = np.array(destinations)
        self.date_range = (date_from, date_to)

    FORMAT = "%Y-%m-%d"

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

        out = Solution(dest, date_come, date_leave, self.sources)

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

        return Solution(dest, date_come, date_leave, self.sources)

    def solve(self, max_iter=4000, T_0=1.0, T_min=0.1, cooling_frequency=200, exp_gamma=0.99):

        T = T_0
        solution_curr = self.random_solution()
        obj_curr = solution_curr.price()

        solution_best, obj_best = solution_curr, obj_curr

        for i in range(max_iter):
            solution_neighbour = self.random_neighbour(solution_curr)
            obj_neighbour = solution_neighbour.price()

            obj_delta = obj_neighbour-obj_curr

            if np.random.random() < np.exp(-obj_delta / T):
                obj_curr, solution_curr = obj_neighbour, solution_neighbour

                if obj_curr < obj_best:
                    obj_best, solution_best = obj_curr, solution_curr

            if i % cooling_frequency == 0 and T > T_min:
                T *= exp_gamma

        return solution_best, obj_best


