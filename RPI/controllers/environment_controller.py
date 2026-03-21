from sensors.sensor_smoother import SensorSmoother
from air_quality.aqi_scorer import AQIScorer
from air_quality.air_trend_detector import AirTrendDetector
from air_quality.ventilation_predictor import VentilationPredictor
from utils.comfort_calculator import ComfortCalculator
import config


class EnvironmentController:

    def __init__(self, ac, exhaust, occupancy):

        self.ac = ac
        self.exhaust = exhaust
        self.occupancy = occupancy

        # Processing modules
        self.smoother = SensorSmoother()
        self.aqi = AQIScorer()
        self.trend = AirTrendDetector()
        self.ventilation = VentilationPredictor()
        self.comfort = ComfortCalculator()

    def process(self, data, people):

        
        # Update occupancy model
        
        occ = self.occupancy.update(people)

        
        # Smooth sensor noise
        
        data = self.smoother.smooth(data)

        
        # Compute AQI score
        
        score = self.aqi.overall(data)

        
        # Detect pollution trend
        
        trend_rising = self.trend.update(score)

        
        # Emergency air quality override
        
        if score > 75:

            print("Dangerous air quality detected")

            self.ac.turn_off()
            self.exhaust.turn_on()

            return

        
        # Predictive ventilation
        
        if self.ventilation.should_ventilate(score, trend_rising):

            self.exhaust.turn_on()

        else:

            self.exhaust.turn_off()

        # If exhaust is running, avoid AC cooling
        if self.exhaust.state == "ON":

            self.ac.turn_off()
            return

        
        # Comfort temperature calculation
        
        feels_like = self.comfort.feels_like(
            data.temperature,
            data.humidity
        )

        
        # Occupied mode
        
        if occ["occupied"]:

            if feels_like > config.COMFORT_TEMP + config.TEMP_BAND:

                self.ac.turn_on(config.COMFORT_TEMP)

            elif feels_like < config.COMFORT_TEMP - config.TEMP_BAND:

                self.ac.turn_off()

        
        # Predictive precooling
        
        elif occ["precool"]:

            print("Precooling room")

            self.ac.turn_on(config.ECO_TEMP)

        
        # Empty room energy saving
        
        else:

            self.ac.turn_off()

        print(
            f"AQI:{score:.2f} "
            f"Temp:{data.temperature:.1f} "
            f"Humidity:{data.humidity:.1f} "
            f"Feels:{feels_like:.1f} "
            f"People:{people}"
        )