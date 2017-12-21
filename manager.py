

class SolutionManager:

    def __init__(self, solve_func, solution_processor):
        self.solve = solve_func
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

    def get_links(self, solution):
        if not solution.routes:
            return []

        links = []

        # def get

