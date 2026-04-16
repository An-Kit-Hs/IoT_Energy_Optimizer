from sensors import SensorModule
from utils import ComfortCalculator
from air_quality import AirQualityModule
from .ac_controller import ACController
from .exhaust_controller import ExhaustController

class EnvironmentController:

    def __init__(self, devices, occupancy_module):
        self.devices = devices
        self.occupancy = occupancy_module
        self.sensor = SensorModule()
        self.air = AirQualityModule()
        self.comfort = ComfortCalculator()
        
        self.ac_ctrl = ACController(devices)
        self.ex_ctrl = ExhaustController(devices)
        
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
            trend = aq.get("trend_rising")

            # -------- Exhaust Control --------
            self.ex_ctrl.update(score, trend)

            # -------- Comfort --------
            feels_like = self.comfort.feels_like(
                data.temperature,
                data.humidity
            )

            # -------- AC Control --------
            self.ac_ctrl.update(
                occupied=occ.get("occupied"),
                feels_like=feels_like,
                humidity=data.humidity,
                exhaust_on=self.ex_ctrl.is_on()
            )

            # -------- Status Logging --------
            ac_state = self.ac_ctrl.get_state()

            ac_state = self.ac_ctrl.get_state()

            ac_str = "OFF"
            if ac_state["on"]:
                ac_str = f"ON({ac_state['mode']},{ac_state['temp']}°C)"

            print(
                f"[STATUS] "
                f"Occ:{occ['state']}({people}) | "
                f"AQI:{self.safe_fmt(score)} | "
                f"T:{self.safe_fmt(data.temperature)}°C "
                f"H:{self.safe_fmt(data.humidity)}% "
                f"F:{self.safe_fmt(feels_like)}°C | "
                f"AC:{ac_str} | "
                f"EX:{'ON' if self.ex_ctrl.is_on() else 'OFF'} | "
                f"L:{'ON' if self.devices.is_lights_on() else 'OFF'}"
            )

        except Exception as e:
            print(f"[Controller] Error: {e}")