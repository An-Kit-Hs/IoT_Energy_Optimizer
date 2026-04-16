import time
import config


class ACController:

    def __init__(self, devices):
        self.devices = devices

        self._on = False
        self._temp = None
        self._mode = None
        self._last_change = time.time()

        # Hysteresis (feels-like)
        self.ON_THRESHOLD = 26
        self.OFF_THRESHOLD = 24

        # Timing protection
        self.MIN_ON_TIME = 30
        self.MIN_OFF_TIME = 20
        
    def _compute_temp(self, feels_like):
        # Base comfort
        base = 24

        # Cooling strength factor
        k = 0.5

        # Adjust temperature
        temp = base - k * (feels_like - base)
        temp = max(18, min(26, temp))

        return round(temp)


    def update(self, occupied, feels_like, humidity, exhaust_on):
        now = time.time()

        # Exhaust override
        if exhaust_on:
            if self._on:
                self.devices.turn_off_ac()
                self._on = False
            return

        desired = self._on
        temp = self._temp
        mode = self._mode

        # -------- Mode decision --------
        if humidity is not None:
            if humidity > 70:
                mode = "dry"
            elif feels_like is not None and feels_like < 24:
                mode = "fan"
            else:
                mode = "cool"

        # -------- State decision --------
        if occupied and feels_like is not None:
            if feels_like > self.ON_THRESHOLD:
                desired = True
            elif feels_like < self.OFF_THRESHOLD:
                desired = False
        else:
            desired = False
            
        if temp is not None and  self._temp is not None and abs(temp - self._temp) < 1:
            temp = self._temp

        # -------- Temp selection --------
        if desired:
            temp = self._compute_temp(feels_like)

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
                self.devices.turn_on_ac(temp, mode)
            else:
                self.devices.turn_off_ac()

        elif self._on:
            if temp != self._temp or mode != self._mode:
                self.devices.turn_on_ac(temp, mode)

        self._temp = temp
        self._mode = mode

    def is_on(self):
        return self._on

    def get_state(self):
        return {
            "on": self._on,
            "temp": self._temp,
            "mode": self._mode
        }