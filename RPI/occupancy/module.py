import time
import config


class OccupancyModule:

    def __init__(self):
        self.state = "EMPTY"
        self.last_seen = 0
        self.first_seen = None
        self.last_change = time.time()

    def update(self, count: int):
        now = time.time()

        # --- Detect presence (positive hysteresis) ---
        if count > 0:
            if self.first_seen is None:
                self.first_seen = now

            if now - self.first_seen >= config.POSITIVE_DELAY:
                self.last_seen = now
                desired_state = "OCCUPIED"
            else:
                desired_state = self.state  # wait until stable

        else:
            self.first_seen = None

            # --- Negative hysteresis ---
            if now - self.last_seen > config.EMPTY_DELAY:
                desired_state = "EMPTY"
            else:
                desired_state = self.state

        # --- Rapid switching protection ---
        time_in_state = now - self.last_change

        if self.state == "OCCUPIED":
            if desired_state == "EMPTY" and time_in_state < config.MIN_ON_TIME:
                return self._result(count)

        elif self.state == "EMPTY":
            if desired_state == "OCCUPIED" and time_in_state < config.MIN_OFF_TIME:
                return self._result(count)

        # --- Apply state change ---
        if desired_state != self.state:
            self.state = desired_state
            self.last_change = now

        return self._result(count)

    def _result(self, count):
        return {
            "state": self.state,
            "occupied": self.state == "OCCUPIED",
            "count": count
        }