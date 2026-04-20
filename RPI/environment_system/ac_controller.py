import time


class ACState:
    OFF = "OFF"
    COOLING = "COOLING"
    FAN = "FAN"
    DRY = "DRY"


class ACControllerFSM:

    def __init__(self, devices):
        self.devices = devices

        self.state = ACState.OFF
        self.temp = None
        self.mode = None

        self.last_change = time.time()
        self.exhaust_block_until = 0

        # thresholds
        self.ON_THRESHOLD = 27
        self.OFF_THRESHOLD = 24.5

        # timing
        self.MIN_ON_TIME = 30
        self.MIN_OFF_TIME = 20

    def _compute_temp(self, feels_like):
        if feels_like <= 26:
            return 24
        elif feels_like <= 28:
            return 22
        elif feels_like <= 30:
            return 20
        elif feels_like <= 32:
            return 18
        else:
            return 18

    def _select_mode(self, feels_like, humidity):
        if feels_like is not None and feels_like < 24:
            return "fan"

        if humidity is not None:
            if humidity > 75:
                return "dry"
            elif humidity < 65:
                return "cool"

        return self.mode or "cool"

    def _can_switch(self, new_state):
        elapsed = time.time() - self.last_change

        if self.state != ACState.OFF:
            if new_state == ACState.OFF and elapsed < self.MIN_ON_TIME:
                return False
        else:
            if new_state != ACState.OFF and elapsed < self.MIN_OFF_TIME:
                return False

        return True

    def _apply(self, new_state, temp, mode):
        if new_state == ACState.OFF:
            self.devices.turn_off_ac()
        else:
            self.devices.turn_on_ac(temp, mode)

        self.state = new_state
        self.temp = temp
        self.mode = mode
        self.last_change = time.time()

    def update(self, occupied, feels_like, humidity, exhaust_on):
        now = time.time()

        desired = self.state
        temp = self.temp
        mode = self.mode

        # -------- Exhaust override --------
        if exhaust_on:
            self.exhaust_block_until = max(self.exhaust_block_until, now + 60)
            desired = ACState.OFF

        elif now < self.exhaust_block_until:
            desired = ACState.OFF

        # -------- Comfort logic --------
        elif occupied and feels_like is not None:

            if feels_like > self.ON_THRESHOLD:
                mode = self._select_mode(feels_like, humidity)

                new_temp = self._compute_temp(feels_like)

                if self.temp is not None and abs(new_temp - self.temp) < 1:
                    temp = self.temp
                else:
                    temp = new_temp

                if mode == "fan":
                    desired = ACState.FAN
                elif mode == "dry":
                    desired = ACState.DRY
                else:
                    desired = ACState.COOLING

            elif feels_like < self.OFF_THRESHOLD:
                desired = ACState.OFF

        else:
            desired = ACState.OFF

        # -------- Apply transitions --------
        if desired != self.state:
            if self._can_switch(desired):
                self._apply(desired, temp, mode)

        elif self.state != ACState.OFF:
            if temp != self.temp or mode != self.mode:
                self.devices.turn_on_ac(temp, mode)
                self.temp = temp
                self.mode = mode

    def set_external_state(self, state: bool, temp=None, mode=None):
        if state:
            use_temp = temp if temp is not None else self.temp or 24
            use_mode = (mode if mode is not None else self.mode or "cool").lower()

            if use_mode == "fan":
                new_state = ACState.FAN
            elif use_mode == "dry":
                new_state = ACState.DRY
            else:
                new_state = ACState.COOLING

            self._apply(new_state, use_temp, use_mode)
        else:
            self._apply(ACState.OFF, None, None)

    def is_on(self):
        return self.state != ACState.OFF

    def get_state(self):
        return {
            "state": self.state,
            "temp": self.temp,
            "mode": self.mode
        }