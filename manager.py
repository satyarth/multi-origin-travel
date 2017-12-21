from util import get_cheapest_link

class SolutionManager:

    def __init__(self, solve_func, solution_processor):
        self.solve_func = solve_func
        self.stopped = False
        self.solutions = {}
        self.current_id = 0
        self.solution_processor = solution_processor

    def stop_func(self):
        return self.stopped

    def store_solution(self, solution):
        self.solutions[self.current_id] = solution
        self.solution_processor(self.current_id, solution)
        self.current_id += 1

    def solve(self, outbound_date, inbound_date, origins, min_days):
        self.solve_func(outbound_date, inbound_date, origins, self.stop_func, self.store_solution, min_days)

    def get_links(self, solution):
        if not solution.routes:
            return []

        def route2links(route):
            links = []
            outleg = route['OutboundLeg']
            inleg = route['InboundLeg']

            from_city = outleg['OriginDetails']['CityId']
            to_city = inleg['OriginDetails']['CityId']

            if route['MultiTicket']:
                link_out = get_cheapest_link(from_city,
                                               to_city,
                                               outleg['DepartureDate'][:10])

                links.append({'From': from_city,
                              'To': to_city,
                              'IsRound': False,
                              'Link': link_out})


                link_in = get_cheapest_link(to_city,
                                               from_city,
                                               inleg['DepartureDate'][:10])

                links.append({'From': to_city,
                              'To': from_city,
                              'IsRound': False,
                              'Link': link_in})

            else:
                link =  get_cheapest_link(outleg['OriginDetails']['CityId'],
                                               outleg['DestinationDetails']['CityId'],
                                               outleg['DepartureDate'][:10],
                                               inleg['DepartureDate'][:10])

                links.append({'From': from_city,
                              'To': to_city,
                              'IsRound': True,
                              'Link': link})


            return links

        links = []
        for route in solution.routes:
            links += route2links(route)

        return links





