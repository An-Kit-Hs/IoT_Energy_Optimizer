from .devices.ac import ACDevice
from .devices.exhaust import ExhaustDevice
from .devices.light import LightDevice


class DeviceManager:

    def __init__(self, mqtt):
        self.mqtt = mqtt

        self.acs = {}
        self.exhausts = {}
        self.lights = {}

    # ---------- Add devices ----------
    def add_ac(self, name):
        self.acs[name] = ACDevice(self.mqtt, name)

    def add_exhaust(self, name):
        self.exhausts[name] = ExhaustDevice(self.mqtt, name)

    def add_light(self, name):
        self.lights[name] = LightDevice(self.mqtt, name)

    # ---------- AC control ----------
    def get_ac(self, name):
        return self.acs.get(name)

    def turn_on_ac(self, temp=24, mode="cool"):
        for ac in self.acs.values():
            ac.turn_on(temp, mode)

    def turn_off_ac(self):
        for ac in self.acs.values():
            ac.turn_off()

    def set_ac_temp(self, temp):
        for ac in self.acs.values():
            ac.set_temp(temp)

    def set_ac_mode(self, mode):
        for ac in self.acs.values():
            ac.set_mode(mode)

    # ---------- Load balancing ----------
    def turn_on_single_ac(self, temp, mode="cool"):
        for ac in self.acs.values():
            if ac.state == "OFF":
                ac.turn_on(temp, mode)
                return

        if self.acs:
            next(iter(self.acs.values())).set_temp(temp)

    # ---------- Exhaust ----------
    def turn_on_exhaust(self):
        for ex in self.exhausts.values():
            ex.turn_on()

    def turn_off_exhaust(self):
        for ex in self.exhausts.values():
            ex.turn_off()

    def is_exhaust_on(self):
        return any(ex.state == "ON" for ex in self.exhausts.values())

    # ---------- Lights ----------
    def turn_on_lights(self):
        for light in self.lights.values():
            light.turn_on()

    def turn_off_lights(self):
        for light in self.lights.values():
            light.turn_off()

    def is_lights_on(self):
        return any(light.state == "ON" for light in self.lights.values())
    
    def turn_on_zone_light(self, name):
        if name in self.lights:
            self.lights[name].turn_on()