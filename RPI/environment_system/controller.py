from sensors import SensorModule
from utils import ComfortCalculator
from air_quality import AirQualityModule
import config


class EnvironmentController:

    def __init__(self, devices, occupancy_module):
        self.devices = devices
        self.occupancy = occupancy_module
        self.sensor = SensorModule()
        self.air = AirQualityModule()
        self.comfort = ComfortCalculator()

    def safe_fmt(self, value, fmt=".1f"):
        return format(value, fmt) if isinstance(value, (int, float)) else "N/A"


    def process(self, data, people):
        try:
            # -------- Occupancy --------
            occ = self.occupancy.update(people)
            
                        # -------- Lighting control --------
            if occ.get("occupied"):
                self.devices.turn_on_lights()
            else:
                self.devices.turn_off_lights()

            # -------- Sensor smoothing --------
            sensor = self.sensor.update(data)
            data = sensor["data"]

            # -------- Air Quality --------
            aq = self.air.update(data)
            score = aq.get("score")
            ventilate = aq.get("ventilate", False)

            # -------- Emergency --------
            if isinstance(score, (int, float)) and score > config.AQI_EMERGENCY_THRESHOLD:
                print("Dangerous air quality")
                self.devices.turn_off_ac()
                self.devices.turn_on_exhaust()
                return

            # -------- Ventilation --------
            if ventilate:
                self.devices.turn_on_exhaust()
            else:
                self.devices.turn_off_exhaust()

            # Exhaust overrides AC
            if self.devices.is_exhaust_on():
                self.devices.turn_off_ac()
                return

            # -------- Comfort --------
            feels_like = self.comfort.feels_like(
                data.temperature,
                data.humidity
            )

            # -------- AC Mode Decision --------
            mode = "cool"

            if data.humidity is not None:
                if data.humidity > 70:
                    mode = "dry"   # dehumidify
                elif feels_like is not None and feels_like < 24:
                    mode = "fan"   # air circulation only

            # -------- AC Temperature Logic --------
            if occ.get("occupied") and feels_like is not None:

                # smoother control instead of aggressive jumps
                if feels_like > 30:
                    set_temp = 18
                elif feels_like > 28:
                    set_temp = 20
                elif feels_like > 26:
                    set_temp = 22
                elif feels_like > 24:
                    set_temp = 24
                else:
                    set_temp = 25  # comfort hold

                # Turn ON AC properly with mode + temp
                self.devices.turn_on_ac(set_temp, mode)

            else:
                self.devices.turn_off_ac()
                
            # -------- Device states --------
            ac_on = any(ac.state == "ON" for ac in self.devices.acs.values())
            light_on = self.devices.is_lights_on()
            exhaust_on = self.devices.is_exhaust_on()

            # -------- Extract one AC (for display) --------
            ac_temp = None
            ac_mode = None
            for ac in self.devices.acs.values():
                if ac.state == "ON":
                    ac_temp = getattr(ac, "temp", None)
                    ac_mode = getattr(ac, "mode", None)
                    break

            # -------- Status log --------
            print(
                f"[STATUS] "
                f"Occ:{occ['state']}({people}) | "
                f"AQI:{self.safe_fmt(score)} | "
                f"T:{self.safe_fmt(data.temperature)}°C "
                f"H:{self.safe_fmt(data.humidity)}% "
                f"F:{self.safe_fmt(feels_like)}°C | "
                f"AC:{'ON' if ac_on else 'OFF'}"
                f"{f'({ac_mode},{ac_temp}°C)' if ac_on else ''} | "
                f"EX:{'ON' if exhaust_on else 'OFF'} | "
                f"L:{'ON' if light_on else 'OFF'}"
            )

        except Exception as e:
            print(f"[Controller] Error: {e}")