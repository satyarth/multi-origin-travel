class Solution:
    def __init__(self, destination, date_come, date_leave):
        self.destination = destination
        self.date_come = date_come
        self.date_leave = date_leave
        self.routes = None
        self.price = None

    def __repr__(self):
        out = "TO: {0},\tCOME: {1},\tLEAVE: {2}"
        return out.format(self.destination, self.date_come, self.date_leave)
