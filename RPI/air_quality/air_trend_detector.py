from collections import deque


class AirTrendDetector:

    def __init__(self):

        self.history = deque(maxlen=6)

    def update(self, score):

        self.history.append(score)

        if len(self.history) < 6:
            return False

        trend = self.history[-1] - self.history[0]

        return trend > 15