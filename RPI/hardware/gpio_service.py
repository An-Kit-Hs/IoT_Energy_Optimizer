import RPi.GPIO as GPIO  # type: ignore
import config


class GPIOService:
    def __init__(self):
        self.device_pins = config.DEVICE_PINS
        self.active_low = config.ACTIVE_LOW

        self.states = {d: False for d in self.device_pins}

        GPIO.setmode(GPIO.BCM)

        print("[GPIO] Initializing...")
        for device, pin in self.device_pins.items():
            GPIO.setup(pin, GPIO.OUT)
            self._write(pin, False)
            print(f"  - {device} → GPIO {pin}")

    # -------- PUBLIC API --------

    def set_device(self, device, state: bool):
        if device not in self.device_pins:
            print(f"[GPIO] Unknown device: {device}")
            return

        state = bool(state)

        if self.states[device] == state:
            return

        pin = self.device_pins[device]
        self._write(pin, state)

        self.states[device] = state

        print(f"[GPIO] {device} → {'ON' if state else 'OFF'}")

    def get_device(self, device):
        return self.states.get(device)

    def toggle_device(self, device):
        if device not in self.states:
            print(f"[GPIO] Unknown device: {device}")
            return

        self.set_device(device, not self.states[device])

    def all_devices(self):
        return self.states.copy()

    # -------- INTERNAL --------

    def _write(self, pin, state):
        if self.active_low:
            GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)
        else:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    def cleanup(self):
        GPIO.cleanup()