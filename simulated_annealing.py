import numpy as np
from util import min_roundtrip_price, search_quotes, random_date, SkyscannerInteractor, FORMAT
import json
import datetime, time
import math
from search import SearchModel
from solution import Solution, FORMAT


class SimAnnSolver:
    def __init__(self, date_from, date_to, interactor, newbest_callback, stop_callback, min_days=0):

        self.interactor = interactor
        self.date_range = (date_from, date_to)
        self.destinations = interactor.cities
        self.min_days=min_days
        self.newbest_callback = newbest_callback
        self.stop_callback = stop_callback

    def random_solution(self):
        dest = np.random.choice(self.destinations)
        days_gap = datetime.timedelta(days=self.min_days)
        date_come = random_date(self.date_range[0], self.date_range[1]-days_gap)
        date_leave = random_date(date_come+days_gap, self.date_range[1])

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
            date_come = random_date(self.date_range[0], date_leave-days_gap)
        else:
            date_leave = random_date(date_come+days_gap, self.date_range[1])

        return Solution(dest, date_come, date_leave)

    def solve(self, max_iter=400, T_0=5000.0, T_min=0.1, cooling_frequency=10, exp_gamma=0.99):

        T = T_0
        solution_curr = self.random_solution()
        obj_curr = self.interactor.get_price(solution_curr)

        solution_best, obj_best = solution_curr, obj_curr

        st = time.time()

        for i in range(max_iter):

            if self.stop_callback():
                break

            solution_neighbour = self.random_neighbour(solution_curr)
            obj_neighbour = self.interactor.get_price(solution_neighbour)

            obj_delta = obj_neighbour-obj_curr

            if np.random.random() < np.exp(-obj_delta / T):
                obj_curr, solution_curr = obj_neighbour, solution_neighbour

                if obj_curr < obj_best:
                    obj_best, solution_best = obj_curr, solution_curr
                    self.newbest_callback(solution_best)

            if i % cooling_frequency == 0 and T > T_min:
                T *= exp_gamma



        return solution_best, obj_best


def solve_SA(origins, dates, destination, tabu_dates, tabu_destinations, solution_callback, stop_callback, min_days=0, city_ids_file='city_ids.json'):
    outbound_date, inbound_date = dates

    with open(city_ids_file) as f:
        cities = list(json.load(f).values())

    interactor = SkyscannerInteractor(cities, origins)
    inbound_date = datetime.datetime.strptime(inbound_date, FORMAT)
    outbound_date = datetime.datetime.strptime(outbound_date, FORMAT)

    solver = SimAnnSolver(outbound_date, inbound_date, interactor, solution_callback, stop_callback, min_days)
    return solver.solve(max_iter=100)[0]


if __name__ == '__main__':
    # np.random.seed(57)
    outdate = "2018-01-01"
    indate = "2018-01-15"

    origins = ['RIGA', 'BUDA', 'MOSC']

    solution_cb = lambda s: print(s)
    stop_cb = lambda: False

    min_days = 3

    with open('city_ids.json') as f:
        cities = list(json.load(f).values())

    interactor = SkyscannerInteractor(cities, origins)
    inbound_date = datetime.datetime.strptime(indate, FORMAT)
    outbound_date = datetime.datetime.strptime(outdate, FORMAT)

    solver = SimAnnSolver(outbound_date, inbound_date, interactor, solution_cb, stop_cb, min_days)



    sol = solve_SA(outdate, indate, origins, solution_cb, stop_cb, min_days)

    from manager import SolutionManager

    sm = SolutionManager(1,2)

    links = sm.get_links(sol)

    print(links)