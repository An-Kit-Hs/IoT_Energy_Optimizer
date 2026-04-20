from .base import BaseDevice

class ExhaustDevice(BaseDevice):

    def __init__(self, mqtt, name):
        super().__init__(mqtt, f"control/{name}/state")

    def turn_on(self):
        if self.state == "ON":
            return

        self.publish({"power": "on"})
        self.state = "ON"

    def turn_off(self):
        if self.state == "OFF":
            return

        self.publish({"power": "off"})
        self.state = "OFF"