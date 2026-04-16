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

    def process(self, data, people):
        # -------- Occupancy --------
        occ = self.occupancy.update(people)

        # -------- Sensor smoothing --------
        sensor = self.sensor.update(data)
        data = sensor["data"]

        # -------- Air Quality --------
        aq = self.air.update(data)

        score = aq["score"]
        ventilate = aq["ventilate"]

        # -------- Emergency --------
        if score > config.AQI_EMERGENCY_THRESHOLD:
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
        if occ["occupied"] and feels_like:
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

        print(
            f"AQI:{score:.1f} "
            f"Temp:{data.temperature:.1f} "
            f"Humidity:{data.humidity:.1f} "
            f"Feels:{feels_like:.1f} "
            f"People:{people}"
        )