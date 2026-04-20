import time

from sensors import SensorModule
from utils import ComfortCalculator
from air_quality import AirQualityModule

from .ac_controller import ACControllerFSM
from .exhaust_controller import ExhaustControllerFSM


class EnvironmentController:

    def __init__(self, devices, occupancy_module):
        self.devices = devices
        self.occupancy = occupancy_module

        self.sensor = SensorModule()
        self.air = AirQualityModule()
        self.comfort = ComfortCalculator()

        self.ac_ctrl = ACControllerFSM(devices)
        self.ex_ctrl = ExhaustControllerFSM(devices)

        # -------- MANUAL OVERRIDE --------
        self.manual_override = {}
        self.override_logged = {}
        self.override_duration = 60  # 10 min

    # ================= OVERRIDE =================
    def set_override(self, device):
        self.manual_override[device] = time.time()
        self.override_logged[device] = False
        print(f"[OVERRIDE] {device} enabled")

    def is_overridden(self, device):
        ts = self.manual_override.get(device)
        if not ts:
            return False

        elapsed = time.time() - ts

        if elapsed >= self.override_duration:
            del self.manual_override[device]
            self.override_logged.pop(device, None)
            print(f"[OVERRIDE] {device} expired")
            return False

        # log only once
        if not self.override_logged.get(device):
            print(f"[OVERRIDE] {device} manual control active")
            self.override_logged[device] = True

        return True

    # ================= MAIN LOOP =================
    def process(self, data, people):
        try:
            occ = self.occupancy.update(people)

            # -------- LIGHTS --------
            if not self.is_overridden("light1"):
                if occ.get("occupied"):
                    self.devices.turn_on_lights()
                else:
                    self.devices.turn_off_lights()

            # -------- SENSOR --------
            sensor = self.sensor.update(data)
            data = sensor["data"]

            # -------- AIR --------
            aq = self.air.update(data)

            # -------- COMFORT --------
            feels_like = self.comfort.feels_like(
                data.temperature,
                data.humidity
            )

            # -------- EXHAUST --------
            if not self.is_overridden("exhaust"):
                self.ex_ctrl.update(
                    aq.get("score"),
                    aq.get("trend_rising")
                )

            # -------- AC --------
            ac1_override = self.is_overridden("ac1")
            ac2_override = self.is_overridden("ac2")

            # only skip if BOTH overridden
            if not (ac1_override and ac2_override):
                self.ac_ctrl.update(
                    occupied=occ.get("occupied"),
                    feels_like=feels_like,
                    humidity=data.humidity,
                    exhaust_on=self.ex_ctrl.is_on()
                )

            # -------- STATUS --------
            ac = self.ac_ctrl.get_state()

            print(
                f"[STATUS] "
                f"Occ:{occ['state']}({people}) | "
                f"AQI:{aq.get('score')} | "
                f"T:{data.temperature:.1f}°C "
                f"F:{feels_like:.1f}°C "
                f"H:{data.humidity:.1f}% | "
                f"AC:{ac['state']}({ac['mode']},{ac['temp']}) | "
                f"EX:{self.ex_ctrl.state} | "
                f"L:{'ON' if self.devices.is_lights_on() else 'OFF'}"
            )

        except Exception as e:
            print(f"[Controller] Error: {e}")

    # ================= COMMAND HANDLER =================
    def handle_command(self, device, state):
        try:
            if state is None:
                print(f"[CONTROL] Ignored invalid state for {device}")
                return

            # -------- SOURCE CHECK --------
            if isinstance(state, dict):
                source = state.get("source", "auto")
            else:
                source = "manual"

            # ONLY manual triggers override
            if source == "manual":
                self.set_override(device)

            # Normalize
            if isinstance(state, str):
                state = {"power": state.lower()}

            power = state.get("power")
            mode = state.get("mode")
            temp = state.get("temp")

            if mode:
                mode = str(mode).lower()

            # -------- AC --------
            if device.startswith("ac"):
                ac = self.devices.get_ac(device)

                if not ac:
                    print(f"[CONTROL] Unknown AC: {device}")
                    return

                if power == "on":
                    ac.turn_on(temp=temp or 24, mode=mode or "cool")

                elif power == "off":
                    ac.turn_off()

                if temp is not None:
                    ac.set_temp(temp)

                if mode is not None:
                    ac.set_mode(mode)

            # -------- LIGHT --------
            elif device.startswith("light"):
                if power == "on":
                    self.devices.turn_on_lights()
                elif power == "off":
                    self.devices.turn_off_lights()

            # -------- EXHAUST --------
            elif device.startswith("exhaust"):
                if power == "on":
                    self.devices.turn_on_exhaust()
                elif power == "off":
                    self.devices.turn_off_exhaust()

            else:
                print(f"[CONTROL] Unknown device: {device}")

        except Exception as e:
            print(f"[CONTROL ERROR] {device}: {e}")