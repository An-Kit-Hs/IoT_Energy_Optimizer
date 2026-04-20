from .base import BaseDevice

class LightDevice(BaseDevice):

    def __init__(self, mqtt, name, gpio):
        super().__init__(mqtt, f"control/{name}/state")
        self.name = name
        self.gpio = gpio

    def turn_on(self):
        if self.state == "ON":
            return

        self.gpio.set_device(self.name, True)

        self.state = "ON"
        print(f"[LIGHT] {self.name} ON (GPIO)")

    def turn_off(self):
        if self.state == "OFF":
            return

        self.gpio.set_device(self.name, False)

        self.state = "OFF"
        print(f"[LIGHT] {self.name} OFF (GPIO)")