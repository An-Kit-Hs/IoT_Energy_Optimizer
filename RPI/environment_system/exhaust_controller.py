import time
import config


class ExhaustController:

    def __init__(self, devices):
        self.devices = devices

        self._on = False
        self._last_change = time.time()

        # Hysteresis thresholds
        self.ON_THRESHOLD = config.AQI_PREVENTIVE_THRESHOLD
        self.OFF_THRESHOLD = config.AQI_PREVENTIVE_THRESHOLD - 10

        # Timing protection
        self.MIN_ON_TIME = 10
        self.MIN_OFF_TIME = 10

    def update(self, score, trend_rising):
        now = time.time()

        desired = self._on

        if isinstance(score, (int, float)):

            # Emergency
            if score > config.AQI_EMERGENCY_THRESHOLD:
                desired = True

            # Preventive
            elif score > self.ON_THRESHOLD and trend_rising:
                desired = True

            # Safe OFF
            elif score < self.OFF_THRESHOLD:
                desired = False

        # -------- Anti flip --------
        elapsed = now - self._last_change

        if self._on:
            if not desired and elapsed < self.MIN_ON_TIME:
                desired = True
        else:
            if desired and elapsed < self.MIN_OFF_TIME:
                desired = False

        # -------- Apply --------
        if desired != self._on:
            self._on = desired
            self._last_change = now

            if self._on:
                self.devices.turn_on_exhaust()
            else:
                self.devices.turn_off_exhaust()

    def is_on(self):
        return self._on