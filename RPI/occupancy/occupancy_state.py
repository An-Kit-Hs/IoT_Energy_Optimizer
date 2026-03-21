import time


class OccupancyState:

    EMPTY_DELAY = 300

    def __init__(self):

        self.people = 0
        self.last_seen = 0
        self.state = "EMPTY"

    def update(self, count):

        now = time.time()

        self.people = count

        if count > 0:

            self.last_seen = now
            self.state = "OCCUPIED"

        elif now - self.last_seen > self.EMPTY_DELAY:

            self.state = "EMPTY"

        return self.state