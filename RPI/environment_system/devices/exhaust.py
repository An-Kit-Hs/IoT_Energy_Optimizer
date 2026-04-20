from .base import BaseDevice

class ExhaustDevice(BaseDevice):

    def __init__(self, mqtt, name, gpio):
        super().__init__(mqtt, f"control/{name}/state")
        self.name = name
        self.gpio = gpio

    def turn_on(self):
        if self.state == "ON":
            return

        self.gpio.set_device(self.name, True)
        self.publish({"power": "on"})

        self.state = "ON"
        print(f"[EXHAUST] {self.name} ON (GPIO)")

    def turn_off(self):
        if self.state == "OFF":
            return

        self.gpio.set_device(self.name, False)
        self.publish({"power": "off"})

        self.state = "OFF"
        print(f"[EXHAUST] {self.name} OFF (GPIO)")