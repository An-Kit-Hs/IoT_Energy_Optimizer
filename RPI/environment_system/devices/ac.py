import json
import time
from .base import BaseDevice
from utils import CompressorProtection


class ACDevice(BaseDevice):

    def __init__(self, mqtt, name):
        super().__init__(mqtt, f"control/{name}/state")
        self.command_topic = f"control/{name}/command"

        self.protection = CompressorProtection()
        self.mode = "cool"
        self.temp = None

    def _publish_command(self, payload):
        # use BaseDevice publish
        self.publish(json.dumps(payload), topic=self.command_topic)

    def turn_on(self, temp, mode="cool"):
        if self.state == "ON":
            self.set_mode(mode)
            self.set_temp(temp)
            return

        if not self.protection.can_turn_on():
            return

        self.mode = mode
        self.temp = temp

        self.publish(json.dumps({"power": "ON"}))
        self.state = "ON"
        self.protection.mark_on()

        time.sleep(1)

        # 3. Send full config
        self._publish_command({
            "mode": self.mode,
            "temp": self.temp
        })

    def turn_off(self):
        if self.state == "OFF":
            return

        if not self.protection.can_turn_off():
            return

        self.publish(json.dumps({"power": "OFF"}))

        self.state = "OFF"
        self.protection.mark_off()

    def set_temp(self, temp):
        if self.state == "OFF":
            return

        if temp is None or temp == self.temp:
            return

        self.temp = temp

        self._publish_command({
            "temp": self.temp
        })

    def set_mode(self, mode):
        if self.state == "OFF":
            return

        if mode == self.mode:
            return

        self.mode = mode

        self._publish_command({
            "mode": self.mode
        })