import time
import config

class ExhaustState:
    OFF = "OFF"
    PREVENTIVE = "PREVENTIVE"
    EMERGENCY = "EMERGENCY"
    COOLDOWN = "COOLDOWN"

class ExhaustControllerFSM:

    def __init__(self, devices):
        self.devices = devices

        self.state = ExhaustState.OFF
        self.last_change = time.time()

        self.cooldown_start = None

        # thresholds
        self.ON_THRESHOLD = config.AQI_PREVENTIVE_THRESHOLD
        self.OFF_THRESHOLD = config.AQI_PREVENTIVE_THRESHOLD - 10
        self.EMERGENCY = config.AQI_EMERGENCY_THRESHOLD

        # timing
        self.MIN_ON_TIME = 10
        self.MIN_OFF_TIME = 10
        self.COOLDOWN_TIME = 30

    def _can_switch(self, new_state):
        elapsed = time.time() - self.last_change

        if self.state != ExhaustState.OFF:
            if new_state == ExhaustState.OFF and elapsed < self.MIN_ON_TIME:
                return False
        else:
            if new_state != ExhaustState.OFF and elapsed < self.MIN_OFF_TIME:
                return False

        return True

    def _apply(self, new_state):
        if new_state == ExhaustState.OFF:
            self.devices.turn_off_exhaust()
        else:
            self.devices.turn_on_exhaust()

        self.state = new_state
        self.last_change = time.time()

    def update(self, score, trend_rising):

        desired = self.state

        if isinstance(score, (int, float)):

            if score > self.EMERGENCY:
                desired = ExhaustState.EMERGENCY

            elif score > self.ON_THRESHOLD and trend_rising:
                desired = ExhaustState.PREVENTIVE

            elif score < self.OFF_THRESHOLD:
                desired = (
                    ExhaustState.COOLDOWN
                    if self.state != ExhaustState.OFF
                    else ExhaustState.OFF
                )

        # -------- cooldown --------
        if desired == ExhaustState.COOLDOWN:
            if self.cooldown_start is None:
                self.cooldown_start = time.time()

            if time.time() - self.cooldown_start > self.COOLDOWN_TIME:
                desired = ExhaustState.OFF
                self.cooldown_start = None
        else:
            self.cooldown_start = None

        # -------- apply --------
        if desired != self.state and self._can_switch(desired):
            self._apply(desired)

    def is_on(self):
        return self.state != ExhaustState.OFF