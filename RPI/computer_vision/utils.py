import cv2
import numpy as np

# Drawing
def draw_boxes(frame, tracks):
    for t in tracks:
        x, y, w, h = map(int, t.bbox)
        tid = t.id

        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        label = f"ID {tid}"
        cv2.rectangle(frame, (x, y-20), (x+60, y), (0,255,0), -1)
        cv2.putText(frame, label, (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)

    return frame

def draw_info_panel(frame, count):
    h, w = frame.shape[:2]

    cv2.rectangle(frame, (0,0), (w,40), (30,30,30), -1)
    cv2.putText(frame, f"People: {count}", (10,28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    return frame

# Occupancy Map UI 
class OccupancyMap:
    def __init__(self, width=200, height=200, decay=0.95):
        self.map = np.zeros((height, width), dtype=np.float32)
        self.decay = decay

    def update(self, points):
        # Fade old values
        self.map *= self.decay

        for (x, y) in points:
            if 0 <= x < self.map.shape[1] and 0 <= y < self.map.shape[0]:
                self.map[y, x] += 3.0

    def render(self, size=(300,300), min_threshold=1):
        norm = cv2.normalize(self.map, self.map.copy(), 0, 255, cv2.NORM_MINMAX)
        norm = norm.astype(np.uint8)

        # Make low values pure black
        norm[norm < min_threshold] = 0

        # Apply color map only to non-zero areas
        heat = cv2.applyColorMap(norm, cv2.COLORMAP_JET)

        # Force background to black
        heat[norm == 0] = (0, 0, 0)

        heat = cv2.resize(heat, size)

        return heat
