from .occupancy_state import OccupancyState
from .occupancy_pattern_model import OccupancyPatternModel
from .occupancy_predictor import OccupancyPredictor


class OccupancyController:

    def __init__(self):
        self.state = OccupancyState()
        self.pattern = OccupancyPatternModel()
        self.predictor = OccupancyPredictor()

    def update(self, count):
        state = self.state.update(count)
        occupied = state == "OCCUPIED"
        self.pattern.update(occupied)
        probability = self.pattern.probability()
        precool = self.predictor.should_precool(probability)

        return {
            "occupied": occupied,
            "probability": probability,
            "precool": precool
        }