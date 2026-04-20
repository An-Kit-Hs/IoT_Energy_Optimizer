from .aqi import IAQScorer
from .trend import AirTrendDetector
from .ventilation import VentilationPredictor


class AirQualityModule:

    def __init__(self):
        self.aqi = IAQScorer()
        self.trend = AirTrendDetector()
        self.ventilation = VentilationPredictor()

    def update(self, data):
        score = self.aqi.overall(data)
        trend_rising = self.trend.update(score)

        ventilate = self.ventilation.should_ventilate(
            score,
            trend_rising
        )

        return {
            "score": score,
            "trend_rising": trend_rising,
            "ventilate": ventilate
        }