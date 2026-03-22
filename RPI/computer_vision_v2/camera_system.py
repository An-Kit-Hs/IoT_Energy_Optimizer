from .detector import HumanDetector
from .tracker import Tracker
from .occupancy_map import OccupancyMap

class OccupancySystem:
    def __init__(self, model_path,
                 map_scale=(0.3, 0.3)):

        self.detector = HumanDetector(model_path)
        self.tracker = Tracker()
        self.occupancy = OccupancyMap()

        self.scale_x, self.scale_y = map_scale

    def process(self, frame):
        detections = self.detector.detect(frame)
        det_boxes = [d["bbox"] for d in detections]
        tracks = self.tracker.update(det_boxes)

        points = []

        for t in tracks:
            x, y, w, h = t.bbox

            cx = x + w / 2
            cy = y + h  # feet

            px = int(cx * self.scale_x)
            py = int(cy * self.scale_y)

            points.append((px, py))

        self.occupancy.update(points)

        return {
            "count": len(tracks),
            "points": points,
            "heatmap": self.occupancy.render(),
            "tracks": tracks
        }