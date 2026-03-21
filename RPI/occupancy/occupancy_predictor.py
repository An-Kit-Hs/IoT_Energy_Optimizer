class OccupancyPredictor:

    PRECOOL_THRESHOLD = 0.6

    def should_precool(self, probability):

        return probability > self.PRECOOL_THRESHOLD