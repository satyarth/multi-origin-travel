class Solution:
    def __init__(self, destination, date_come, date_leave):
        self.destination = destination
        self.date_come = date_come
        self.date_leave = date_leave
        self.routes = None
        self.price = None

    def __repr__(self):
        if self.price:
            return "TO: {0},\tCOME: {1},\tLEAVE: {2}, PRICE: {3}".\
                format(self.destination, self.date_come, self.date_leave, self.price)
        else:
            return "TO: {0},\tCOME: {1},\tLEAVE: {2}". \
                format(self.destination, self.date_come, self.date_leave)
