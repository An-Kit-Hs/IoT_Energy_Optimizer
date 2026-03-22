from collections import defaultdict
import datetime

class OccupancyPatternModel:

    def __init__(self):
        self.presence = defaultdict(int)
        self.samples = defaultdict(int)

    def update(self, occupied):
        hour = datetime.datetime.now().hour
        self.samples[hour] += 1

        if occupied:
            self.presence[hour] += 1

    def probability(self):
        hour = datetime.datetime.now().hour
        s = self.samples[hour]

        if s == 0:
            return 0

        return self.presence[hour] / s