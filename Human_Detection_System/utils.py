import cv2
import time
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

def draw_info_panel(frame, fps, count):
    h, w = frame.shape[:2]

    cv2.rectangle(frame, (0,0), (w,40), (30,30,30), -1)

    cv2.putText(frame, f"FPS: {int(fps)}", (10,28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

    cv2.putText(frame, f"People: {count}", (150,28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    return frame


# FPS
class FPSCounter:
    def __init__(self):
        self.prev_time = time.time()
        self.fps = 0

    def update(self):
        curr = time.time()
        instant = 1.0 / max(curr - self.prev_time, 1e-6)
        self.prev_time = curr
        self.fps = 0.9*self.fps + 0.1*instant
        return self.fps


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
                self.map[y, x] += 1.0

    def render(self, size=(300,300)):
        norm = cv2.normalize(self.map, self.map.copy(), 0, 255, cv2.NORM_MINMAX)
        norm = norm.astype(np.uint8)

        heat = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
        heat = cv2.resize(heat, size)

        return heat
