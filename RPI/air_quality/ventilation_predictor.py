class VentilationPredictor:

    PREVENTIVE_THRESHOLD = 55

    def should_ventilate(self, score, trend_rising):

        # Already bad air
        if score > 75:
            return True

        # Preventive ventilation
        if trend_rising and score > self.PREVENTIVE_THRESHOLD:
            return True

        return False