from collections import deque
from statistics import mean


class MovingAverage:
    def __init__(self, size=5):
        self.values = deque(maxlen=size)

    def update(self, value):
        try:
            # Ignore invalid values
            if value is None:
                return self._safe_mean()

            self.values.append(value)
            return self._safe_mean()

        except Exception as e:
            # Last line of defense: never crash the thread
            print(f"[MovingAverage] Error: {e}")
            return self._safe_mean()

    def _safe_mean(self):
        # Only average valid numbers
        valid = [v for v in self.values if isinstance(v, (int, float))]
        return mean(valid) if valid else None

    def reset(self):
        self.values.clear()