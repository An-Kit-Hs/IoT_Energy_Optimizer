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

            # -------- Occupancy logic --------
            if occ.get("occupied") and feels_like is not None:
                if feels_like > 27:
                    set_temp = 18
                elif feels_like > 25:
                    set_temp = 20
                elif feels_like > 24:
                    set_temp = 22
                else:
                    set_temp = 24

                self.devices.set_ac_temp(set_temp)
            else:
                self.devices.turn_off_ac()

            # -------- Safe logging --------
            print(
                f"AQI:{self.safe_fmt(score)} "
                f"Temp:{self.safe_fmt(data.temperature)} "
                f"Humidity:{self.safe_fmt(data.humidity)} "
                f"Feels:{self.safe_fmt(feels_like)} "
                f"People:{people}"
            )

        except Exception as e:
            print(f"[Controller] Error: {e}")